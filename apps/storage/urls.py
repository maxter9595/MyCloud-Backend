from django.urls import path

from .views import (
    FileDetailView,
    FileDownloadView,
    FileListView,
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
        'shared/<uuid:shared_link>/',
        SharedFileDownloadView.as_view(),
        name='shared-file-download'
    ),
]
