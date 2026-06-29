from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from datetime import timedelta
import json

from .decorators import superuser_required
from .models import SiteSettings
from .forms import SiteSettingsForm
from business.models import Business
from appointments.models import Appointment
from accounts.models import User


# ─── Dashboard Home ───────────────────────────────────────────────────────────

@superuser_required
def dashboard(request):
    today = timezone.localdate()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    total_businesses = Business.objects.count()
    active_businesses = Business.objects.filter(is_blocked=False, is_active=True).count()
    blocked_businesses = Business.objects.filter(is_blocked=True).count()
    total_users = User.objects.count()
    total_appointments = Appointment.objects.count()
    today_appointments = Appointment.objects.filter(date=today).count()

    # Recent registrations (last 7 days)
    recent_businesses = (
        Business.objects.select_related('owner')
        .order_by('-created_at')[:10]
    )

    # New businesses this week/month
    new_this_week = Business.objects.filter(created_at__date__gte=week_ago).count()
    new_this_month = Business.objects.filter(created_at__date__gte=month_ago).count()

    # Subscription breakdown
    plan_counts = dict(
        Business.objects.values_list('subscription_plan')
        .annotate(c=Count('id'))
        .values_list('subscription_plan', 'c')
    )

    # Weekly registration trend (last 14 days)
    daily_reg = (
        Business.objects.filter(created_at__date__gte=today - timedelta(days=13))
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )
    chart_labels = []
    chart_data = []
    for i in range(14):
        d = today - timedelta(days=13 - i)
        chart_labels.append(d.strftime('%d/%m'))
        match = next((r for r in daily_reg if r['day'] == d), None)
        chart_data.append(match['count'] if match else 0)

    # Category breakdown
    category_data = dict(
        Business.objects.values_list('category')
        .annotate(c=Count('id'))
        .values_list('category', 'c')
    )

    context = {
        'total_businesses': total_businesses,
        'active_businesses': active_businesses,
        'blocked_businesses': blocked_businesses,
        'total_users': total_users,
        'total_appointments': total_appointments,
        'today_appointments': today_appointments,
        'recent_businesses': recent_businesses,
        'new_this_week': new_this_week,
        'new_this_month': new_this_month,
        'plan_counts': plan_counts,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
        'category_data': json.dumps(category_data),
        'category_labels': json.dumps(list(category_data.keys())),
        'category_values': json.dumps(list(category_data.values())),
    }
    return render(request, 'superadmin/dashboard.html', context)


# ─── Businesses List ──────────────────────────────────────────────────────────

@superuser_required
def businesses_list(request):
    qs = Business.objects.select_related('owner').order_by('-created_at')

    # Search
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(name__icontains=q) | Q(owner__email__icontains=q) |
            Q(owner__first_name__icontains=q) | Q(owner__last_name__icontains=q)
        )

    # Filter by category
    cat = request.GET.get('category', '')
    if cat:
        qs = qs.filter(category=cat)

    # Filter by status
    status = request.GET.get('status', '')
    if status == 'active':
        qs = qs.filter(is_blocked=False, is_active=True)
    elif status == 'blocked':
        qs = qs.filter(is_blocked=True)

    # Filter by plan
    plan = request.GET.get('plan', '')
    if plan:
        qs = qs.filter(subscription_plan=plan)

    context = {
        'businesses': qs,
        'query': q,
        'selected_category': cat,
        'selected_status': status,
        'selected_plan': plan,
        'category_choices': Business.CATEGORY_CHOICES,
        'total_count': qs.count(),
    }
    return render(request, 'superadmin/businesses.html', context)


# ─── Business Detail ─────────────────────────────────────────────────────────

@superuser_required
def business_detail(request, pk):
    business = get_object_or_404(Business.objects.select_related('owner'), pk=pk)
    appointments = business.appointments.select_related('customer', 'service').order_by('-date')[:20]
    employees = business.employees.all()
    services = business.services.all()
    customers_count = business.customers.count()

    context = {
        'business': business,
        'appointments': appointments,
        'employees': employees,
        'services': services,
        'customers_count': customers_count,
        'total_appointments': business.appointments.count(),
    }
    return render(request, 'superadmin/business_detail.html', context)


# ─── Toggle Block ─────────────────────────────────────────────────────────────

@superuser_required
def toggle_block(request, pk):
    if request.method == 'POST':
        business = get_object_or_404(Business, pk=pk)
        business.is_blocked = not business.is_blocked
        business.save(update_fields=['is_blocked'])
        state = 'bloklandi' if business.is_blocked else 'blokdan chiqarildi'
        messages.success(request, f'"{business.name}" {state}.')
    return redirect(request.POST.get('next', 'superadmin:businesses'))


# ─── Update Subscription ─────────────────────────────────────────────────────

@superuser_required
def update_subscription(request, pk):
    if request.method == 'POST':
        business = get_object_or_404(Business, pk=pk)
        plan = request.POST.get('subscription_plan', business.subscription_plan)
        status = request.POST.get('subscription_status', business.subscription_status)
        business.subscription_plan = plan
        business.subscription_status = status

        end_raw = request.POST.get('subscription_end', '').strip()
        if end_raw:
            from django.utils.dateparse import parse_datetime
            parsed = parse_datetime(end_raw)
            if parsed:
                business.subscription_end = parsed

        if status == 'active':
            if not business.subscription_start:
                business.subscription_start = timezone.now()
            if not end_raw and not business.subscription_end:
                business.subscription_end = timezone.now() + timedelta(days=30)

        if status == 'expired':
            business.subscription_plan = 'free'

        business.save(update_fields=[
            'subscription_plan', 'subscription_status', 'subscription_start', 'subscription_end',
        ])
        messages.success(request, f'"{business.name}" obunasi yangilandi.')
    return redirect('superadmin:business_detail', pk=pk)


# ─── Site Settings ────────────────────────────────────────────────────────────

@superuser_required
def site_settings(request):
    settings_obj = SiteSettings.load()
    if request.method == 'POST':
        form = SiteSettingsForm(request.POST, request.FILES, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sayt sozlamalari saqlandi.')
            return redirect('superadmin:site_settings')
    else:
        form = SiteSettingsForm(instance=settings_obj)
    return render(request, 'superadmin/site_settings.html', {'form': form})


# ─── Statistics ───────────────────────────────────────────────────────────────

@superuser_required
def statistics(request):
    today = timezone.localdate()

    # Monthly appointments trend (last 6 months)
    months_data = []
    for i in range(5, -1, -1):
        d = today - timedelta(days=30 * i)
        month_start = d.replace(day=1)
        if i > 0:
            next_month = (d + timedelta(days=32)).replace(day=1)
        else:
            next_month = today + timedelta(days=1)
        count = Appointment.objects.filter(
            date__gte=month_start, date__lt=next_month
        ).count()
        months_data.append({
            'label': month_start.strftime('%b %Y'),
            'count': count,
        })

    # Top 10 businesses by appointments
    top_businesses = (
        Business.objects.annotate(appt_count=Count('appointments'))
        .order_by('-appt_count')[:10]
    )

    # Category breakdown
    categories = (
        Business.objects.values('category')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    # Subscription plan breakdown
    plans = (
        Business.objects.values('subscription_plan')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    context = {
        'months_labels': json.dumps([m['label'] for m in months_data]),
        'months_data': json.dumps([m['count'] for m in months_data]),
        'top_businesses': top_businesses,
        'categories': categories,
        'plans': plans,
        'category_labels': json.dumps([c['category'] for c in categories]),
        'category_values': json.dumps([c['count'] for c in categories]),
        'plan_labels': json.dumps([p['subscription_plan'] for p in plans]),
        'plan_values': json.dumps([p['count'] for p in plans]),
    }
    return render(request, 'superadmin/statistics.html', context)


# ─── Change Owner Password ─────────────────────────────────────────────────────

@superuser_required
def change_owner_password(request, pk):
    business = get_object_or_404(Business, pk=pk)
    if request.method == 'POST':
        new_password = request.POST.get('new_password', '').strip()
        confirm = request.POST.get('confirm_password', '').strip()
        if not new_password:
            messages.error(request, 'Yangi parol kiritilmadi.')
        elif len(new_password) < 6:
            messages.error(request, 'Parol kamida 6 belgidan iborat bo\'lishi kerak.')
        elif new_password != confirm:
            messages.error(request, 'Parollar bir-biriga mos kelmadi.')
        else:
            business.owner.password = make_password(new_password)
            business.owner.save(update_fields=['password'])
            messages.success(request, f'"{business.owner.get_full_name}" paroli muvaffaqiyatli o\'zgartirildi.')
    return redirect('superadmin:business_detail', pk=pk)
