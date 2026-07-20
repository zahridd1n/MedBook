from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from .forms import RegisterForm, LoginForm
from .models import User
from django.conf import settings
from django.urls import reverse
import urllib.parse
import requests
import secrets


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, _('Account created! Set up your business profile.'))
            return redirect('business:setup')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('superadmin:dashboard')
        
        next_url = request.GET.get('next', '')
        if next_url.startswith('/superadmin/'):
            logout(request)
            messages.info(request, _("Superadmin sahifasiga kirish uchun administrator hisobingiz bilan tizimga kiring."))
        else:
            return redirect('dashboard:home')
            
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if user.is_superuser:
                next_url = request.GET.get('next', '')
                if next_url.startswith('/superadmin/'):
                    return redirect(next_url)
                return redirect('superadmin:dashboard')
            return redirect(request.GET.get('next', 'dashboard:home'))
        messages.error(request, _('Invalid email or password.'))
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('marketing:home')


def google_login(request):
    client_id = settings.GOOGLE_CLIENT_ID
    redirect_uri = request.build_absolute_uri(reverse('accounts:google_callback'))
    scope = 'openid email profile'
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': scope,
        'access_type': 'online',
    }
    url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    return redirect(url)


def google_callback(request):
    code = request.GET.get('code')
    if not code:
        messages.error(request, _('Google login failed or was cancelled.'))
        return redirect('accounts:login')

    client_id = settings.GOOGLE_CLIENT_ID
    client_secret = settings.GOOGLE_CLIENT_SECRET
    redirect_uri = request.build_absolute_uri(reverse('accounts:google_callback'))

    # Exchange code for token
    token_url = 'https://oauth2.googleapis.com/token'
    data = {
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }
    resp = requests.post(token_url, data=data)
    
    if not resp.ok:
        messages.error(request, _('Failed to authenticate with Google.'))
        return redirect('accounts:login')
        
    access_token = resp.json().get('access_token')

    # Get user info
    user_info_url = 'https://www.googleapis.com/oauth2/v3/userinfo'
    user_resp = requests.get(user_info_url, headers={'Authorization': f'Bearer {access_token}'})
    
    if not user_resp.ok:
        messages.error(request, _('Failed to fetch user info from Google.'))
        return redirect('accounts:login')

    user_info = user_resp.json()
    email = user_info.get('email')
    first_name = user_info.get('given_name', '')
    last_name = user_info.get('family_name', '')

    if not email:
        messages.error(request, _('Google account did not provide an email.'))
        return redirect('accounts:login')

    # Find or create user
    user, created = User.objects.get_or_create(email=email, defaults={
        'first_name': first_name,
        'last_name': last_name,
    })
    
    if created:
        # Set an unusable password
        user.set_unusable_password()
        user.save()

    login(request, user)
    
    if created:
        messages.success(request, _('Account created! Set up your business profile.'))
        return redirect('business:setup')
    
    return redirect('dashboard:home')
