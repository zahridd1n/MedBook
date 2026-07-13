from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'business', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'business')
    search_fields = ('title', 'message', 'business__name')
    readonly_fields = ('created_at',)
