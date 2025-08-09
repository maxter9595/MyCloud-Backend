from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.throttling import LoginThrottle, RegisterThrottle

from .models import CustomUser
from .serializers import (
    AdminCreateSerializer,
    LoginSerializer,
    UserSerializer,
    UserUpdateSerializer,
)


class RegisterView(generics.CreateAPIView):
    throttle_classes = [RegisterThrottle]
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        """
        Create a new user with the given data, and 
        return a response with the new user data and 
        an authentication token.

        The response will contain the user data in 
        the user key, and the authentication
        token in the token key.

        :param request: The request object
        :param args: Additional positional arguments
        :param kwargs: Additional keyword arguments
        :return: The response object
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)

        return Response(
            {
                'user': UserSerializer(user).data,
                'token': token.key
            }, 
            status=status.HTTP_201_CREATED
        )


# @method_decorator(csrf_exempt, name='dispatch')
class LoginView(GenericAPIView):
    throttle_classes = [LoginThrottle]
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """
        Handle a login request.

        :param request: The request object
        :return: A response object with the
        authentication token and user data
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        user = authenticate(
            request=request,
            username=username,
            password=password
        )

        if user is None:
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return Response(
                {
                    "error": "You are deactivated.\
                    Please contact admin (admin@mail.ru)",
                    "code": "account_deactivated"
                },
                status=status.HTTP_403_FORBIDDEN
            )

        login(request, user)
        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            'token': token.key,
            'user': {
                'id': user.pk,
                'username': user.username,
                'email': user.email,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'is_active': user.is_active
            }
        })


class LogoutView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """
        Handle a logout request by deleting the user's
        authentication token and logging them out.

        This method ensures that the user's session is
        terminated, and they are properly logged out from
        the system, making their authentication token
        invalid for future requests.

        :param request: The request object
        :return: An HTTP 204 No Content response
        indicating successful logout
        """
        request.user.auth_token.delete()
        logout(request)
        return Response(
            status=status.HTTP_204_NO_CONTENT
        )


class UserListView(generics.ListAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = [permissions.IsAdminUser]

    def get_serializer_class(self):
        """
        Return the serializer class to
        be used for the request.

        Determine the appropriate serializer class
        based on the HTTP method of the request. Use
        UserUpdateSerializer for PUT and PATCH methods
        to handle updates, and UserSerializer for 
        other methods.

        :return: The serializer class for the request
        """
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserSerializer


class AdminCreateView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = AdminCreateSerializer
    permission_classes = [permissions.IsAdminUser]

    def perform_create(self, serializer):
        """
        Override the perform_create method to
        save a new user with admin privileges.

        This method customizes the creation
        process by ensuring that any new user
        created through this view is automatically
        assigned superuser and staff status, with
        a maximum storage limit defined by MAX_ADMIN_BYTES.

        :param serializer: The serializer instance used to
        validate and save the new user data.
        """
        user = serializer.save(
            is_superuser=True,
            is_staff=True,
            max_storage=settings.MAX_ADMIN_BYTES
        )
        user.set_password(serializer.validated_data['password'])
        user.save()

@api_view(['GET'])
def get_csrf_token(request):
    """
    Returns a CSRF token for the current user.

    :param request: The HTTP request object.
    :return: A Response object containing
    the CSRF token.
    """
    return Response({
        'csrfToken': get_token(request)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    """
    Returns information about the current user.

    :param request: The HTTP request object.
    :return: A Response object containing the user's data.
    """
    user = request.user
    storage_usage = user.get_storage_usage()
    storage_usage_percent = (storage_usage / user.max_storage) * 100\
        if user.max_storage else 0

    return Response({
        'id': user.pk,
        'username': user.username,
        'email': user.email,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
        'is_active': user.is_active,
        'storage_usage': user.get_storage_usage(),
        'max_storage': user.max_storage,
        'storage_usage_percent': storage_usage_percent
    })

@api_view(['GET'])
def check_username(request):
    username = request.GET.get('username', '')
    exists = CustomUser.objects.filter(username__iexact=username).exists()
    return JsonResponse({'available': not exists})

@api_view(['GET'])
def check_email(request):
    email = request.GET.get('email', '')
    exists = CustomUser.objects.filter(email__iexact=email).exists()
    return JsonResponse({'available': not exists})
