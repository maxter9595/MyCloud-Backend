# Generated by Django 4.2 on 2025-07-28 05:55

import apps.storage.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('original_name', models.CharField(max_length=255)),
                ('file', models.FileField(upload_to=apps.storage.models.user_directory_path)),
                ('size', models.BigIntegerField()),
                ('upload_date', models.DateTimeField(auto_now_add=True)),
                ('last_download', models.DateTimeField(blank=True, null=True)),
                ('comment', models.TextField(blank=True)),
                ('shared_link', models.UUIDField(default=uuid.uuid4, unique=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'File',
                'verbose_name_plural': 'Files',
            },
        ),
    ]
