from django import forms
from .models import Business, WorkingHours, FAQ


class BusinessSetupForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = (
            'name', 'category', 'about', 'logo',
            'phone', 'email', 'address', 'city',
            'telegram', 'instagram', 'website',
        )
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'about': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'telegram': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '@username'}),
            'instagram': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '@username'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
        }


class FAQForm(forms.ModelForm):
    class Meta:
        model = FAQ
        fields = ('question', 'answer', 'order', 'is_active')
        widgets = {
            'question': forms.TextInput(attrs={'class': 'form-control'}),
            'answer': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }
