from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, RegexValidator


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

    def save(self, *args, **kwargs):
        """
        Save the user model to the database.

        If the user is created for the first time, check if the user is
        named 'admin' or is a superuser. If yes, set the user as a staff
        and superuser, and set the maximum storage to the maximum value
        for admins.

        If the `storage_path` is not set, set it to
        `user_<user_id>_storage` and save the model again with only the
        `storage_path` field updated.

        :param args: Additional positional arguments to pass to the
            `save()` method.
        :param kwargs: Additional keyword arguments to pass to the
            `save()` method.
        :return: None
        """
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

    def get_storage_usage(self):
        """
        Calculate the total storage usage for the user.

        This method queries the UserFile model to calculate
        the sum of the sizes of all files associated with
        the user. If an error occurs during the query,
        it returns 0.

        :return: The total storage usage in bytes.
        """
        from apps.storage.models import UserFile
        try:
            return sum(
                file.size for file in
                UserFile.objects.filter(user=self)
            )
        except Exception:
            return 0

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
