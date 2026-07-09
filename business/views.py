from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.conf import settings

from .models import Business, WorkingHours, FAQ, Payment
from .forms import BusinessSetupForm, FAQForm, BrandingForm
from superadmin.models import SiteSettings


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

    if business.is_blocked:
        return render(request, 'dashboard/blocked.html')

    was_downgraded = business.enforce_subscription()

    today = timezone.localdate()
    now = timezone.now()
    appts = business.appointments.select_related('customer', 'service', 'employee')

    sub_expiring = False
    days_left = None
    if business.subscription_end and business.subscription_plan != 'free':
        days_left = (business.subscription_end - now).days
        sub_expiring = days_left <= 7

    context = {
        'business': business,
        'sub_expiring': sub_expiring,
        'days_left': days_left,
        'was_downgraded': was_downgraded,
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
            if not b.subscription_plan:
                b.subscription_plan = 'free'
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


# ─── Branding / Page Customization ────────────────────────────────────────────

@login_required
def branding_settings(request):
    business = get_object_or_404(Business, owner=request.user)
    is_paid = business.subscription_plan != 'free'

    if request.method == 'POST':
        if not is_paid:
            messages.error(request, 'Sahifa dizaynini sozlash faqat pullik tariflarda mavjud.')
            return redirect('business:branding')

        # Handle remove banner separately (before form saves old value back)
        if request.POST.get('remove_banner') and not request.FILES.get('banner_image'):
            if business.banner_image:
                business.banner_image.delete(save=False)
            business.banner_image = None
            business.save(update_fields=['banner_image'])
            messages.success(request, 'Banner rasmi o\'chirildi.')
            return redirect('business:branding')

        form = BrandingForm(request.POST, request.FILES, instance=business)
        if form.is_valid():
            form.save()
            messages.success(request, 'Dizayn sozlamalari saqlandi.')
            return redirect('business:branding')
        else:
            for field, errors in form.errors.items():
                for err in errors:
                    messages.error(request, f'{field}: {err}')
    else:
        form = BrandingForm(instance=business)

    return render(request, 'dashboard/settings/branding.html', {
        'business': business,
        'form': form,
        'is_paid': is_paid,
    })


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


# ─── CSS Documentation ────────────────────────────────────────────────────────

CSS_SECTIONS = [
    {
        'title': 'Logotipni kattaroq qilish',
        'tag': 'img',
        'code': '.bk-hero__title img { height: 64px !important; }',
        'desc': 'Logotip rasmini kattalashtirish',
    },
    {
        'title': 'Hero matn rangini o\'zgartirish',
        'tag': 'text',
        'code': '.bk-hero__desc { color: rgba(255,255,255,0.8) !important; }',
        'desc': 'Slogan matni rangini oqroq qilish',
    },
    {
        'title': 'Kartochka fon rangini o\'zgartirish',
        'tag': 'card',
        'code': '.bk-service-card, .bk-team-card, .bk-hours-card { background: #fffaf0 !important; }',
        'desc': 'Xizmat va jamoa kartochkalari fon rangi',
    },
    {
        'title': 'Narx rangini yashil qilish',
        'tag': 'price',
        'code': '.bk-service-price { color: #10b981 !important; font-size: 1.3rem !important; }',
        'desc': 'Xizmat narxini yashil va kattaroq ko\'rsatish',
    },
    {
        'title': 'Orqa fon rangini o\'zgartirish',
        'tag': 'body',
        'code': 'body { background: #f0f4ff !important; }',
        'desc': 'Butun sahifa fon rangini o\'zgartirish',
    },
    {
        'title': 'Tugma hover effekti',
        'tag': 'button',
        'code': '.btn-book-primary:hover { transform: scale(1.05) !important; }',
        'desc': 'Tugma ustiga bosganda kattalashishi',
    },
    {
        'title': 'Kartochka chegarasi (border)',
        'tag': 'card',
        'code': '.bk-service-card { border: 2px solid #e0e7ff !important; }',
        'desc': 'Xizmat kartochkalariga chegara qo\'shish',
    },
    {
        'title': 'Hero balandligi',
        'tag': 'hero',
        'code': '.bk-hero { padding: 6rem 0 5rem !important; }',
        'desc': 'Bosh qism balandligini oshirish',
    },
    {
        'title': 'Xizmat kartochkasida icon rang',
        'tag': 'icon',
        'code': '.bk-service-icon { background: #fef3c7 !important; color: #d97706 !important; }',
        'desc': 'Xizmat ikonkalari rangini o\'zgartirish',
    },
    {
        'title': 'Footer matn rangini o\'zgartirish',
        'tag': 'footer',
        'code': '.bk-footer { background: #1e293b !important; color: #94a3b8 !important; }',
        'desc': 'Pastki qism ranglarini o\'zgartirish',
    },
]


@login_required
def css_docs(request):
    business = get_object_or_404(Business, owner=request.user)
    return render(request, 'dashboard/settings/css_docs.html', {
        'business': business,
        'sections': CSS_SECTIONS,
    })


# ─── Upgrade / Payment ────────────────────────────────────────────────────────

@login_required
def upgrade_view(request):
    business = _get_business(request)
    if not business:
        return redirect('business:setup')

    site = SiteSettings.load()
    plans = [
        {'id': 'pro',  'name': 'Pro',  'price_monthly': site.growth_price_monthly,
         'price_yearly': site.growth_price_yearly},
        {'id': 'max',  'name': 'Max',  'price_monthly': site.enterprise_price_monthly,
         'price_yearly': site.enterprise_price_yearly},
    ]

    context = {
        'business': business,
        'plans': plans,
        'site': site,
    }
    return render(request, 'dashboard/upgrade.html', context)


@login_required
def payment_view(request):
    business = _get_business(request)
    if not business:
        return redirect('business:setup')

    plan_id = request.GET.get('plan') or request.POST.get('plan')
    if plan_id not in ('pro', 'max'):
        messages.error(request, 'Noto\'g\'ri tarif tanlandi.')
        return redirect('business:upgrade')

    site = SiteSettings.load()
    plan_name = 'Pro' if plan_id == 'pro' else 'Max'
    amount = site.growth_price_monthly if plan_id == 'pro' else site.enterprise_price_monthly

    if request.method == 'POST':
        receipt = request.FILES.get('receipt')
        note = request.POST.get('note', '')
        if not receipt:
            messages.error(request, 'Chek rasmini yuklang.')
        else:
            Payment.objects.create(
                business=business,
                plan=plan_id,
                amount=amount,
                receipt=receipt,
                note=note,
            )
            messages.success(request, 'To\'lovingiz qabul qilindi. Admin tekshirgandan so\'ng tarifingiz faollashtiriladi.')
            return redirect('dashboard:home')

    context = {
        'business': business,
        'plan_name': plan_name,
        'plan_id': plan_id,
        'amount': amount,
        'card_number': site.payment_card_number,
        'card_holder': site.payment_card_holder,
    }
    return render(request, 'dashboard/payment.html', context)


# ─── Custom Domain ─────────────────────────────────────────────────────────────

import secrets, socket
from django.http import HttpResponseForbidden

@login_required
def custom_domain_settings(request):
    business = get_object_or_404(Business, owner=request.user)
    can_use = business.can_use_custom_domain()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'save_domain':
            if not can_use:
                return HttpResponseForbidden('Faqat pullik tariflarda mavjud')

            domain = request.POST.get('custom_domain', '').strip().lower()
            domain = domain.replace('https://', '').replace('http://', '').replace('/', '')

            if domain:
                if Business.objects.filter(custom_domain=domain).exclude(pk=business.pk).exists():
                    messages.error(request, 'Bu domen allaqachon boshqa biznes tomonidan ishlatilmoqda.')
                else:
                    business.custom_domain = domain
                    business.domain_verified = False
                    business.domain_verify_token = secrets.token_urlsafe(32)
                    business.save(update_fields=['custom_domain', 'domain_verified', 'domain_verify_token'])
                    messages.success(request, 'Domen saqlandi. Iltimos, DNS sozlamalarini qo\'shing va tasdiqlang.')
            else:
                # Clear
                business.custom_domain = None
                business.domain_verified = False
                business.domain_verify_token = ''
                business.save(update_fields=['custom_domain', 'domain_verified', 'domain_verify_token'])
                messages.success(request, 'Domen o\'chirildi.')

            return redirect('business:custom_domain')

        elif action == 'verify':
            if not business.custom_domain or not business.domain_verify_token:
                messages.error(request, 'Avval domen kiriting.')
                return redirect('business:custom_domain')

            verified = _verify_domain_txt(business.custom_domain, business.domain_verify_token)
            if verified:
                business.domain_verified = True
                business.save(update_fields=['domain_verified'])
                messages.success(request, 'Domen muvaffaqiyatli tasdiqlandi! ✅')
            else:
                messages.error(request, 'TXT record topilmadi. DNS sozlamalari tarqalishini kuting va qayta urinib ko\'ring.')

            return redirect('business:custom_domain')

    return render(request, 'dashboard/settings/custom_domain.html', {
        'business': business,
        'can_use': can_use,
    })


def _verify_domain_txt(domain, token):
    try:
        import dns.resolver
        answers = dns.resolver.resolve(domain, 'TXT', lifetime=10)
        for rdata in answers:
            txt = b''.join(rdata.strings).decode('utf-8') if isinstance(rdata.strings, list) else str(rdata)
            if token in txt:
                return True
    except Exception:
        pass
    return False
