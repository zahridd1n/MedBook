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
    path('upgrade/', views.upgrade_view, name='upgrade'),
    path('payment/', views.payment_view, name='payment'),
    path('custom-domain/', views.custom_domain_settings, name='custom_domain'),
    path('google-calendar/', views.google_calendar_settings, name='google_calendar'),
    path('google-calendar/callback/', views.google_calendar_callback, name='google_calendar_callback'),
    path('analytics/', views.analytics, name='analytics'),
    path('white-label/', views.white_label_settings, name='white_label'),
    path('api/', views.api_settings, name='api'),
    path('api/docs/', views.api_docs, name='api_docs'),
    path('api/appointments/', views.api_appointments, name='api_appointments'),
    path('api/appointments/today/', views.api_appointments_today, name='api_appointments_today'),
    path('api/appointments/<int:pk>/', views.api_appointment_detail, name='api_appointment_detail'),
    path('api/services/', views.api_services, name='api_services'),
    path('api/employees/', views.api_employees, name='api_employees'),
    path('api/customers/', views.api_customers, name='api_customers'),
    path('api/stats/', views.api_stats, name='api_stats'),

    # Marketing — QR Code
    path('marketing/qr-code/', views.qr_code_settings, name='qr_code'),
    path('marketing/qr-code/download/<str:size>/<str:fmt>/', views.qr_download, name='qr_download'),
    path('marketing/link-sharing/', views.link_sharing, name='link_sharing'),
]
