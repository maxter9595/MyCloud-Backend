# apps\accounts\tests\test_models.py
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import TransactionTestCase

from apps.accounts.models import CustomUser
from apps.storage.models import UserFile


class CustomUserModelTest(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        cache.clear()

        if connection.vendor == 'postgresql':
            with connection.cursor() as cursor:
                cursor.execute("TRUNCATE storage_userfile, accounts_customuser RESTART IDENTITY CASCADE;")

        # Create test user after clearing and resetting sequences
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            full_name='Test User',
            password='testpass123',
            max_storage=100 * 1024 * 1024
        )

    def test_storage_usage_calculation(self):
        test_content = b'This is a test file content'
        test_file = SimpleUploadedFile(
            'test_file.txt',
            test_content,
            content_type='text/plain'
        )

        # Явно указываем ID или используем bulk_create для обхода автоинкремента
        user_file = UserFile(
            user=self.user,
            original_name='test_file.txt',
            file=test_file,
            size=len(test_content)
        )
        user_file.save()  # Это может работать лучше, чем create()

        usage = self.user.get_storage_usage()
        self.assertEqual(usage, len(test_content))

        cached_usage = cache.get(f'user_{self.user.id}_storage_usage')
        self.assertEqual(cached_usage, usage)

    def test_storage_usage_percent(self):
        test_size = 50 * 1024 * 1024  # 50MB
        UserFile.objects.create(
            user=self.user,
            original_name='test_file.txt',
            file=None,
            size=test_size
        )

        percent = self.user.get_storage_usage_percent()
        expected_percent = (test_size / self.user.max_storage) * 100
        self.assertEqual(percent, expected_percent)

    def test_has_storage_space(self):
        test_size = 50 * 1024 * 1024  # 50MB
        UserFile.objects.create(
            user=self.user,
            original_name='test_file.txt',
            file=None,
            size=test_size
        )

        self.assertTrue(self.user.has_storage_space(50 * 1024 * 1024))
        self.assertFalse(self.user.has_storage_space(60 * 1024 * 1024))

    def test_storage_path_auto_generation(self):
        new_user = CustomUser.objects.create_user(
            username='newuser',
            email='new@example.com',
            full_name='New User',
            password='testpass123'
        )
        self.assertEqual(new_user.storage_path, f'user_{new_user.id}_storage')

    def test_admin_user_creation(self):
        admin = CustomUser.objects.create_superuser(
            username='adminuser',
            email='admin@example.com',
            full_name='Admin',
            password='adminpass'
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
