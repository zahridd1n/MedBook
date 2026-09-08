from django import forms
from .models import Product, Order


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'price_label', 'image', 'is_active', 'order']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Mahsulot nomi',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Mahsulot haqida qisqacha ma\'lumot',
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0',
                'min': '0',
                'step': '0.01',
            }),
            'price_label': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'so\'m',
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
            }),
        }
        labels = {
            'name': 'Nomi *',
            'description': 'Tavsif',
            'price': 'Narx *',
            'price_label': 'Valyuta / birlik',
            'image': 'Rasm *',
            'is_active': 'Saytda ko\'rinsin',
            'order': 'Tartib raqami',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Image required only on create
        if self.instance and self.instance.pk:
            self.fields['image'].required = False


class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select form-select-sm'}),
        }
