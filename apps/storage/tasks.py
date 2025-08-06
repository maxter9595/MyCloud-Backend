# backend/apps/storage/tasks.py
import logging

from celery import shared_task
from django.utils import timezone

from apps.storage.models import UserFile

logger = logging.getLogger(__name__)

@shared_task(name="storage.tasks.cleanup_files_task")
def cleanup_files_task():
    """Единственная задача для очистки файлов"""
    try:
        logger.info("=== STARTING CLEANUP TASK ===")
        
        # Очистка битых файлов
        orphaned_count = 0
        for file in UserFile.objects.filter(file__isnull=False):
            if not file.file_exists:
                file.delete()
                orphaned_count += 1
        
        # Очистка просроченных ссылок
        expired_files = UserFile.objects.filter(
            shared_expiry__lt=timezone.now()
        ).exclude(shared_link__isnull=True)
        expired_count = expired_files.update(shared_link=None, shared_expiry=None)
        
        result = {
            'orphaned_files_deleted': orphaned_count,
            'expired_links_cleared': expired_files.count()
        }
        
        logger.info(f"=== TASK COMPLETE: {result} ===")
        return result
        
    except Exception as e:
        logger.error(f"!!! TASK ERROR: {str(e)}", exc_info=True)
        raise
