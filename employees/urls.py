from django.urls import path
from . import views

app_name = 'employees'

urlpatterns = [
    path('', views.employee_list, name='list'),
    path('add/', views.employee_create, name='create'),
    path('<int:pk>/edit/', views.employee_edit, name='edit'),
    path('<int:pk>/delete/', views.employee_delete, name='delete'),
    path('<int:pk>/schedule/', views.employee_schedule, name='schedule'),
]
