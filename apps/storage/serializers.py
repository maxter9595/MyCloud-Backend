from rest_framework import serializers

from .models import UserFile


class FileSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = UserFile
        fields = [
            'id',
            'original_name',
            'size',
            'upload_date',
            'last_download',
            'comment',
            'shared_link',
            'user'
        ]
        read_only_fields = [
            'original_name',
            'size',
            'upload_date',
            'last_download',
            'shared_link',
            'user'
        ]
