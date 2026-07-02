from django import forms
from .models import Employee, EmployeeSchedule


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ('name', 'position', 'photo', 'bio', 'services', 'order', 'is_active', 'is_visible_on_public')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'services': forms.CheckboxSelectMultiple(),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
            'is_visible_on_public': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
        }

    def __init__(self, *args, business=None, **kwargs):
        super().__init__(*args, **kwargs)
        if business:
            self.fields['services'].queryset = business.services.filter(is_active=True)
