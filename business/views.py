from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.conf import settings

from .models import Business, WorkingHours, FAQ
from .forms import BusinessSetupForm, FAQForm


def _get_business(request):
    try:
        return request.user.business
    except Business.DoesNotExist:
        return None


# ─── Dashboard Home ───────────────────────────────────────────────────────────

@login_required
def dashboard_home(request):
    business = _get_business(request)
    if not business:
        return redirect('business:setup')

    today = timezone.localdate()
    appts = business.appointments.select_related('customer', 'service', 'employee')

    context = {
        'business': business,
        'total_appointments': appts.count(),
        'today_count': appts.filter(date=today).count(),
        'upcoming_appointments': (
            appts.filter(date__gte=today, status__in=['new', 'confirmed'])
                 .order_by('date', 'time')[:5]
        ),
        'total_customers': business.customers.count(),
        'unread_notifications': business.notifications.filter(is_read=False).count(),
        'recent_appointments': appts.order_by('-created_at')[:10],
        'today': today,
    }
    return render(request, 'dashboard/home.html', context)


# ─── Business Setup / Settings ────────────────────────────────────────────────

@login_required
def business_setup(request):
    business = _get_business(request)
    if request.method == 'POST':
        form = BusinessSetupForm(request.POST, request.FILES, instance=business)
        if form.is_valid():
            b = form.save(commit=False)
            b.owner = request.user
            b.save()
            if not business:
                # Create default working hours for new business
                for day in range(7):
                    WorkingHours.objects.get_or_create(
                        business=b, day=day,
                        defaults={'is_open': day < 6, 'open_time': '09:00', 'close_time': '18:00'},
                    )
            messages.success(request, 'Business settings saved.')
            return redirect('dashboard:home')
    else:
        form = BusinessSetupForm(instance=business)
    return render(request, 'dashboard/settings/business.html', {'form': form, 'business': business})


# ─── Working Hours ────────────────────────────────────────────────────────────

@login_required
def working_hours(request):
    business = get_object_or_404(Business, owner=request.user)
    # Ensure all 7 days exist
    existing = {h.day for h in business.working_hours.all()}
    for day in range(7):
        if day not in existing:
            WorkingHours.objects.create(business=business, day=day, is_open=False)
    hours = list(business.working_hours.order_by('day'))

    if request.method == 'POST':
        for h in hours:
            h.is_open = request.POST.get(f'is_open_{h.day}') == 'on'
            h.open_time = request.POST.get(f'open_time_{h.day}') or None
            h.close_time = request.POST.get(f'close_time_{h.day}') or None
            h.save()
        messages.success(request, 'Working hours saved.')
        return redirect('business:working_hours')
    return render(request, 'dashboard/settings/working_hours.html', {
        'business': business, 'hours': hours,
    })


# ─── FAQ ──────────────────────────────────────────────────────────────────────

@login_required
def faq_list(request):
    business = get_object_or_404(Business, owner=request.user)
    return render(request, 'dashboard/settings/faq_list.html', {
        'business': business, 'faqs': business.faqs.all(),
    })


@login_required
def faq_create(request):
    business = get_object_or_404(Business, owner=request.user)
    if request.method == 'POST':
        form = FAQForm(request.POST)
        if form.is_valid():
            f = form.save(commit=False)
            f.business = business
            f.save()
            messages.success(request, 'FAQ added.')
            return redirect('business:faq_list')
    else:
        form = FAQForm()
    return render(request, 'dashboard/settings/faq_form.html', {
        'form': form, 'business': business, 'action': 'Add',
    })


@login_required
def faq_edit(request, pk):
    business = get_object_or_404(Business, owner=request.user)
    faq = get_object_or_404(FAQ, pk=pk, business=business)
    if request.method == 'POST':
        form = FAQForm(request.POST, instance=faq)
        if form.is_valid():
            form.save()
            messages.success(request, 'FAQ updated.')
            return redirect('business:faq_list')
    else:
        form = FAQForm(instance=faq)
    return render(request, 'dashboard/settings/faq_form.html', {
        'form': form, 'business': business, 'action': 'Edit',
    })


@login_required
def faq_delete(request, pk):
    business = get_object_or_404(Business, owner=request.user)
    faq = get_object_or_404(FAQ, pk=pk, business=business)
    if request.method == 'POST':
        faq.delete()
        messages.success(request, 'FAQ deleted.')
    return redirect('business:faq_list')


# ─── Telegram Settings ────────────────────────────────────────────────────────

@login_required
def telegram_settings(request):
    """
    Telegram bot notification settings page.

    Actions (POST):
      generate_link  — create a one-time connect token and show the t.me deep link
      disconnect     — remove chat_id, disable notifications
      toggle         — enable / disable notifications without disconnecting
      test           — send a test message to the connected chat
      set_webhook    — register webhook URL with Telegram (admin action)
    """
    business = get_object_or_404(Business, owner=request.user)
    bot_token_set = bool(settings.TELEGRAM_BOT_TOKEN)
    bot_username = settings.TELEGRAM_BOT_USERNAME

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'generate_link':
            if not bot_token_set:
                messages.error(request, 'TELEGRAM_BOT_TOKEN is not set in your .env file.')
            elif not bot_username:
                messages.error(request, 'TELEGRAM_BOT_USERNAME is not set in your .env file.')
            else:
                business.generate_connect_token()
                messages.success(request, 'Connection link generated. Click it to open Telegram.')

        elif action == 'disconnect':
            business.telegram_chat_id = ''
            business.telegram_notifications_enabled = False
            business.telegram_connect_token = ''
            business.save(update_fields=[
                'telegram_chat_id', 'telegram_notifications_enabled', 'telegram_connect_token'
            ])
            messages.success(request, 'Telegram disconnected successfully.')

        elif action == 'toggle':
            if not business.telegram_chat_id:
                messages.error(request, 'Connect Telegram first before enabling notifications.')
            else:
                business.telegram_notifications_enabled = not business.telegram_notifications_enabled
                business.save(update_fields=['telegram_notifications_enabled'])
                state = 'enabled' if business.telegram_notifications_enabled else 'paused'
                messages.success(request, f'Telegram notifications {state}.')

        elif action == 'test':
            if not business.telegram_chat_id:
                messages.error(request, 'Telegram is not connected yet.')
            else:
                from notifications.utils import send_telegram_message
                ok = send_telegram_message(
                    business.telegram_chat_id,
                    f'🔔 <b>Test Notification</b>\n\n'
                    f'Hello from <b>{business.name}</b>!\n'
                    f'Your Telegram notifications are working correctly. ✅\n\n'
                    f'<i>You will receive a message like this every time a new booking arrives.</i>'
                )
                if ok:
                    messages.success(request, '✅ Test message sent! Check your Telegram.')
                else:
                    messages.error(request, '❌ Failed to send. Check that TELEGRAM_BOT_TOKEN is correct.')

        elif action == 'set_webhook':
            from notifications.utils import set_telegram_webhook
            result = set_telegram_webhook(settings.SITE_URL)
            if result.get('ok'):
                messages.success(request, f'Webhook set to {settings.SITE_URL}/telegram/webhook/…')
            else:
                messages.error(request, f'Webhook error: {result.get("description", result)}')

        return redirect('business:telegram')

    # ── GET ──────────────────────────────────────────────────────────────────
    connect_url = business.get_telegram_connect_url() if business.telegram_connect_token else None

    # Fetch webhook info (only if token is set)
    webhook_info = {}
    if bot_token_set:
        try:
            from notifications.utils import get_webhook_info, get_bot_info
            webhook_info = get_webhook_info()
            bot_info = get_bot_info()
            if bot_info.get('username') and not bot_username:
                bot_username = bot_info['username']
        except Exception:
            pass

    return render(request, 'dashboard/settings/telegram.html', {
        'business': business,
        'connect_url': connect_url,
        'bot_token_set': bot_token_set,
        'bot_username': bot_username,
        'webhook_info': webhook_info,
    })
