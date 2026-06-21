from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from notifications.views import telegram_webhook
from blog.views import blog_public_list, blog_public_detail
from public_site.views import (
    public_home, booking_step1_service,
    booking_step3_datetime, booking_step4_confirm, booking_success
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # Telegram Bot webhook (CSRF exempt, no login needed)
    path('telegram/webhook/<str:token>/', telegram_webhook, name='telegram_webhook'),

    # Marketing landing pages
    path('', include('marketing.urls')),

    # Authentication
    path('accounts/', include('accounts.urls')),

    # Dashboard (namespaced)
    path('dashboard/', include('business.dashboard_urls')),   # app_name='dashboard'
    path('dashboard/', include('business.urls')),             # app_name='business'
    path('dashboard/appointments/', include('appointments.urls')),
    path('dashboard/services/', include('services.urls')),
    path('dashboard/employees/', include('employees.urls')),
    path('dashboard/customers/', include('customers.urls')),
    path('dashboard/notifications/', include('notifications.urls')),
    path('dashboard/', include('blog.urls')),

    # Public business pages — slug-based, must be LAST
    # Home and booking (3-step flow)
    re_path(r'^(?P<slug>[\w-]+)/$', public_home, name='public-home'),
    re_path(r'^(?P<slug>[\w-]+)/book/$', booking_step1_service, name='public-booking-step1'),
    re_path(r'^(?P<slug>[\w-]+)/book/(?P<service_id>\d+)/(?P<employee_id>\d+)/$', booking_step3_datetime, name='public-booking-step2'),
    re_path(r'^(?P<slug>[\w-]+)/book/confirm/$', booking_step4_confirm, name='public-booking-step3'),
    re_path(r'^(?P<slug>[\w-]+)/book/success/$', booking_success, name='public-booking-success'),
    
    # Blog URLs
    re_path(r'^(?P<slug>[\w-]+)/blog/$', blog_public_list, name='public-blog-list'),
    re_path(r'^(?P<slug>[\w-]+)/blog/(?P<post_slug>[\w-]+)/$', blog_public_detail, name='public-blog-detail'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
