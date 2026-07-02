from django import forms
from .models import SiteSettings


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = [
            'hero_title', 'hero_subtitle',
            'starter_price',
            'growth_price_monthly', 'growth_price_yearly',
            'enterprise_price_monthly', 'enterprise_price_yearly',
            'stats_uptime', 'stats_appointments', 'stats_businesses',
            'logo', 'contact_phone', 'contact_email', 'contact_telegram',
            'payment_card_number', 'payment_card_holder',
        ]
        widgets = {
            'hero_title': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Bosh sarlavha',
            }),
            'hero_subtitle': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3, 'placeholder': 'Taglavha',
            }),
            'starter_price': forms.NumberInput(attrs={
                'class': 'form-control', 'placeholder': '0',
            }),
            'growth_price_monthly': forms.NumberInput(attrs={
                'class': 'form-control', 'placeholder': '99000',
            }),
            'growth_price_yearly': forms.NumberInput(attrs={
                'class': 'form-control', 'placeholder': '79000',
            }),
            'enterprise_price_monthly': forms.NumberInput(attrs={
                'class': 'form-control', 'placeholder': '249000',
            }),
            'enterprise_price_yearly': forms.NumberInput(attrs={
                'class': 'form-control', 'placeholder': '199000',
            }),
            'stats_uptime': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': '99.9%',
            }),
            'stats_appointments': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': '20,000+',
            }),
            'stats_businesses': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': '500+',
            }),
            'logo': forms.FileInput(attrs={
                'class': 'form-control',
            }),
            'contact_phone': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': '+998 90 123 45 67',
            }),
            'contact_email': forms.EmailInput(attrs={
                'class': 'form-control', 'placeholder': 'support@booksaas.com',
            }),
            'contact_telegram': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'https://t.me/BookSaaSBot',
            }),
            'payment_card_number': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': '9860 0101 2345 6789',
            }),
            'payment_card_holder': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'SUPER ADMIN',
            }),
        }
        labels = {
            'hero_title': 'Bosh Sarlavha',
            'hero_subtitle': 'Taglavha',
            'starter_price': 'Start narxi (UZS/oy)',
            'growth_price_monthly': 'Pro oylik (UZS)',
            'growth_price_yearly': 'Pro yillik (UZS/oy)',
            'enterprise_price_monthly': 'Max oylik (UZS)',
            'enterprise_price_yearly': 'Max yillik (UZS/oy)',
            'stats_uptime': 'Uptime ko\'rsatkichi',
            'stats_appointments': 'Jami Bandlovlar',
            'stats_businesses': 'Faol Bizneslar',
            'logo': 'Sayt Logotipi',
            'contact_phone': 'Aloqa Telefon Raqami',
            'contact_email': 'Aloqa Email Manzili',
            'contact_telegram': 'Telegram Havolasi',
            'payment_card_number': 'Karta raqami',
            'payment_card_holder': 'Karta egasi (ism familya)',
        }
