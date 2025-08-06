# backend/mycloud/celery.py
import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mycloud.settings.local')

app = Celery('mycloud')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Явно указываем где искать задачи
app.autodiscover_tasks(['apps.storage'])

# Настройки периодических задач
app.conf.beat_schedule = {
    'cleanup-files': {
        'task': 'storage.tasks.cleanup_files_task',
        'schedule': 60.0,  # 60 секунд = 1 минута
        'options': {
            'expires': 30.0  # Задача истечет, если не будет выполнена за 30 сек
        }
    },
}
app.conf.timezone = 'Europe/Moscow'
