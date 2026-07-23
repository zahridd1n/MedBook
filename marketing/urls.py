from django.urls import path
from . import views

app_name = 'marketing'

urlpatterns = [
    path('', views.home, name='home'),
    path('features/', views.features, name='features'),
    path('pricing/', views.pricing, name='pricing'),
    path('faq/', views.faq, name='faq'),
    path('contact/', views.contact, name='contact'),
    path('businesses/', views.businesses_directory, name='businesses'),
    path('tutorials/', views.tutorials, name='tutorials'),
    # Legal pages
    path('oferta/', views.oferta, name='oferta'),
    path('privacy/', views.privacy, name='privacy'),
    path('terms/', views.terms, name='terms'),
]
