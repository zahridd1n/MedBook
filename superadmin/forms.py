from django import forms
from .models import SiteSettings


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = [
            'hero_title', 'hero_subtitle', 'marketing_content',
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
            'marketing_content': forms.Textarea(attrs={
                'class': 'form-control font-monospace',
                'rows': 8,
                'placeholder': '{"uz": {"home": {"title": "..."}}}',
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
                'class': 'form-control', 'placeholder': 'support@BookFlow.com',
            }),
            'contact_telegram': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'https://t.me/BookFlowBot',
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
            'marketing_content': 'Marketing matnlari (JSON: uz/ru/en)',
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


from .models import PricingPlan, PricingPlanFeature
from django.forms import inlineformset_factory

class PricingPlanForm(forms.ModelForm):
    class Meta:
        model = PricingPlan
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'price_monthly': forms.NumberInput(attrs={'class': 'form-control'}),
            'price_yearly': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_employees': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_appointments_monthly': forms.NumberInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'allow_telegram': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_email': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_custom_domain': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_branding': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_custom_css': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_google_calendar': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_api': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_white_label': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_popular': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PricingPlanFeatureForm(forms.ModelForm):
    class Meta:
        model = PricingPlanFeature
        fields = ['text', 'is_included', 'order']
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'order': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'is_included': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

PricingPlanFeatureFormSet = inlineformset_factory(
    PricingPlan, PricingPlanFeature,
    form=PricingPlanFeatureForm,
    extra=1,
    can_delete=True
)
