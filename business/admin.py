from django.contrib import admin
from .models import Business, WorkingHours, FAQ, Payment


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


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('business', 'plan', 'amount', 'status', 'created_at')
    list_filter = ('status', 'plan', 'created_at')
    search_fields = ('business__name', 'note')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['approve_payments', 'reject_payments']

    def approve_payments(self, request, queryset):
        for payment in queryset:
            payment.status = 'approved'
            payment.save()
        self.message_user(request, "To'lovlar tasdiqlandi.")

    def reject_payments(self, request, queryset):
        for payment in queryset:
            payment.status = 'rejected'
            payment.save()
        self.message_user(request, "To'lovlar rad etildi.")

    approve_payments.short_description = "Tanlangan to'lovlarni tasdiqlash"
    reject_payments.short_description = "Tanlangan to'lovlarni rad etish"
