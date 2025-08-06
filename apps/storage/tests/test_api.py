from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import CustomUser
from apps.storage.models import UserFile


class FileAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            full_name='Test User',
            password='testpass123',
            max_storage=100 * 1024 * 1024 # 100MB
        )

        cls.admin = CustomUser.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            full_name='Admin',
            password='adminpass'
        )

    def setUp(self):
        self.client.force_authenticate(user=self.user)
        self.test_file = SimpleUploadedFile(
            'test_file.txt',
            b'This is a test file content',
            content_type='text/plain'
        )

    def test_file_upload(self):
        url = reverse('file-list')
        response = self.client.post(
            url,
            {'file': self.test_file},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserFile.objects.count(), 1)
        
        file = UserFile.objects.first()
        self.assertEqual(file.user, self.user)
        self.assertEqual(file.original_name, 'test_file.txt')

    def test_file_download(self):
        # Создаем тестовый файл
        file = UserFile.objects.create(
            user=self.user,
            original_name='test_download.txt',
            file=self.test_file,
            size=len(self.test_file)
        )
        
        url = reverse('file-download', kwargs={'pk': file.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response['Content-Disposition'],
            'attachment; filename="test_download.txt"'
        )

    def test_shared_file_download(self):
        # Создаем тестовый файл с общей ссылкой
        file = UserFile.objects.create(
            user=self.user,
            original_name='test_shared.txt',
            file=self.test_file,
            size=len(self.test_file),
            shared_link='12345678-1234-5678-1234-567812345678'
        )
        
        # Разлогиниваемся для проверки доступа без авторизации
        self.client.logout()
        
        url = reverse('shared-file-download', kwargs={
            'shared_link': '12345678-1234-5678-1234-567812345678'
        })
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response['Content-Disposition'],
            'attachment; filename="test_shared.txt"'
        )

    def test_storage_quota_enforcement(self):
        # Исчерпываем квоту пользователя
        UserFile.objects.create(
            user=self.user,
            original_name='large_file.txt',
            file=None,
            size=self.user.max_storage
        )
        
        url = reverse('file-list')
        response = self.client.post(
            url,
            {'file': self.test_file},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('exceeded the maximum storage limit', str(response.data))

    def test_admin_access_to_user_files(self):
        # Создаем тестовый файл от имени обычного пользователя
        file = UserFile.objects.create(
            user=self.user,
            original_name='admin_test.txt',
            file=self.test_file,
            size=len(self.test_file)
        )
        
        # Логинимся как админ
        self.client.force_authenticate(user=self.admin)
        
        # Проверяем доступ к файлу через API
        url = reverse('file-download', kwargs={'pk': file.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем список файлов пользователя
        list_url = reverse('file-list') + f'?user_id={self.user.id}'
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
