from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_list, name='list'),
    path('popup/', views.notification_popup, name='popup'),
    path('mark-read/<int:pk>/', views.mark_read, name='mark_read'),
    path('mark-all-read/', views.mark_all_read, name='mark_all_read'),
    path('unread-count/', views.unread_count, name='unread_count'),
]
