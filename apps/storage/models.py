import os
import uuid

from apps.accounts.models import CustomUser
from django.db import models


def user_directory_path(instance, filename):
    """
    Create a directory path to store a user's files.
    The directory name is of the form user_<user_id>_storage
    and the file name is an uuid with the same extension as
    the original file name.

    :param instance: The UserFile instance to generate a path for
    :param filename: The name of the file to be stored
    :return: A string representing the path to store the file
    """
    ext = os.path.splitext(filename)[1]
    filename = f"{uuid.uuid4()}{ext}"
    return os.path.join(
        f'user_{instance.user.id}_storage',
        filename
    )


class UserFile(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE
    )
    original_name = models.CharField(
        max_length=255
    )
    file = models.FileField(
        upload_to=user_directory_path
    )
    size = models.BigIntegerField()
    upload_date = models.DateTimeField(
        auto_now_add=True
    )
    last_download = models.DateTimeField(
        null=True,
        blank=True
    )
    comment = models.TextField(
        blank=True
    )
    shared_link = models.UUIDField(
        default=uuid.uuid4,
        unique=True
    )

    def save(self, *args, **kwargs):
        """
        Save the UserFile model to the database.

        If the UserFile is created for the first time,
        set the size and original_name fields from the
        file, and then save the model again with only
        the size and original_name fields updated.

        :param args: Additional positional arguments
        to pass to the save() method.
        :param kwargs: Additional keyword arguments
        to pass to the save() method.
        :return: None
        """
        if self.file and not self.pk:
            file = self.file
            self.file = None

            super().save(*args, **kwargs)

            self.file = file
            self.size = file.size
            self.original_name = os.path.basename(file.name)

        super().save(*args, **kwargs)

    def __str__(self):
        """
        Return a string representation of the UserFile.

        The string representation includes the username
        of the user who uploaded the file and the original
        name of the file.

        :return: A string representation of the UserFile.
        """
        return f"{self.user.username}: {self.original_name}"

    def get_file_path(self):
        """
        Retrieve the file path of the associated file.

        This method returns the path of the file stored
        in the UserFile instance if the file exists. If
        there is no file associated with the instance,
        it returns None.

        :return: The file path as a string, or None if
        no file is associated with the instance.
        """
        if self.file:
            return self.file.path
        return None

    @property
    def file_exists(self):
        """
        Check if the file associated with this UserFile exists.

        :return: True if the file exists, False otherwise.
        """
        return self.file and os.path.exists(self.file.path)

    class Meta:
        verbose_name = 'File'
        verbose_name_plural = 'Files'
