from django.urls import path
from . import views

app_name = 'superadmin'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('businesses/', views.businesses_list, name='businesses'),
    path('businesses/<int:pk>/', views.business_detail, name='business_detail'),
    path('businesses/<int:pk>/toggle-block/', views.toggle_block, name='toggle_block'),
    path('businesses/<int:pk>/update-subscription/', views.update_subscription, name='update_subscription'),
    path('businesses/<int:pk>/change-password/', views.change_owner_password, name='change_owner_password'),
    path('subscriptions/', views.subscriptions, name='subscriptions'),
    path('site-settings/', views.site_settings, name='site_settings'),
    path('statistics/', views.statistics, name='statistics'),
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/<int:pk>/', views.payment_detail, name='payment_detail'),
    path('pricing-plans/', views.pricing_plan_list, name='pricing_plan_list'),
    path('pricing-plans/create/', views.pricing_plan_create, name='pricing_plan_create'),
    path('pricing-plans/<int:pk>/edit/', views.pricing_plan_edit, name='pricing_plan_edit'),
    path('pricing-plans/<int:pk>/delete/', views.pricing_plan_delete, name='pricing_plan_delete'),
]
