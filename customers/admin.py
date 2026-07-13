from django.contrib import admin
from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone', 'email', 'business', 'appointment_count', 'created_at')
    list_filter = ('business', 'created_at')
    search_fields = ('full_name', 'phone', 'email', 'business__name')
    readonly_fields = ('created_at', 'updated_at', 'appointment_count', 'last_visit')
    list_select_related = ('business',)
