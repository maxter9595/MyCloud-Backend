from django.contrib import admin

from .models import UserFile


@admin.register(UserFile)
class UserFileAdmin(admin.ModelAdmin):
    list_display = (
        'original_name',
        'user',
        'size',
        'upload_date'
    )
    list_filter = (
        'user',
    )
    search_fields = (
        'original_name',
        'user__username'
    )
    readonly_fields = (
        'size',
        'upload_date',
        'last_download'
    )
