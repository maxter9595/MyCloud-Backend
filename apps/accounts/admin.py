from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html

from .models import CustomUser


class CustomUserAdmin(UserAdmin):
    list_display = (
        'username',
        'email',
        'full_name',
        'is_staff',
        'is_superuser',
        'storage_usage_column',
    )
    list_filter = (
        'is_staff',
        'is_superuser',
    )
    fieldsets = (
        (
            None, {
                'fields': (
                    'username',
                    'password'
                )
            }
        ),
        (
            'Personal info', {
                'fields': (
                    'full_name',
                    'email',
                    'storage_path',
                    'max_storage'
                )
            }
        ),
        (
            'Permissions', {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'groups',
                    'user_permissions'
                )
            }
        ),
        (
            'Important dates', {
                'fields': (
                    'last_login',
                    'date_joined'
                )
            }
        ),
    )
    add_fieldsets = (
        (None, {
            'classes': (
                'wide',
            ),
            'fields': (
                'username',
                'email',
                'full_name',
                'password1',
                'password2',
                'max_storage'
            )
        }),
    )

    def storage_usage_column(self, obj):
        """
        Generates a column in the admin interface that displays
        a bar chart illustrating the user's current storage usage.

        :param obj: The user object being rendered.
        :return: A string containing the HTML for the bar chart.
        """
        usage = obj.get_storage_usage()
        max_storage = obj.max_storage
        percent = (usage / max_storage) * 100 if max_storage else 0

        return format_html(
            '<div style="width:100%; background:#ddd;">'
            '<div style="width:{}%; background:{}; height:20px;"></div>'
            '<div>{:.1f}% ({} / {} MB)</div>'
            '</div>',
            min(100, percent),
            'red' if percent > 90 else 'green',
            percent,
            round(usage / (1024 * 1024)),
            round(max_storage / (1024 * 1024))
        )

    storage_usage_column.short_description = 'Storage usage'


admin.site.register(CustomUser, CustomUserAdmin)
