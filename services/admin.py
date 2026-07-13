from django.contrib import admin
from .models import Service


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'business', 'duration', 'duration_display', 'price', 'is_active', 'order', 'created_at')
    list_filter = ('is_active', 'business')
    search_fields = ('name', 'description', 'business__name')
    readonly_fields = ('created_at', 'duration_display')
    list_editable = ('is_active', 'order')
    list_select_related = ('business',)
