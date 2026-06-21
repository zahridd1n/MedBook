from django import forms
from .models import Service


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ('name', 'description', 'duration', 'price', 'order', 'is_active')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'duration': forms.NumberInput(attrs={'class': 'form-control', 'min': 5, 'step': 5}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': '0.01'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }
