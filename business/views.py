import logging
import secrets
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.utils.translation import gettext as _

from .models import Business, WorkingHours, FAQ, Payment
from .forms import BusinessSetupForm, FAQForm, BrandingForm, SEOForm
from superadmin.models import SiteSettings

logger = logging.getLogger(__name__)


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
            messages.success(request, _('Business settings saved.'))
            return redirect('dashboard:home')
    else:
        form = BusinessSetupForm(instance=business)
    from .forms import UZBEKISTAN_CITIES
    return render(request, 'dashboard/settings/business.html', {
        'form': form,
        'business': business,
        'uzbekistan_cities': UZBEKISTAN_CITIES,
    })


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
        messages.success(request, _('Working hours saved.'))
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
            messages.success(request, _('FAQ added.'))
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
            messages.success(request, _('FAQ updated.'))
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
        messages.success(request, _('FAQ deleted.'))
    return redirect('business:faq_list')


# ─── Branding / Page Customization ────────────────────────────────────────────

@login_required
def branding_settings(request):
    business = get_object_or_404(Business, owner=request.user)
    can_use = business.can_use_branding()

    if request.method == 'POST':
        if not can_use:
            messages.error(request, _('Sahifa dizaynini sozlash faqat Pro va Max tariflarida mavjud.'))
            return redirect('business:branding')

        # Handle remove banner separately (before form saves old value back)
        if request.POST.get('remove_banner') and not request.FILES.get('banner_image'):
            if business.banner_image:
                business.banner_image.delete(save=False)
            business.banner_image = None
            business.save(update_fields=['banner_image'])
            messages.success(request, _('Banner rasmi o\'chirildi.'))
            return redirect('business:branding')

        form = BrandingForm(request.POST, request.FILES, instance=business)
        if form.is_valid():
            form.save()
            messages.success(request, _('Dizayn sozlamalari saqlandi.'))
            return redirect('business:branding')
        else:
            for field, errors in form.errors.items():
                for err in errors:
                    messages.error(request, _(f'{field}: {err}'))
    else:
        form = BrandingForm(instance=business)

    return render(request, 'dashboard/settings/branding.html', {
        'business': business,
        'form': form,
        'is_paid': can_use,
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

    can_use_tg = business.can_use_telegram()

    if request.method == 'POST':
        if not can_use_tg:
            messages.error(request, _('Telegram xabarnomalari faqat Pro va Max tariflarida mavjud.'))
            return redirect('business:telegram')

        action = request.POST.get('action')

        if action == 'generate_link':
            if not bot_token_set:
                messages.error(request, _('TELEGRAM_BOT_TOKEN is not set in your .env file.'))
            elif not bot_username:
                messages.error(request, _('TELEGRAM_BOT_USERNAME is not set in your .env file.'))
            else:
                business.generate_connect_token()
                messages.success(request, _('Connection link generated. Click it to open Telegram.'))

        elif action == 'disconnect':
            business.telegram_chat_id = ''
            business.telegram_notifications_enabled = False
            business.telegram_connect_token = ''
            business.save(update_fields=[
                'telegram_chat_id', 'telegram_notifications_enabled', 'telegram_connect_token'
            ])
            messages.success(request, _('Telegram disconnected successfully.'))

        elif action == 'toggle':
            if not business.telegram_chat_id:
                messages.error(request, _('Connect Telegram first before enabling notifications.'))
            else:
                business.telegram_notifications_enabled = not business.telegram_notifications_enabled
                business.save(update_fields=['telegram_notifications_enabled'])
                state = 'enabled' if business.telegram_notifications_enabled else 'paused'
                messages.success(request, _(f'Telegram notifications {state}.'))

        elif action == 'test':
            if not business.telegram_chat_id:
                messages.error(request, _('Telegram is not connected yet.'))
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
                    messages.success(request, _('✅ Test message sent! Check your Telegram.'))
                else:
                    messages.error(request, _('❌ Failed to send. Check that TELEGRAM_BOT_TOKEN is correct.'))

        elif action == 'set_webhook':
            from notifications.utils import set_telegram_webhook
            result = set_telegram_webhook(settings.SITE_URL)
            if result.get('ok'):
                messages.success(request, _(f'Webhook set to {settings.SITE_URL}/telegram/webhook/…'))
            else:
                messages.error(request, _(f'Webhook error: {result.get("description", result)}'))

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
        'can_use_tg': can_use_tg,
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

    from superadmin.models import PricingPlan
    plans = PricingPlan.objects.filter(is_active=True).order_by('order').prefetch_related('features')

    context = {
        'business': business,
        'plans': plans,
        'site': SiteSettings.load(),
    }
    return render(request, 'dashboard/upgrade.html', context)


@login_required
def payment_view(request):
    business = _get_business(request)
    if not business:
        return redirect('business:setup')

    plan_id = request.GET.get('plan') or request.POST.get('plan')
    duration = request.GET.get('duration', '3months') or request.POST.get('duration', '3months')
    if duration not in ('3months', 'yearly'):
        duration = '3months'

    from superadmin.models import PricingPlan
    plan = PricingPlan.objects.filter(slug=plan_id).first()
    if not plan or plan.slug == 'free':
        messages.error(request, _('Noto\'g\'ri tarif tanlandi.'))
        return redirect('business:upgrade')

    site = SiteSettings.load()
    plan_name = plan.name
    # Duration bo'yicha narx
    if duration == 'yearly':
        amount = plan.price_yearly
        duration_label = '1 yillik (365 kun)'
    else:
        amount = plan.price_3months
        duration_label = '3 oylik (90 kun)'

    if request.method == 'POST':
        receipt = request.FILES.get('receipt')
        note = request.POST.get('note', '')
        post_duration = request.POST.get('duration', duration)
        if post_duration not in ('3months', 'yearly'):
            post_duration = '3months'
        if not receipt:
            messages.error(request, _('Chek rasmini yuklang.'))
        else:
            # POST dan qayta narx hisoblash
            if post_duration == 'yearly':
                pay_amount = plan.price_yearly
            else:
                pay_amount = plan.price_3months
            Payment.objects.create(
                business=business,
                plan=plan_id,
                duration=post_duration,
                amount=pay_amount,
                receipt=receipt,
                note=note,
            )
            messages.success(request, _('To\'lovingiz qabul qilindi. Admin tekshirgandan so\'ng tarifingiz faollashtiriladi.'))
            return redirect('dashboard:home')

    context = {
        'business': business,
        'plan_name': plan_name,
        'plan_id': plan_id,
        'duration': duration,
        'duration_label': duration_label,
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
                return HttpResponseForbidden(_('Faqat pullik tariflarda mavjud'))

            domain = request.POST.get('custom_domain', '').strip().lower()
            domain = domain.replace('https://', '').replace('http://', '').replace('/', '')

            if domain:
                if Business.objects.filter(custom_domain=domain).exclude(pk=business.pk).exists():
                    messages.error(request, _('Bu domen allaqachon boshqa biznes tomonidan ishlatilmoqda.'))
                else:
                    business.custom_domain = domain
                    business.domain_verified = False
                    business.domain_verify_token = secrets.token_urlsafe(32)
                    business.save(update_fields=['custom_domain', 'domain_verified', 'domain_verify_token'])
                    messages.success(request, _('Domen saqlandi. Iltimos, DNS sozlamalarini qo\'shing va tasdiqlang.'))
            else:
                # Clear
                business.custom_domain = None
                business.domain_verified = False
                business.domain_verify_token = ''
                business.save(update_fields=['custom_domain', 'domain_verified', 'domain_verify_token'])
                messages.success(request, _('Domen o\'chirildi.'))

            return redirect('business:custom_domain')

        elif action == 'verify':
            if not business.custom_domain or not business.domain_verify_token:
                messages.error(request, _('Avval domen kiriting.'))
                return redirect('business:custom_domain')

            verified = _verify_domain_txt(business.custom_domain, business.domain_verify_token)
            if verified:
                business.domain_verified = True
                business.save(update_fields=['domain_verified'])
                messages.success(request, _('Domen muvaffaqiyatli tasdiqlandi! ✅'))
            else:
                messages.error(request, _('TXT record topilmadi. DNS sozlamalari tarqalishini kuting va qayta urinib ko\'ring.'))

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


# ─── Google Calendar ──────────────────────────────────────────────────────────

@login_required
def google_calendar_settings(request):
    business = get_object_or_404(Business, owner=request.user)
    can_use = business.can_use_google_calendar()
    has_creds = bool(business.google_credentials)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'disconnect':
            business.google_credentials = None
            business.google_calendar_sync_enabled = False
            business.save(update_fields=['google_credentials', 'google_calendar_sync_enabled'])
            messages.success(request, _('Google Calendar uzildi.'))
            return redirect('business:google_calendar')

        elif action == 'toggle_sync':
            if not has_creds:
                messages.error(request, _('Avval Google Calendar ga ulaning.'))
            else:
                business.google_calendar_sync_enabled = not business.google_calendar_sync_enabled
                business.save(update_fields=['google_calendar_sync_enabled'])
                state = 'yoqildi' if business.google_calendar_sync_enabled else 'o\'chirildi'
                messages.success(request, _(f'Google Calendar sinxronizatsiya {state}.'))

        return redirect('business:google_calendar')

    connect_url = None
    if can_use and settings.GOOGLE_OAUTH_CLIENT_CONFIG:
        from .google_calendar import get_flow
        try:
            flow = get_flow(request, business)
            connect_url, _state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent',
            )
        except Exception as e:
            logger.error(f'Google Calendar auth URL error: {e}')

    return render(request, 'dashboard/settings/google_calendar.html', {
        'business': business,
        'can_use': can_use,
        'has_creds': has_creds,
        'connect_url': connect_url,
    })


@login_required
def google_calendar_callback(request):
    business = get_object_or_404(Business, owner=request.user)
    error = request.GET.get('error')
    if error:
        messages.error(request, _(f'Google Calendar ulanish bekor qilindi yoki xatolik: {error}'))
        return redirect('business:google_calendar')

    code = request.GET.get('code')
    if not code:
        messages.error(request, _('Google Calendar ulanish uchun kod topilmadi.'))
        return redirect('business:google_calendar')

    if not settings.GOOGLE_OAUTH_CLIENT_CONFIG:
        messages.error(request, _('Google OAuth sozlanmagan.'))
        return redirect('business:google_calendar')

    from .google_calendar import get_flow
    try:
        flow = get_flow(request, business)
        flow.fetch_token(code=code)
        business.google_credentials = flow.credentials.to_json()
        business.google_calendar_sync_enabled = True
        business.save(update_fields=['google_credentials', 'google_calendar_sync_enabled'])
        messages.success(request, _('Google Calendar muvaffaqiyatli ulandi! ✅'))
    except Exception as e:
        logger.error(f'Google Calendar callback error: {e}')
        messages.error(request, _(f'Google Calendar ulanishda xatolik: {e}'))

    return redirect('business:google_calendar')


# ─── Analytics ────────────────────────────────────────────────────────────────

@login_required
def analytics(request):
    business = get_object_or_404(Business, owner=request.user)
    is_paid = business.can_use_analytics()

    from django.db.models import Count, Q, Sum
    from django.db.models.functions import TruncMonth
    from appointments.models import Appointment
    from customers.models import Customer
    from services.models import Service
    from employees.models import Employee
    import calendar

    now = timezone.now()
    this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # ── Monthly appointments (last 12 months) ──
    months_data = []
    for i in range(11, -1, -1):
        m = now.month - i
        y = now.year
        while m < 1:
            m += 12
            y -= 1
        total = Appointment.objects.filter(
            business=business, date__year=y, date__month=m,
        ).exclude(status='cancelled').count()
        months_data.append({
            'label': f'{y}-{m:02d}',
            'total': total,
            'month_name': f'{calendar.month_abbr[m]} {y}',
        })

    # ── Monthly revenue (last 12 months) ──
    revenue_data = []
    for i in range(11, -1, -1):
        m = now.month - i
        y = now.year
        while m < 1:
            m += 12
            y -= 1
        apps = Appointment.objects.filter(
            business=business, date__year=y, date__month=m,
            service__isnull=False,
        ).exclude(status='cancelled').select_related('service')
        total_rev = sum(a.service.price for a in apps if a.service)
        revenue_data.append({
            'label': f'{y}-{m:02d}',
            'total': total_rev,
            'month_name': f'{calendar.month_abbr[m]} {y}',
        })

    # ── Top services (by count + revenue) ──
    top_services = (
        Service.objects.filter(business=business)
        .annotate(count=Count('appointments', filter=~Q(appointments__status='cancelled')))
        .order_by('-count')[:5]
    )
    for s in top_services:
        s.revenue = sum(
            a.service.price for a in Appointment.objects.filter(
                business=business, service=s
            ).exclude(status='cancelled') if a.service
        )

    # ── Customer growth (monthly for 12 months) ──
    customer_growth = []
    for i in range(11, -1, -1):
        m = now.month - i
        y = now.year
        while m < 1:
            m += 12
            y -= 1
        cnt = Customer.objects.filter(
            business=business,
            created_at__year=y, created_at__month=m,
        ).count()
        customer_growth.append({
            'label': f'{y}-{m:02d}',
            'total': cnt,
            'month_name': f'{calendar.month_abbr[m]} {y}',
        })

    # ── Day-of-week distribution ──
    weekday_names = ['Dushanba', 'Seshanba', 'Chorshanba', 'Payshanba', 'Juma', 'Shanba', 'Yakshanba']
    weekday_data = [0] * 7
    for appt in Appointment.objects.filter(business=business).exclude(status='cancelled').values_list('date', flat=True):
        weekday_data[appt.weekday()] += 1

    # ── Customer stats ──
    total_customers = Customer.objects.filter(business=business).count()
    new_customers_this_month = Customer.objects.filter(
        business=business, created_at__gte=this_month_start
    ).count()

    # ── Employee performance ──
    top_employees = (
        Employee.objects.filter(business=business)
        .annotate(count=Count('appointments', filter=~Q(appointments__status='cancelled')))
        .order_by('-count')[:5]
    )

    # ── Status breakdown ──
    status_counts = {}
    for status_key, status_label in Appointment.STATUS_CHOICES:
        cnt = Appointment.objects.filter(business=business, status=status_key).count()
        if cnt:
            status_counts[status_label] = cnt

    total_appointments = Appointment.objects.filter(business=business).exclude(status='cancelled').count()
    this_month_appointments = Appointment.objects.filter(
        business=business, date__gte=this_month_start.date(),
    ).exclude(status='cancelled').count()

    cancelled_count = Appointment.objects.filter(business=business, status='cancelled').count()
    total_all = total_appointments + cancelled_count
    cancellation_rate = round((cancelled_count / total_all * 100) if total_all else 0, 1)

    avg_per_day = round(total_appointments / 30, 1) if total_appointments else 0

    # ── Conversion: completed vs cancelled ──
    completed_count = Appointment.objects.filter(business=business, status='completed').count()

    context = {
        'business': business,
        'is_paid': is_paid,
        'months_data': months_data,
        'revenue_data': revenue_data,
        'top_services': top_services,
        'total_customers': total_customers,
        'new_customers_this_month': new_customers_this_month,
        'customer_growth': customer_growth,
        'weekday_data': weekday_data,
        'weekday_names': weekday_names,
        'top_employees': top_employees,
        'status_counts': status_counts,
        'total_appointments': total_appointments,
        'this_month_appointments': this_month_appointments,
        'cancelled_count': cancelled_count,
        'cancellation_rate': cancellation_rate,
        'completed_count': completed_count,
        'avg_per_day': avg_per_day,
    }
    return render(request, 'dashboard/analytics.html', context)


# ─── White Label ──────────────────────────────────────────────────────────────

@login_required
def white_label_settings(request):
    business = get_object_or_404(Business, owner=request.user)
    can_use = business.can_use_white_label()

    if request.method == 'POST':
        if not can_use:
            messages.error(request, _('White Label faqat Max tarifida mavjud.'))
            return redirect('business:white_label')
        enabled = request.POST.get('white_label_enabled') == 'on'
        business.white_label_enabled = enabled
        business.save(update_fields=['white_label_enabled'])
        if enabled:
            messages.success(request, _('White Label yoqildi — BookFlow brendi yashirildi.'))
        else:
            messages.success(request, _('White Label o\'chirildi.'))
        return redirect('business:white_label')

    return render(request, 'dashboard/settings/white_label.html', {
        'business': business,
        'can_use': can_use,
    })


# ─── API & Webhook ──────────────────────────────────────────────────────────

@login_required
def api_settings(request):
    business = get_object_or_404(Business, owner=request.user)
    can_use = business.can_use_api()

    if request.method == 'POST':
        if not can_use:
            messages.error(request, _('API va Webhook faqat Max tarifida mavjud.'))
            return redirect('business:api')

        action = request.POST.get('action')

        if action == 'regenerate_key':
            business.api_key = secrets.token_hex(32)
            business.api_key_created = timezone.now()
            business.save(update_fields=['api_key', 'api_key_created'])
            messages.success(request, _('API kaliti muvaffaqiyatli yangilandi.'))

        elif action == 'save_webhook':
            webhook_url = request.POST.get('webhook_url', '').strip()
            business.webhook_url = webhook_url
            business.save(update_fields=['webhook_url'])
            if webhook_url:
                messages.success(request, _('Webhook URL saqlandi. Yangi qabullar avtomatik yuboriladi.'))
            else:
                messages.success(request, _('Webhook URL o\'chirildi.'))

        elif action == 'test_webhook':
            import json
            from urllib.request import Request, urlopen
            from urllib.error import URLError
            payload = {'event': 'test', 'message': 'This is a test webhook from BookFlow'}
            try:
                req = Request(
                    business.webhook_url,
                    data=json.dumps(payload).encode('utf-8'),
                    headers={'Content-Type': 'application/json', 'X-API-Key': business.api_key},
                    method='POST',
                )
                urlopen(req, timeout=5)
                messages.success(request, _('Test webhook muvaffaqiyatli yuborildi ✅'))
            except URLError as e:
                messages.error(request, _(f'Webhook test xatosi: {e.reason}'))
            except Exception as e:
                messages.error(request, _(f'Webhook test xatosi: {e}'))

        return redirect('business:api')

    if not business.api_key:
        business.api_key = secrets.token_hex(32)
        business.api_key_created = timezone.now()
        business.save(update_fields=['api_key', 'api_key_created'])

    # API activity count (simple stats)
    try:
        from django.core.cache import cache
        api_calls_today = cache.get(f'api_calls_{business.id}', 0)
    except Exception:
        api_calls_today = 0

    return render(request, 'dashboard/settings/api.html', {
        'business': business,
        'can_use': can_use,
        'api_calls_today': api_calls_today,
    })


@login_required
def api_docs(request):
    business = get_object_or_404(Business, owner=request.user)
    can_use = business.can_use_api()

    base_url = request.build_absolute_uri('/dashboard/api/')
    api_key = business.api_key if can_use else 'YOUR_API_KEY'

    return render(request, 'dashboard/settings/api_docs.html', {
        'business': business,
        'can_use': can_use,
        'base_url': base_url,
        'api_key': api_key,
    })


# ─── API Endpoints ──────────────────────────────────────────────────────────

def _api_auth(request, business):
    """Verify API access and key. Returns JsonResponse on failure, None on success."""
    if not business.can_use_api():
        return JsonResponse({'error': _('API ruxsati yo\'q. Max tarifini talab qiladi.')}, status=403)
    api_key = request.GET.get('api_key') or request.headers.get('X-API-Key') or request.POST.get('api_key')
    if not api_key or api_key != business.api_key:
        return JsonResponse({'error': _('Noto\'g\'ri API kaliti. X-API-Key header yoki ?api_key= parametrini tekshiring.')}, status=401)
    # Track API call count (cache may be unavailable)
    try:
        from django.core.cache import cache
        today_key = f'api_calls_{business.id}'
        cache.set(today_key, cache.get(today_key, 0) + 1, 86400)
    except Exception:
        pass
    return None


@login_required
def api_appointments(request):
    business = get_object_or_404(Business, owner=request.user)
    err = _api_auth(request, business)
    if err: return err

    from appointments.models import Appointment
    from django.utils import timezone

    if request.method == 'GET':
        # Optional filters
        status_filter = request.GET.get('status', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        limit = int(request.GET.get('limit', '100'))

        qs = Appointment.objects.filter(business=business).select_related('customer', 'service', 'employee')
        if status_filter:
            qs = qs.filter(status=status_filter)
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)
        if limit > 500:
            limit = 500

        data = []
        for a in qs.order_by('-date', '-time')[:limit]:
            data.append({
                'id': a.id,
                'date': str(a.date),
                'time': str(a.time),
                'status': a.status,
                'customer_name': a.customer.full_name if a.customer else '',
                'customer_phone': a.customer.phone if a.customer else '',
                'service_name': a.service.name if a.service else '',
                'service_id': a.service.id if a.service else None,
                'employee_name': a.employee.name if a.employee else '',
                'employee_id': a.employee.id if a.employee else None,
                'price': a.service.price if a.service else 0,
                'duration': a.service.duration if a.service else None,
                'notes': a.notes or '',
                'created_at': a.created_at.isoformat() if a.created_at else '',
            })
        return JsonResponse({'ok': True, 'appointments': data, 'total': len(data)})

    elif request.method == 'POST':
        import json
        try:
            body = json.loads(request.body) if request.body else request.POST.dict()
        except json.JSONDecodeError:
            return JsonResponse({'ok': False, 'error': _('JSON formatida yuboring')}, status=400)

        from customers.models import Customer
        from services.models import Service
        from employees.models import Employee

        customer_name = body.get('customer_name', '').strip()
        customer_phone = body.get('customer_phone', '').strip()
        service_id = body.get('service_id')
        employee_id = body.get('employee_id')
        date_str = body.get('date', '')
        time_str = body.get('time', '')

        if not all([customer_name, customer_phone, service_id, date_str, time_str]):
            return JsonResponse({'ok': False, 'error': _('Majburiy maydonlar: customer_name, customer_phone, service_id, date, time')}, status=400)

        try:
            service = Service.objects.get(id=service_id, business=business)
        except Service.DoesNotExist:
            return JsonResponse({'ok': False, 'error': _('Xizmat topilmadi')}, status=404)

        employee = None
        if employee_id:
            try:
                employee = Employee.objects.get(id=employee_id, business=business)
            except Employee.DoesNotExist:
                return JsonResponse({'ok': False, 'error': _('Xodim topilmadi')}, status=404)

        customer, _ = Customer.objects.get_or_create(
            business=business, phone=customer_phone,
            defaults={'full_name': customer_name},
        )

        appointment = Appointment.objects.create(
            business=business,
            customer=customer,
            service=service,
            employee=employee,
            date=date_str,
            time=time_str,
            notes=body.get('notes', ''),
            status=body.get('status', 'pending'),
        )

        return JsonResponse({'ok': True, 'appointment': {'id': appointment.id, 'status': appointment.status}}, status=201)


@login_required
def api_appointment_detail(request, pk):
    business = get_object_or_404(Business, owner=request.user)
    err = _api_auth(request, business)
    if err: return err

    from appointments.models import Appointment
    try:
        a = Appointment.objects.get(id=pk, business=business)
    except Appointment.DoesNotExist:
        return JsonResponse({'ok': False, 'error': _('Qabul topilmadi')}, status=404)

    if request.method == 'DELETE':
        if a.status == 'cancelled':
            return JsonResponse({'ok': False, 'error': _('Qabul allaqachon bekor qilingan')}, status=400)
        a.status = 'cancelled'
        a.save(update_fields=['status'])
        return JsonResponse({'ok': True, 'message': _('Qabul bekor qilindi')})

    data = {
        'id': a.id,
        'date': str(a.date),
        'time': str(a.time),
        'status': a.status,
        'customer_name': a.customer.full_name if a.customer else '',
        'customer_phone': a.customer.phone if a.customer else '',
        'service_name': a.service.name if a.service else '',
        'service_id': a.service.id if a.service else None,
        'employee_name': a.employee.name if a.employee else '',
        'employee_id': a.employee.id if a.employee else None,
        'price': a.service.price if a.service else 0,
        'duration': a.service.duration if a.service else None,
        'notes': a.notes or '',
        'created_at': a.created_at.isoformat() if a.created_at else '',
    }
    return JsonResponse({'ok': True, 'appointment': data})


@login_required
def api_appointments_today(request):
    business = get_object_or_404(Business, owner=request.user)
    err = _api_auth(request, business)
    if err: return err

    from appointments.models import Appointment
    from django.utils import timezone
    today = timezone.localdate()

    qs = Appointment.objects.filter(
        business=business, date=today
    ).select_related('customer', 'service', 'employee').order_by('time')

    data = []
    for a in qs:
        data.append({
            'id': a.id,
            'time': str(a.time),
            'status': a.status,
            'customer_name': a.customer.full_name if a.customer else '',
            'customer_phone': a.customer.phone if a.customer else '',
            'service_name': a.service.name if a.service else '',
            'employee_name': a.employee.name if a.employee else '',
            'price': a.service.price if a.service else 0,
        })
    return JsonResponse({'ok': True, 'date': str(today), 'appointments': data, 'total': len(data)})


@login_required
def api_customers(request):
    business = get_object_or_404(Business, owner=request.user)
    err = _api_auth(request, business)
    if err: return err

    from customers.models import Customer
    search = request.GET.get('search', '')
    limit = int(request.GET.get('limit', '100'))

    qs = Customer.objects.filter(business=business)
    if search:
        qs = qs.filter(full_name__icontains=search) | qs.filter(phone__icontains=search)
    if limit > 500:
        limit = 500

    data = []
    for c in qs.order_by('-created_at')[:limit]:
        data.append({
            'id': c.id,
            'full_name': c.full_name,
            'phone': c.phone,
            'email': c.email or '',
            'total_appointments': c.appointments.count(),
            'created_at': c.created_at.isoformat() if c.created_at else '',
        })
    return JsonResponse({'ok': True, 'customers': data, 'total': len(data)})


@login_required
def api_stats(request):
    business = get_object_or_404(Business, owner=request.user)
    err = _api_auth(request, business)
    if err: return err

    from appointments.models import Appointment
    from customers.models import Customer
    from services.models import Service
    from employees.models import Employee
    from django.utils import timezone
    from django.db.models import Count, Sum, Q

    now = timezone.now()
    this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    total_appointments = Appointment.objects.filter(business=business).count()
    this_month_apps = Appointment.objects.filter(business=business, date__gte=this_month).count()
    completed = Appointment.objects.filter(business=business, status='completed').count()
    cancelled = Appointment.objects.filter(business=business, status='cancelled').count()
    total_customers = Customer.objects.filter(business=business).count()
    total_services = Service.objects.filter(business=business, is_active=True).count()
    total_employees = Employee.objects.filter(business=business, is_active=True).count()

    # Revenue this month
    monthly_apps = Appointment.objects.filter(
        business=business, date__gte=this_month, status='completed'
    ).select_related('service')
    monthly_revenue = sum(a.service.price for a in monthly_apps if a.service) if monthly_apps else 0

    # Today's appointments
    today = timezone.localdate()
    today_count = Appointment.objects.filter(business=business, date=today).count()

    return JsonResponse({
        'ok': True,
        'stats': {
            'total_appointments': total_appointments,
            'this_month_appointments': this_month_apps,
            'completed_appointments': completed,
            'cancelled_appointments': cancelled,
            'total_customers': total_customers,
            'total_services': total_services,
            'total_employees': total_employees,
            'monthly_revenue': monthly_revenue,
            'today_appointments': today_count,
        }
    })


@login_required
def api_services(request):
    business = get_object_or_404(Business, owner=request.user)
    err = _api_auth(request, business)
    if err: return err

    from services.models import Service
    services = Service.objects.filter(business=business, is_active=True)
    data = [{'id': s.id, 'name': s.name, 'price': s.price, 'duration': s.duration, 'description': s.description} for s in services]
    return JsonResponse({'ok': True, 'services': data, 'total': len(data)})


@login_required
def api_employees(request):
    business = get_object_or_404(Business, owner=request.user)
    err = _api_auth(request, business)
    if err: return err

    from employees.models import Employee
    employees = Employee.objects.filter(business=business, is_active=True)
    data = [{'id': e.id, 'name': e.name, 'position': e.position, 'phone': '', 'email': ''} for e in employees]
    return JsonResponse({'ok': True, 'employees': data, 'total': len(data)})


# ─── Link Sharing ────────────────────────────────────────────────────────────

@login_required
@login_required
def seo_settings(request):
    business = get_object_or_404(Business, owner=request.user)
    can_use_advanced = business.can_use_advanced_seo()

    if request.method == 'POST':
        form = SEOForm(request.POST, request.FILES, instance=business)
        if form.is_valid():
            form.save()
            from core.tasks import invalidate_business_seo_cache
            invalidate_business_seo_cache.delay(business.id)
            messages.success(request, _('SEO sozlamalari saqlandi.'))
            return redirect('business:seo')
        else:
            for field, errors in form.errors.items():
                for err in errors:
                    messages.error(request, err)
    else:
        form = SEOForm(instance=business)

    preview_url = request.build_absolute_uri(f'/{business.slug}/')
    return render(request, 'dashboard/settings/seo.html', {
        'business': business,
        'form': form,
        'can_use_advanced': can_use_advanced,
        'preview_url': preview_url,
    })


def link_sharing(request):
    business = get_object_or_404(Business, owner=request.user)
    can_use = business.subscription_plan != 'free'

    from .qrcode_utils import get_business_url
    qr_url = get_business_url(business)

    return render(request, 'dashboard/settings/link_sharing.html', {
        'business': business,
        'can_use': can_use,
        'qr_url': qr_url,
    })


# ─── QR Code Marketing ──────────────────────────────────────────────────────

@login_required
def qr_code_settings(request):
    business = get_object_or_404(Business, owner=request.user)
    can_use = business.subscription_plan != 'free'

    from django.utils import timezone
    from datetime import timedelta
    from django.db.models import Count
    from .models import QRCodeScan

    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)

    this_month_scans = QRCodeScan.objects.filter(
        business=business, scanned_at__gte=thirty_days_ago
    ).count()

    total_scans = QRCodeScan.objects.filter(business=business).count()

    scans_by_day = []
    max_scan_count = 0
    for i in range(29, -1, -1):
        day = (now - timedelta(days=i)).date()
        cnt = QRCodeScan.objects.filter(
            business=business,
            scanned_at__date=day,
        ).count()
        if cnt > max_scan_count:
            max_scan_count = cnt
        scans_by_day.append({'date': day, 'count': cnt})

    if max_scan_count == 0:
        max_scan_count = 1

    public_url = business.custom_domain if (business.custom_domain and business.domain_verified) else None

    from .qrcode_utils import get_business_url, SIZE_PRESETS, generate_qr_svg
    qr_url = get_business_url(business)

    import base64
    svg_buf = generate_qr_svg(business, border=2)
    qr_svg_b64 = base64.b64encode(svg_buf.getvalue()).decode('utf-8')

    # Logo URL for QR center overlay
    logo_url = ''
    if business.logo:
        try:
            logo_url = request.build_absolute_uri(business.logo.url)
        except Exception:
            logo_url = ''

    context = {
        'business': business,
        'can_use': can_use,
        'this_month_scans': this_month_scans,
        'total_scans': total_scans,
        'scans_by_day': scans_by_day,
        'max_scan_count': max_scan_count,
        'qr_url': qr_url,
        'qr_svg_b64': qr_svg_b64,
        'size_presets': SIZE_PRESETS,
        'logo_url': logo_url,
        'primary_color': business.primary_color or '#6366f1',
    }
    return render(request, 'dashboard/settings/qrcode.html', context)


@login_required
def qr_download(request, size='visitka', fmt='png'):
    business = get_object_or_404(Business, owner=request.user)

    from .qrcode_utils import generate_qr_png, generate_qr_svg, SIZE_PRESETS

    preset = SIZE_PRESETS.get(size, SIZE_PRESETS['visitka'])

    if fmt == 'svg':
        buf = generate_qr_svg(business, border=preset['border'])
        response = HttpResponse(buf.getvalue(), content_type='image/svg+xml')
        response['Content-Disposition'] = f'attachment; filename="{business.slug}_qr_{size}.svg"'
    else:
        buf = generate_qr_png(business, box_size=preset['box_size'], border=preset['border'])
        response = HttpResponse(buf.getvalue(), content_type='image/png')
        response['Content-Disposition'] = f'attachment; filename="{business.slug}_qr_{size}.png"'

    return response
