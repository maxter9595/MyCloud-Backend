import uuid
from datetime import timedelta

from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.db.models import Prefetch
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, serializers, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from apps.accounts.models import CustomUser
from mycloud.settings.base import CACHE_TTL

from .models import UserFile
from .renderers.binary_file import BinaryFileRenderer
from .serializers import FileSerializer, FileShareSerializer


class FileListView(generics.ListCreateAPIView):
    serializer_class = FileSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser]

    def get_cache_key(self):
        user = self.request.user
        user_id = user.id
        if user.is_superuser and 'user_id' in self.request.query_params:
            user_id = self.request.query_params['user_id']
        return f'user_files_{user_id}'

    def get_queryset(self):
        """
        Returns a queryset of UserFile objects with caching and optimized queries
        """
        cache_key = self.get_cache_key()
        queryset = cache.get(cache_key)
        
        if queryset is None:
            user = self.request.user

            if user.is_superuser and 'user_id' in self.request.query_params:
                target_user = get_object_or_404(
                    CustomUser,
                    id=self.request.query_params['user_id']
                )
                queryset = UserFile.objects.filter(user=target_user)
            else:
                queryset = UserFile.objects.filter(user=user)

            # Оптимизация запросов
            queryset = queryset.select_related('user').only(
                'id',
                'original_name',
                'size',
                'upload_date',
                'last_download',
                'comment',
                'shared_link',
                'shared_expiry',
                'user__username'
            )
            
            # Кешируем на 1 час
            cache.set(cache_key, queryset, timeout=CACHE_TTL)

        return queryset

    def perform_create(self, serializer):
        """
        Customize the creation of a new UserFile object and invalidate cache
        """
        file_obj = self.request.FILES.get('file')
        if not file_obj:
            raise ValueError("No file was uploaded")

        user = self.request.user
        if not user.has_storage_space(file_obj.size):
            raise serializers.ValidationError({
                'error': "You have exceeded the maximum storage limit. "
                "Please contact the administrator at admin@mail.ru "
                "to increase your storage quota"
            })

        instance = serializer.save(
            user=user,
            original_name=file_obj.name,
            size=file_obj.size,
            file=None
        )
        instance.file.save(file_obj.name, file_obj)
        instance.save()
        
        # Инвалидируем кеш
        cache.delete(self.get_cache_key())

    @action(detail=False, methods=['post'])
    def clear_cache(self, request):
        """
        Clear cache for current user's files
        """
        cache.delete(self.get_cache_key())
        return Response({'status': 'cache cleared'}, status=status.HTTP_200_OK)


class FileDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = FileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Retrieve a queryset of UserFile objects with optimized queries
        """
        user = self.request.user

        if user.is_superuser and 'user_id' in self.request.query_params:
            target_user = get_object_or_404(
                CustomUser,
                id=self.request.query_params['user_id']
            )
            queryset = UserFile.objects.filter(user=target_user)
        else:
            queryset = UserFile.objects.filter(user=user)

        return queryset.select_related('user').only(
            'id',
            'original_name',
            'size',
            'upload_date',
            'last_download',
            'comment',
            'shared_link',
            'shared_expiry',
            'user__username',
            'file'
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        instance.last_download = None
        instance.save()
        
        # Инвалидируем кеш списка файлов
        cache_key = f'user_files_{instance.user.id}'
        cache.delete(cache_key)

    def perform_destroy(self, instance):
        user_id = instance.user.id
        instance.delete()
        
        # Инвалидируем кеш списка файлов
        cache_key = f'user_files_{user_id}'
        cache.delete(cache_key)


class FileDownloadView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [BinaryFileRenderer]

    def get(self, request, pk):
        """
        Return a file response for the specified UserFile object.
        """
        try:
            user_file = self.get_object(pk)

            if not user_file.file:
                raise Http404("File not found")

            is_user = (user_file.user == request.user)
            if not is_user and not request.user.is_superuser:
                raise PermissionDenied(
                    "You don't have the rights to download this file"
                )

            user_file.last_download = timezone.now()
            user_file.save()

            file_handle = user_file.file.open('rb')
            response = FileResponse(
                file_handle,
                content_type='application/octet-stream',
                as_attachment=True,
                filename=user_file.original_name
            )

            attachment = f'attachment; filename="{user_file.original_name}"'
            response['Content-Disposition'] = attachment
            return response

        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_object(self, pk):
        """
        Returns the UserFile object with the given primary key.
        """
        file = get_object_or_404(UserFile, pk=pk)

        is_superuser = self.request.user.is_superuser
        if not is_superuser and file.user != self.request.user:
            raise PermissionDenied(
                "You don't have the rights to download this file"
            )

        return file


class SharedFileDownloadView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, shared_link):
        """
        Handle GET requests to download a file from a shared link.
        """
        try:
            user_file = get_object_or_404(
                UserFile,
                shared_link=shared_link
            )

            if user_file.is_shared_link_expired():
                return Response(
                    {"detail": "Срок действия ссылки истек"},
                    status=status.HTTP_410_GONE
                )

            user_file.last_download = timezone.now()
            user_file.save()

            if not user_file.file:
                raise Http404("File not found on server")

            response = FileResponse(
                user_file.file,
                as_attachment=True,
                filename=user_file.original_name
            )

            return response

        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FileShareView(generics.UpdateAPIView):
    serializer_class = FileShareSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Оптимизированный запрос с select_related для пользователя
        """
        user = self.request.user
        return UserFile.objects.filter(user=user).select_related('user')

    def patch(self, request, *args, **kwargs):
        """
        Creates or updates a shared link for a file
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        
        if 'expiry_days' not in request.data:
            instance.shared_expiry = None
        
        instance.shared_link = uuid.uuid4()
        instance.save()
        
        # Инвалидируем кеш списка файлов
        cache_key = f'user_files_{instance.user.id}'
        cache.delete(cache_key)
        
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        """
        Deletes the shared link from the file
        """
        instance = self.get_object()
        user_id = instance.user.id
        
        instance.shared_link = None
        instance.shared_expiry = None
        instance.save()
        
        # Инвалидируем кеш списка файлов
        cache_key = f'user_files_{user_id}'
        cache.delete(cache_key)
        
        return Response(status=status.HTTP_204_NO_CONTENT)
