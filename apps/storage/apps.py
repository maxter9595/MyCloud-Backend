# backend/apps/storage/apps.py
from django.apps import AppConfig


class StorageConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.storage'
    verbose_name = 'File storage'

    def ready(self):
        # Принудительно импортируем задачи при запуске приложения
        from . import tasks  # noqa
        super().ready()
