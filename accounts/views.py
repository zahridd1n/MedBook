from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm, LoginForm
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
        if request.user.is_superuser:
            return redirect('superadmin:dashboard')
        
        next_url = request.GET.get('next', '')
        if next_url.startswith('/superadmin/'):
            logout(request)
            messages.info(request, "Superadmin sahifasiga kirish uchun administrator hisobingiz bilan tizimga kiring.")
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
        messages.error(request, 'Invalid email or password.')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('marketing:home')
