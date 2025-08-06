from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.accounts.models import CustomUser
from apps.storage.models import UserFile


class CustomUserModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = CustomUser.objects.create_user(
        username='testuser',
        email='test@example.com',
        full_name='Test User',
        password='testpass123',
        max_storage=100 * 1024 * 1024 # 100MB
    )

    def setUp(self):
        cache.clear()

    def test_storage_usage_calculation(self):
        # Создаем тестовый файл
        test_file = SimpleUploadedFile(
            'test_file.txt',
            b'This is a test file content',
            content_type='text/plain'
        )
        
        UserFile.objects.create(
            user=self.user,
            original_name='test_file.txt',
            file=test_file,
            size=len(test_file)
        )
        
        # Проверяем расчет использования хранилища
        usage = self.user.get_storage_usage()
        self.assertEqual(usage, len(test_file))
        
        # Проверяем кеширование
        cached_usage = cache.get(f'user_{self.user.id}_storage_usage')
        self.assertEqual(cached_usage, usage)

    def test_storage_usage_percent(self):
        # Проверяем расчет процентов использования
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
        # Проверяем проверку свободного места
        test_size = 50 * 1024 * 1024  # 50MB
        UserFile.objects.create(
            user=self.user,
            original_name='test_file.txt',
            file=None,
            size=test_size
        )
        
        # Проверяем, что есть место для еще 50MB
        self.assertTrue(self.user.has_storage_space(50 * 1024 * 1024))
        
        # Проверяем, что нет места для еще 60MB
        self.assertFalse(self.user.has_storage_space(60 * 1024 * 1024))

    def test_storage_path_auto_generation(self):
        # Проверяем автоматическое создание storage_path
        new_user = CustomUser.objects.create_user(
            username='newuser',
            email='new@example.com',
            full_name='New User',
            password='testpass123'
        )
        self.assertEqual(new_user.storage_path, f'user_{new_user.id}_storage')

    def test_admin_user_creation(self):
        # Проверяем создание админа
        admin = CustomUser.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            full_name='Admin',
            password='adminpass'
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
