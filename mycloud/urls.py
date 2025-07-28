from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.conf.urls.static import static


urlpatterns = [
    path(
        'admin/',
        admin.site.urls
    ),
    path(
        'api/auth/',
        include(
            'apps.accounts.urls'
        )
    ),
    path(
        'api/storage/',
        include(
            'apps.storage.urls'
        )
    ),
]

urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
)
