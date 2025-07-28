from django.conf import settings
from rest_framework import serializers

from .models import CustomUser


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True
    )
    confirmPassword = serializers.CharField(
        write_only=True,
        required=True
    )
    is_staff = serializers.BooleanField(
        read_only=True
    )
    is_superuser = serializers.BooleanField(
        read_only=True
    )
    storage_usage = serializers.SerializerMethodField()
    max_storage_gb = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            'id',
            'username',
            'email',
            'full_name',
            'password',
            'confirmPassword',
            'is_staff',
            'is_superuser',
            'storage_path',
            'is_active',
            'max_storage',
            'storage_usage',
            'max_storage_gb'
        ]
        extra_kwargs = {
            'password': {
                'write_only': True
            },
            'confirmPassword': {
                'write_only': True
            },
        }

    def get_storage_usage(self, obj):
        """
        Return the total storage usage for the user in bytes.

        :param obj: The user object
        :return: The total storage usage in bytes
        """
        return obj.get_storage_usage()

    def get_max_storage_gb(self, obj):
        """
        Return the maximum storage limit for the user in gigabytes.

        :param obj: The user object
        :return: The maximum storage limit in gigabytes
        """
        if obj.max_storage:
            return round(obj.max_storage / (1024 ** 3), 2)
        return 0

    def validate(self, data):
        """
        Validate that the password and confirmPassword fields match.

        :param data: The validated data
        :return: The validated data
        """
        if 'password' in data and 'confirmPassword' in data:
            if data['password'] != data['confirmPassword']:
                raise serializers.ValidationError("Passwords don't match")
        return data

    def to_representation(self, instance):
        """
        Customize the representation of the user object to include
        the storage usage and maximum storage limit.

        :param instance: The user object
        :return: The customized representation of the user object
        """
        representation = super().to_representation(instance)
        representation['storage_usage'] = self.get_storage_usage(instance)
        representation['max_storage_gb'] = self.get_max_storage_gb(instance)
        return representation

    def create(self, validated_data):
        """
        Create a new user.

        :param validated_data: The validated data to create the user with
        :return: The newly created user
        """
        validated_data.pop('confirmPassword')
        is_superuser = validated_data.pop('is_superuser', False)
        is_staff = validated_data.pop('is_staff', False)

        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            full_name=validated_data['full_name'],
            password=validated_data['password'],
            is_superuser=is_superuser,
            is_staff=is_staff,
            max_storage=validated_data.get(
                'max_storage',
                settings.DEFAULT_USER_BYTES
            )
        )
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True
    )

    class Meta:
        model = CustomUser
        fields = [
            'id',
            'username',
            'email',
            'full_name',
            'password',
            'is_staff',
            'is_superuser',
            'storage_path',
            'is_active',
            'max_storage'
        ]
        read_only_fields = [
            'username',
            'email'
        ]

    def update(self, instance, validated_data):
        """
        Update a user instance with validated data.

        :param instance: The user instance to update
        :param validated_data: The validated data containing fields to update
        :return: The updated user instance
        """
        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password)
        return super().update(instance, validated_data)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        """
        Validate that the username and password fields are present and non-empty.

        :param data: The validated data
        :return: The validated data
        """
        return data


class AdminCreateSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields

    def create(self, validated_data):
        """
        Create a new admin user instance with validated data.

        :param validated_data: The validated data containing fields to create
        :return: The created user instance
        """
        validated_data.pop('confirmPassword', None)
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            full_name=validated_data['full_name'],
            password=validated_data['password'],
            is_superuser=True,
            is_staff=True,
            max_storage=settings.MAX_ADMIN_BYTES
        )
        return user
