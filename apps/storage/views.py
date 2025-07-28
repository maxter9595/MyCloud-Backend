from django.utils import timezone
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied

from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework import generics, permissions, status

from .models import UserFile
from .serializers import FileSerializer
from apps.accounts.models import CustomUser
from .renderers.binary_file import BinaryFileRenderer


class FileListView(generics.ListCreateAPIView):
    serializer_class = FileSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser]

    def get_queryset(self):
        """
        Returns a queryset of UserFile objects, either
        for the current user (if not a superuser) or
        for the user specified in the user_id query
        parameter (if a superuser).

        :return: UserFile queryset
        """
        user = self.request.user

        if user.is_superuser and 'user_id' in self.request.query_params:
            target_user = get_object_or_404(
                CustomUser,
                id=self.request.query_params['user_id']
            )
            return UserFile.objects.filter(user=target_user)

        return UserFile.objects.filter(user=user)

    def perform_create(self, serializer):
        """
        Customize the creation of a new UserFile object to
        enforce storage size limits and set the original_name
        and size fields.

        :param serializer: The UserFile serializer instance
        :return: The created UserFile object
        """
        file_obj = self.request.FILES.get('file')
        if not file_obj:
            raise ValueError(
                "No file was uploaded"
            )

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


class FileDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = FileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Retrieve a queryset of UserFile objects
        based on the user's permissions.

        If the request is made by a superuser and
        includes a user_id query parameter, return
        the UserFile objects associated with the
        specified user. Otherwise, return the UserFile
        objects associated with the requesting user.

        :return: Queryset of UserFile objects
        """
        user = self.request.user

        if user.is_superuser and 'user_id' in self.request.query_params:
            target_user = get_object_or_404(
                CustomUser,
                id=self.request.query_params['user_id']
            )
            return UserFile.objects.filter(user=target_user)

        return UserFile.objects.filter(user=user)

    def perform_update(self, serializer):
        """
        Update the UserFile instance with new data.

        This method saves the updated instance data from
        the serializer and resets the last_download
        attribute to None, indicating that the file has
        not been downloaded since the update. It then
        saves the changes to the database.

        :param serializer: The serializer instance containing
        the validated data for updating the UserFile.
        :return: None
        """
        instance = serializer.save()
        instance.last_download = None
        instance.save()


class FileDownloadView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [BinaryFileRenderer]

    def get(self, request, pk):
        """
        Return a file response for the specified UserFile object.

        This method checks if the requesting user is either the owner
        of the file or a superuser. If the user has the necessary
        permissions, it updates the last_download attribute of the
        UserFile instance with the current time, and then saves the
        changes to the database.

        If the file does not exist or if the user does not have
        the necessary permissions, it raises the appropriate
        exception.

        :param request: The HTTP request object
        :param pk: The primary key of the UserFile object
        :return: A file response with the file contents
        """
        try:
            user_file = self.get_object(pk)

            if not user_file.file:
                raise Http404(
                    "File not found"
                )

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
        Raises PermissionDenied if the requesting user is not 
        the owner of the file and not a superuser.

        :param pk: The primary key of the UserFile object
        :return: The UserFile object
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
        Handle GET requests to download
        a file from a shared link.

        :param request: The GET request
        :param shared_link: The shared link of the file to download
        :return: A streaming HTTP response containing the file
        """
        try:
            user_file = get_object_or_404(
                UserFile,
                shared_link=shared_link
            )

            user_file.last_download = timezone.now()
            user_file.save()

            if not user_file.file:
                raise Http404(
                    "File not found on server"
                )

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
