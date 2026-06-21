import secrets
from datetime import timedelta
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from .forms import RegisterForm, LoginForm, PasswordResetRequestForm, SetNewPasswordForm
from .models import User


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created! Set up your business profile.')
            return redirect('business:setup')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect(request.GET.get('next', 'dashboard:home'))
        messages.error(request, 'Invalid email or password.')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('marketing:home')


def password_reset_request(request):
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                token = secrets.token_urlsafe(32)
                user.reset_token = token
                user.reset_token_expiry = timezone.now() + timedelta(hours=2)
                user.save(update_fields=['reset_token', 'reset_token_expiry'])
                reset_url = f"{settings.SITE_URL}/accounts/password-reset/{token}/"
                send_mail(
                    'Password Reset', f'Reset link: {reset_url}',
                    settings.DEFAULT_FROM_EMAIL, [email], fail_silently=True,
                )
            except User.DoesNotExist:
                pass
            messages.success(request, 'If that email exists, a reset link has been sent.')
            return redirect('accounts:login')
    else:
        form = PasswordResetRequestForm()
    return render(request, 'accounts/password_reset_request.html', {'form': form})


def password_reset_confirm(request, token):
    try:
        user = User.objects.get(reset_token=token)
        if user.reset_token_expiry < timezone.now():
            messages.error(request, 'Reset link has expired.')
            return redirect('accounts:password_reset')
    except User.DoesNotExist:
        messages.error(request, 'Invalid reset link.')
        return redirect('accounts:password_reset')
    if request.method == 'POST':
        form = SetNewPasswordForm(request.POST)
        if form.is_valid():
            user.set_password(form.cleaned_data['password1'])
            user.reset_token = ''
            user.reset_token_expiry = None
            user.save()
            messages.success(request, 'Password updated. You can now log in.')
            return redirect('accounts:login')
    else:
        form = SetNewPasswordForm()
    return render(request, 'accounts/password_reset_confirm.html', {'form': form})
