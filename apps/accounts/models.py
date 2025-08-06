from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.cache import cache
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models


class CustomUser(AbstractUser):
    username = models.CharField(
        max_length=20,
        unique=True,
        validators=[
            RegexValidator(
                regex='^[a-zA-Z][a-zA-Z0-9]{3,19}$',
                message='The login must start with a letter and contain\
                    only latin letters and numbers (4-20 characters)'
            )
        ]
    )
    email = models.EmailField(
        unique=True
    )
    full_name = models.CharField(
        max_length=100
    )
    storage_path = models.CharField(
        max_length=255,
        unique=True,
        blank=True
    )
    max_storage = models.BigIntegerField(
        default=settings.DEFAULT_USER_BYTES,
        validators=[MinValueValidator(settings.MIN_USER_BYTES)],
        help_text="Maximum storage capacity in bytes"
    )

    def get_storage_usage(self):
        """
        Calculate the total storage usage for the user with caching
        """
        cache_key = f'user_{self.id}_storage_usage'
        usage = cache.get(cache_key)
        
        if usage is None:
            from apps.storage.models import UserFile
            try:
                usage = sum(
                    file.size for file in
                    UserFile.objects.filter(user=self).only('size')
                )
                # Кешируем на 5 минут
                cache.set(cache_key, usage, timeout=300)
            except Exception:
                usage = 0
                
        return usage

    def save(self, *args, **kwargs):
        if not self.pk:
            is_superuser = (
                hasattr(self, 'is_superuser')
                and self.is_superuser
            )
            if self.username == 'admin' or is_superuser:
                self.is_staff = True
                self.is_superuser = True
                self.max_storage = settings.MAX_ADMIN_BYTES
        super().save(*args, **kwargs)
        if not self.storage_path:
            self.storage_path = f'user_{self.id}_storage'
            super().save(update_fields=['storage_path'])
        
        # Инвалидируем кеш использования хранилища
        cache.delete(f'user_{self.id}_storage_usage')

    def get_storage_usage_percent(self):
        """
        Calculate the percentage of
        storage used by the user.

        This method returns the result of get_storage_usage()
        divided by max_storage, multiplied by 100. If max_storage
        is 0, it returns 0.

        :return: The percentage of storage used by the user.
        """
        if self.max_storage == 0:
            return 0
        return (self.get_storage_usage() / self.max_storage) * 100

    def has_storage_space(self, additional_bytes=0):
        """
        Check if the user has enough storage
        space to add additional bytes.

        :param additional_bytes: The number
        of bytes to add to the user's storage.
        :return: True if the user has
        enough space, False otherwise.
        """
        new_storage_value = self.get_storage_usage() + additional_bytes
        return new_storage_value <= self.max_storage

    def __str__(self):
        """
        Return the string representation of the user.
        This method returns the username of the user
        as its string representation.

        :return: The username of the user.
        """
        return self.username

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
