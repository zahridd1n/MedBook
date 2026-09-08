from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    # Dashboard — Products
    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.product_add, name='product_add'),
    path('products/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),
    path('products/<int:pk>/toggle/', views.product_toggle, name='product_toggle'),

    # Dashboard — Orders
    path('orders/', views.order_list, name='order_list'),
    path('orders/<int:pk>/status/', views.order_update_status, name='order_update_status'),
    path('orders/<int:pk>/delete/', views.order_delete, name='order_delete'),
]
