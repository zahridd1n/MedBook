from django.urls import path
from . import views

app_name = 'business'

urlpatterns = [
    path('setup/', views.business_setup, name='setup'),
    path('working-hours/', views.working_hours, name='working_hours'),
    path('faq/', views.faq_list, name='faq_list'),
    path('faq/add/', views.faq_create, name='faq_create'),
    path('faq/<int:pk>/edit/', views.faq_edit, name='faq_edit'),
    path('faq/<int:pk>/delete/', views.faq_delete, name='faq_delete'),
    path('branding/', views.branding_settings, name='branding'),
    path('branding/css-docs/', views.css_docs, name='css_docs'),
    path('telegram/', views.telegram_settings, name='telegram'),
]
