from django.contrib import admin
from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('customer', 'service', 'employee', 'date', 'time', 'status', 'business')
    list_filter = ('status', 'date', 'business')
    search_fields = ('customer__full_name', 'customer__phone', 'service__name')
    date_hierarchy = 'date'
    readonly_fields = ('created_at', 'updated_at', 'end_time')
