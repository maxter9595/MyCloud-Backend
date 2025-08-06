from django.urls import path

from .views import (
    FileDetailView,
    FileDownloadView,
    FileListView,
    FileShareView,
    SharedFileDownloadView,
)

urlpatterns = [
    path(
        'files/',
        FileListView.as_view(),
        name='file-list'
    ),
    path(
        'files/<int:pk>/',
        FileDetailView.as_view(),
        name='file-detail'
    ),
    path(
        'files/<int:pk>/download/',
        FileDownloadView.as_view(),
        name='file-download'
    ),
    path(
        'files/<int:pk>/share/',
        FileShareView.as_view(),
        name='file-share'
    ),
    path(
        'shared/<uuid:shared_link>/',
        SharedFileDownloadView.as_view(),
        name='shared-file-download'
    ),
]
