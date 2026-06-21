from django import forms
from .models import Appointment


class AppointmentForm(forms.ModelForm):
    customer_name = forms.CharField(max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}))
    customer_phone = forms.CharField(max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+998901234567'}))

    class Meta:
        model = Appointment
        fields = ('service', 'employee', 'date', 'time', 'status', 'notes')
        widgets = {
            'service': forms.Select(attrs={'class': 'form-select'}),
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, business=None, **kwargs):
        super().__init__(*args, **kwargs)
        if business:
            self.fields['service'].queryset = business.services.filter(is_active=True)
            self.fields['employee'].queryset = business.employees.filter(is_active=True)
            self.fields['employee'].required = False
        if self.instance and self.instance.pk and self.instance.customer:
            self.fields['customer_name'].initial = self.instance.customer.full_name
            self.fields['customer_phone'].initial = self.instance.customer.phone


class BookingForm(forms.Form):
    """Public-facing booking form."""
    service = forms.IntegerField(widget=forms.HiddenInput())
    employee = forms.IntegerField(required=False, widget=forms.HiddenInput())
    date = forms.DateField(widget=forms.HiddenInput())
    time = forms.TimeField(widget=forms.HiddenInput())
    customer_name = forms.CharField(max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Your full name'}))
    customer_phone = forms.CharField(max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Phone number'}))
    notes = forms.CharField(required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Notes (optional)'}))
