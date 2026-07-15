import json
import logging
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.translation import gettext as _

from .decorators import superuser_required
from .models import SiteSettings
from .forms import SiteSettingsForm
from .telegram_bot import handle_callback, send_message
from business.models import Business, Payment
from appointments.models import Appointment
from accounts.models import User

logger = logging.getLogger(__name__)


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
        messages.success(request, _(f'"{business.name}" {state}.'))
    return redirect(request.POST.get('next', 'superadmin:businesses'))


# ─── Subscriptions List (OBUNALAR) ───────────────────────────────────────────

@superuser_required
def subscriptions(request):
    from datetime import timedelta
    qs = Business.objects.select_related('owner').order_by('-created_at')

    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(name__icontains=q) | Q(owner__email__icontains=q) |
            Q(owner__first_name__icontains=q) | Q(owner__last_name__icontains=q)
        )

    plan = request.GET.get('plan', '')
    if plan:
        qs = qs.filter(subscription_plan=plan)

    sub_status = request.GET.get('sub_status', '')
    if sub_status:
        qs = qs.filter(subscription_status=sub_status)

    expiring = request.GET.get('expiring', '')
    now = timezone.now()
    if expiring == '7':
        qs = qs.filter(
            subscription_end__gte=now, subscription_end__lte=now + timedelta(days=7),
            subscription_status__in=['trial', 'active'],
        )
    elif expiring == '30':
        qs = qs.filter(
            subscription_end__gte=now, subscription_end__lte=now + timedelta(days=30),
            subscription_status__in=['trial', 'active'],
        )

    all_qs = Business.objects.all()
    stats = {
        'total': all_qs.count(),
        'by_plan': {
            'free': all_qs.filter(subscription_plan='free').count(),
            'growth': all_qs.filter(subscription_plan='growth').count(),
            'enterprise': all_qs.filter(subscription_plan='enterprise').count(),
        },
        'by_status': {
            'trial': all_qs.filter(subscription_status='trial').count(),
            'active': all_qs.filter(subscription_status='active').count(),
            'expired': all_qs.filter(subscription_status='expired').count(),
            'cancelled': all_qs.filter(subscription_status='cancelled').count(),
        },
        'blocked': all_qs.filter(is_blocked=True).count(),
        'expiring_7': all_qs.filter(
            subscription_end__gte=now, subscription_end__lte=now + timedelta(days=7),
            subscription_status__in=['trial', 'active'],
        ).count(),
    }

    context = {
        'subscriptions': qs,
        'stats': stats,
        'query': q,
        'selected_plan': plan,
        'selected_sub_status': sub_status,
        'selected_expiring': expiring,
        'total_count': qs.count(),
        'now': timezone.now(),
    }
    return render(request, 'superadmin/subscriptions.html', context)


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
        messages.success(request, _(f'"{business.name}" obunasi yangilandi.'))
    return redirect('superadmin:business_detail', pk=pk)


# ─── Site Settings ────────────────────────────────────────────────────────────

@superuser_required
def site_settings(request):
    settings_obj = SiteSettings.load()
    if request.method == 'POST':
        form = SiteSettingsForm(request.POST, request.FILES, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, _('Sayt sozlamalari saqlandi.'))
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
            messages.error(request, _('Yangi parol kiritilmadi.'))
        elif len(new_password) < 6:
            messages.error(request, _('Parol kamida 6 belgidan iborat bo\'lishi kerak.'))
        elif new_password != confirm:
            messages.error(request, _('Parollar bir-biriga mos kelmadi.'))
        else:
            business.owner.password = make_password(new_password)
            business.owner.save(update_fields=['password'])
            messages.success(request, _(f'"{business.owner.get_full_name}" paroli muvaffaqiyatli o\'zgartirildi.'))
    return redirect('superadmin:business_detail', pk=pk)


# ─── Payment Management ───────────────────────────────────────────────────────

@superuser_required
def payment_list(request):
    status_filter = request.GET.get('status', '')
    payments = Payment.objects.select_related('business__owner').all()
    if status_filter:
        payments = payments.filter(status=status_filter)
    context = {
        'payments': payments,
        'status_filter': status_filter,
    }
    return render(request, 'superadmin/payments.html', context)


@superuser_required
def payment_detail(request, pk):
    payment = get_object_or_404(Payment.objects.select_related('business__owner'), pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            payment.status = 'approved'
            business = payment.business
            business.subscription_plan = 'growth' if payment.plan == 'pro' else 'enterprise'
            business.subscription_status = 'active'
            business.subscription_start = timezone.now()
            business.subscription_end = timezone.now() + timedelta(days=30)
            business.save(update_fields=[
                'subscription_plan', 'subscription_status',
                'subscription_start', 'subscription_end',
            ])
            messages.success(request, _(f'"{business.name}" to\'lovi tasdiqlandi — {payment.get_plan_display()} faollashtirildi.'))
        elif action == 'reject':
            reason = request.POST.get('rejected_reason', '').strip()
            payment.status = 'rejected'
            payment.rejected_reason = reason
            messages.warning(request, _(f'"{payment.business.name}" to\'lovi rad etildi.'))
        payment.save(update_fields=['status', 'rejected_reason'])
        return redirect('superadmin:payment_list')

    context = {
        'payment': payment,
    }
    return render(request, 'superadmin/payment_detail.html', context)


# ─── Pricing Plans Management ──────────────────────────────────────────────────

from .models import PricingPlan
from .forms import PricingPlanForm, PricingPlanFeatureFormSet

@superuser_required
def pricing_plan_list(request):
    plans = PricingPlan.objects.all().order_by('order')
    return render(request, 'superadmin/pricing_plans/list.html', {'plans': plans})

@superuser_required
def pricing_plan_create(request):
    if request.method == 'POST':
        form = PricingPlanForm(request.POST)
        formset = PricingPlanFeatureFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            plan = form.save()
            formset.instance = plan
            formset.save()
            messages.success(request, _('Yangi tarif muvaffaqiyatli qo\'shildi.'))
            return redirect('superadmin:pricing_plan_list')
    else:
        form = PricingPlanForm()
        formset = PricingPlanFeatureFormSet()
    
    return render(request, 'superadmin/pricing_plans/form.html', {
        'form': form, 'formset': formset, 'action': 'Qo\'shish'
    })

@superuser_required
def pricing_plan_edit(request, pk):
    plan = get_object_or_404(PricingPlan, pk=pk)
    if request.method == 'POST':
        form = PricingPlanForm(request.POST, instance=plan)
        formset = PricingPlanFeatureFormSet(request.POST, instance=plan)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, _('Tarif muvaffaqiyatli yangilandi.'))
            return redirect('superadmin:pricing_plan_list')
    else:
        form = PricingPlanForm(instance=plan)
        formset = PricingPlanFeatureFormSet(instance=plan)
    
    return render(request, 'superadmin/pricing_plans/form.html', {
        'form': form, 'formset': formset, 'action': 'Tahrirlash'
    })

@superuser_required
def pricing_plan_delete(request, pk):
    plan = get_object_or_404(PricingPlan, pk=pk)
    if request.method == 'POST':
        plan.delete()
        messages.success(request, _('Tarif o\'chirildi.'))
        return redirect('superadmin:pricing_plan_list')
    return render(request, 'superadmin/pricing_plans/delete.html', {'plan': plan})


# ─── Superadmin Telegram Bot Webhook ──────────────────────────────────────────

@csrf_exempt
@require_POST
def superadmin_webhook(request, token):
    if token != getattr(settings, 'SUPERADMIN_BOT_TOKEN', ''):
        return HttpResponse(status=403)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'ok': False, 'error': _('Invalid JSON')}, status=400)

    logger.debug('[SuperadminBot] Update: %s', data)

    # Handle inline keyboard callback
    callback = data.get('callback_query', {})
    if callback:
        chat_id = callback.get('message', {}).get('chat', {}).get('id')
        callback_data = callback.get('data', '')
        if chat_id and callback_data:
            handle_callback(chat_id, callback_data)
        return JsonResponse({'ok': True})

    # Handle text commands
    message = data.get('message', {})
    chat = message.get('chat', {})
    chat_id = chat.get('id')
    text = (message.get('text') or '').strip()

    if chat_id and text == '/start':
        send_message(
            chat_id,
            '👋 <b>Xush kelibsiz!</b>\n\n'
            'Bu bot to\'lov cheklarini qabul qilish va tasdiqlash uchun.\n\n'
            '<b>Qo\'llanma:</b>\n'
            '1. Botni superadmin sifatida sozlang\n'
            '2. SUPERADMIN_CHAT_IDS ga shu chat id ni qo\'shing\n'
            '3. To\'lov kelganda avtomatik xabar olasiz\n\n'
            'Sizning chat id ingiz: <code>' + str(chat_id) + '</code>'
        )

    return JsonResponse({'ok': True})
