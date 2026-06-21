from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    # Dashboard blog URLs
    path('blog/', views.blog_list, name='list'),
    path('blog/create/', views.blog_create, name='create'),
    path('blog/<int:pk>/edit/', views.blog_edit, name='edit'),
    path('blog/<int:pk>/delete/', views.blog_delete, name='delete'),
]
