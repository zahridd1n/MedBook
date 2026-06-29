from django import forms
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm, PasswordResetForm
from django.contrib.auth import get_user_model

User = get_user_model()


class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(label='Parol',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Parol'}))
    password2 = forms.CharField(label='Parol (takroran)',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Parol (takroran)'}))

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ism'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Familiya'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Telefon (ixtiyoriy)'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Bu email bilan hisob mavjud.')
        return email

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password1') != cleaned.get('password2'):
            raise forms.ValidationError('Parollar mos kelmadi.')
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.EmailField(label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email', 'autofocus': True}))
    password = forms.CharField(label='Parol',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Parol'}))


class PasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email manzilingiz'}))


class SetNewPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(label='Yangi parol',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Yangi parol'}))
    new_password2 = forms.CharField(label='Yangi parol (takroran)',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Yangi parol (takroran)'}))
