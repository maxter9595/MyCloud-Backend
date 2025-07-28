from django.urls import path

from .views import (
    AdminCreateView,
    LoginView,
    LogoutView,
    RegisterView,
    UserDetailView,
    UserListView,
    current_user,
    get_csrf_token,
)

urlpatterns = [
    path(
        'register/',
        RegisterView.as_view(),
        name='register'
    ),
    path(
        'admin/create/',
        AdminCreateView.as_view(),
        name='admin-create'
    ),
    path(
        'login/',
        LoginView.as_view(),
        name='login'
    ),
    path(
        'logout/',
        LogoutView.as_view(),
        name='logout'
    ),
    path(
        'users/',
        UserListView.as_view(),
        name='user-list'
    ),
    path(
        'users/<int:pk>/',
        UserDetailView.as_view(),
        name='user-detail'
    ),
    path(
        'users/me/',
        current_user,
        name='current-user'
    ),
    path(
        'csrf/',
        get_csrf_token,
        name='csrf'
    ),
]
