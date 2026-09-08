from django.contrib import admin
from .models import Product, Order


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'business', 'price', 'is_active', 'order']
    list_filter = ['is_active', 'business']
    search_fields = ['name', 'business__name']
    list_editable = ['is_active', 'order']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['customer_name', 'customer_phone', 'product', 'business', 'status', 'created_at']
    list_filter = ['status', 'business']
    search_fields = ['customer_name', 'customer_phone']
    readonly_fields = ['created_at']
