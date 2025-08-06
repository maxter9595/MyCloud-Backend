from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from .models import UserFile


class FileSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    is_shared_expired = serializers.SerializerMethodField()

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
            'shared_expiry',
            'is_shared_expired',
            'user'
        ]
        read_only_fields = [
            'original_name',
            'size',
            'upload_date',
            'last_download',
            'shared_link',
            'is_shared_expired',
            'user'
        ]

    def get_is_shared_expired(self, obj):
        return obj.is_shared_link_expired()


class FileShareSerializer(serializers.ModelSerializer):
    expiry_days = serializers.IntegerField(
        write_only=True,
        required=False,
        min_value=1,
        max_value=365,
        help_text="The number of days the link is valid"
    )

    class Meta:
        model = UserFile
        fields = ['shared_link', 'shared_expiry', 'expiry_days']
        read_only_fields = ['shared_link', 'shared_expiry']

    def update(self, instance, validated_data):
        expiry_days = validated_data.pop('expiry_days', None)
        
        if expiry_days:
            instance.shared_expiry = timezone.now() + timedelta(days=expiry_days)
            instance.save()
        
        return instance
