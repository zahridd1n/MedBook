from django.urls import path
from . import views
from blog.views import blog_public_list, blog_public_detail

app_name = 'public'

urlpatterns = [
    path('<slug:slug>/', views.public_home, name='home'),
    path('<slug:slug>/book/', views.booking_step1_service, name='booking_step1'),
    path('<slug:slug>/book/<int:service_id>/<int:employee_id>/', views.booking_step3_datetime, name='booking_step2'),
    path('<slug:slug>/book/confirm/', views.booking_step4_confirm, name='booking_step3'),
    path('<slug:slug>/book/success/', views.booking_success, name='booking_success'),

    # Blog URLs
    path('<slug:slug>/blog/', blog_public_list, name='blog-list'),
    path('<slug:slug>/blog/<slug:post_slug>/', blog_public_detail, name='blog-detail'),
]
