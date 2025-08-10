from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITransactionTestCase
from django.db import connection
from django.core.cache import cache

from apps.accounts.models import CustomUser
from apps.storage.models import UserFile

class FileAPITestCase(APITransactionTestCase):
    reset_sequences = True

    def setUp(self):
        # Clear the database
        UserFile.objects.all().delete()
        CustomUser.objects.all().delete()
        
        # Reset sequences for PostgreSQL
        if connection.vendor == 'postgresql':
            with connection.cursor() as cursor:
                cursor.execute("ALTER SEQUENCE storage_userfile_id_seq RESTART WITH 1;")
                cursor.execute("ALTER SEQUENCE accounts_customuser_id_seq RESTART WITH 1;")
        
        # Create test data
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            full_name='Test User',
            password='testpass123',
            max_storage=100 * 1024 * 1024
        )
        self.admin = CustomUser.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            full_name='Admin',
            password='adminpass'
        )
        
        self.client.force_authenticate(user=self.user)
        self.test_file = SimpleUploadedFile(
            'test_file.txt',
            b'This is a test file content',
            content_type='text/plain'
        )
    
    def tearDown(self):
        UserFile.objects.all().delete()
        CustomUser.objects.all().delete()
        cache.clear()
        if connection.vendor == 'postgresql':
            with connection.cursor() as cursor:
                cursor.execute("ALTER SEQUENCE storage_userfile_id_seq RESTART WITH 1;")
                cursor.execute("ALTER SEQUENCE accounts_customuser_id_seq RESTART WITH 1;")

    def test_file_download(self):
        file = UserFile(
            user=self.user,
            file=self.test_file,
            size=self.test_file.size,
        )
        file.save()

        url = reverse('file-download', kwargs={'pk': file.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(f'attachment; filename="{file.original_name}"', response['Content-Disposition'])

    def test_shared_file_download(self):
        shared_link = '12345678-1234-5678-1234-567812345678'

        file = UserFile(
            user=self.user,
            file=self.test_file,
            size=self.test_file.size,
            shared_link=shared_link
        )
        file.save()

        self.client.logout()  # Разлогиниваемся, чтобы проверить доступ без авторизации

        url = reverse('shared-file-download', kwargs={'shared_link': shared_link})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(f'attachment; filename="{file.original_name}"', response['Content-Disposition'])

    def test_storage_quota_enforcement(self):
        large_file = UserFile(
            user=self.user,
            size=self.user.max_storage,
        )
        large_file.save()

        url = reverse('file-list')
        response = self.client.post(url, {'file': self.test_file}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('exceeded the maximum storage limit', str(response.data).lower())

    def test_admin_access_to_user_files(self):
        file = UserFile(
            user=self.user,
            file=self.test_file,
            size=self.test_file.size,
        )
        file.save()

        self.client.force_authenticate(user=self.admin)

        url = reverse('file-download', kwargs={'pk': file.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        list_url = reverse('file-list') + f'?user_id={self.user.id}'
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
