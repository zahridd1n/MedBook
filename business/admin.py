from django.contrib import admin
from .models import Business, WorkingHours, FAQ


class WorkingHoursInline(admin.TabularInline):
    model = WorkingHours
    extra = 0


class FAQInline(admin.TabularInline):
    model = FAQ
    extra = 0


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'owner', 'category', 'telegram_connected', 'is_active', 'created_at')
    list_filter = ('category', 'is_active', 'telegram_notifications_enabled')
    search_fields = ('name', 'slug', 'owner__email')
    readonly_fields = ('created_at', 'updated_at', 'telegram_chat_id')
    inlines = [WorkingHoursInline, FAQInline]

    @admin.display(boolean=True, description='Telegram')
    def telegram_connected(self, obj):
        return bool(obj.telegram_chat_id)
