import json
import logging
from datetime import datetime

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext as _

from .models import Notification
from business.models import Business

logger = logging.getLogger(__name__)


# ─── Upcoming‑appointments inline button definition ───────────────────────────

_UPCOMING_BTN = [[{'text': '📋 Bugungi qabullar', 'callback_data': 'upcoming_appointments'}]]


# ─── Dashboard: Notification Popup (last 5 for bell dropdown) ─────────────────

@login_required
def notification_popup(request):
    try:
        business = request.user.business
    except Business.DoesNotExist:
        return JsonResponse({'notifications': [], 'unread_count': 0})

    qs = business.notifications.all()[:5]
    unread = business.notifications.filter(is_read=False).count()

    data = []
    for n in qs:
        icon = 'calendar-plus' if n.notification_type == 'booking' else 'info-circle'
        color = '#6366f1' if n.notification_type == 'booking' else '#6b7280'

        url = None
        if n.related_appointment_id:
            url = f'/dashboard/appointments/{n.related_appointment_id}/edit/'

        data.append({
            'id': n.pk,
            'title': n.title,
            'message': n.message[:80] + '…' if len(n.message) > 80 else n.message,
            'type': n.notification_type,
            'icon': icon,
            'color': color,
            'is_read': n.is_read,
            'time_ago': n.created_at.isoformat(),
            'time_display': _timesince(n.created_at),
            'url': url,
        })

    return JsonResponse({'notifications': data, 'unread_count': unread})


def _timesince(dt):
    from django.utils import timezone
    from datetime import timedelta
    now = timezone.now()
    diff = now - dt
    if diff < timedelta(minutes=1):
        return _('Hozir')
    if diff < timedelta(hours=1):
        m = int(diff.total_seconds() / 60)
        return _(f'{m} daqiqa oldin')
    if diff < timedelta(days=1):
        h = int(diff.total_seconds() / 3600)
        return _(f'{h} soat oldin')
    if diff < timedelta(days=7):
        d = diff.days
        return _(f'{d} kun oldin')
    return dt.strftime('%d.%m.%Y')


# ─── Dashboard: Full Notification List ────────────────────────────────────────

@login_required
def notification_list(request):
    business = get_object_or_404(Business, owner=request.user)
    notifications = business.notifications.all()
    return render(request, 'dashboard/notifications/list.html', {
        'business': business,
        'notifications': notifications,
    })


# ─── Mark single notification as read ─────────────────────────────────────────

@login_required
@require_POST
def mark_read(request, pk):
    n = get_object_or_404(Notification, pk=pk, business__owner=request.user)
    n.is_read = True
    n.save(update_fields=['is_read'])
    return JsonResponse({'ok': True})


# ─── Mark all as read ─────────────────────────────────────────────────────────

@login_required
@require_POST
def mark_all_read(request):
    try:
        request.user.business.notifications.filter(is_read=False).update(is_read=True)
    except Business.DoesNotExist:
        pass
    return JsonResponse({'ok': True})


# ─── Unread count (for sidebar badge) ─────────────────────────────────────────

@login_required
def unread_count(request):
    try:
        count = request.user.business.notifications.filter(is_read=False).count()
    except Business.DoesNotExist:
        count = 0
    return JsonResponse({'count': count})


# ─── Telegram Bot Helpers ──────────────────────────────────────────────────────

def _build_upcoming_message(business):
    """
    Build a formatted list of appointments from now until end of today.
    Returns (text, count) — count = number of upcoming appointments.
    """
    from appointments.models import Appointment

    now_local = timezone.localtime(timezone.now())
    today = now_local.date()
    current_time = now_local.time()

    appointments = (
        Appointment.objects
        .filter(business=business, date=today, time__gte=current_time)
        .exclude(status=Appointment.STATUS_CANCELLED)
        .select_related('customer', 'service', 'employee')
        .order_by('time')
    )

    date_str = today.strftime('%d.%m.%Y')
    time_str = now_local.strftime('%H:%M')

    if not appointments.exists():
        return (
            f"📋 <b>Bugungi qo'lgan qabullar ({date_str})</b>\n\n"
            f"🕒 Soat {time_str} dan keyingi qabullar yo'q.\n"
            f"<i>Barcha qabullar yakunlangan yoki hech narsa rejalashtirilmagan.</i>"
        ), 0

    lines = [
        f"📋 <b>Bugungi qo'lgan qabullar ({date_str})</b>",
        f"<i>Soat {time_str} dan boshlab:</i>\n",
    ]

    for idx, appt in enumerate(appointments, 1):
        appt_time = appt.time.strftime('%H:%M')
        customer_name = appt.customer.full_name if appt.customer else "Noma'lum"
        service_name = appt.service.name if appt.service else 'Xizmat belgilanmagan'
        emp_name = appt.employee.name if appt.employee else '—'

        lines.append(
            f"{idx}. 🕒 <b>{appt_time}</b> | 👤 {customer_name}\n"
            f"   💼 {service_name}  👨‍⚕️ {emp_name}"
        )

    count = appointments.count()
    lines.append(f"\n━━━━━━━━━━━━━━━\nJami: <b>{count}</b> ta qabul qoldi")
    return '\n'.join(lines), count


def _send_upcoming_to_chat(chat_id: str):
    """Find the business for this chat_id, build message and send it with the button."""
    from .utils import send_with_inline_keyboard, send_telegram_message

    try:
        business = Business.objects.get(telegram_chat_id=chat_id)
    except Business.DoesNotExist:
        send_telegram_message(
            chat_id,
            '❌ Ushbu chat hech qanday biznesga ulanmagan.\n'
            'Dashboard → Sozlamalar → Telegram orqali ulaning.',
        )
        return

    text, _ = _build_upcoming_message(business)
    send_with_inline_keyboard(chat_id, text, _UPCOMING_BTN)


# ─── Telegram Webhook ─────────────────────────────────────────────────────────

@csrf_exempt
def telegram_webhook(request, token):
    if token != settings.TELEGRAM_BOT_TOKEN:
        logger.warning('Telegram webhook: invalid token received')
        return HttpResponse(status=403)

    if request.method != 'POST':
        return HttpResponse(status=405)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'ok': False, 'error': _('Invalid JSON')}, status=400)

    logger.debug(f'[Telegram webhook] Update: {data}')

    # ── 1. Inline keyboard button pressed ─────────────────────────────────────
    callback_query = data.get('callback_query', {})
    if callback_query:
        from .utils import answer_callback_query

        cb_id      = callback_query.get('id', '')
        cb_data    = callback_query.get('data', '')
        cb_chat_id = str(callback_query.get('message', {}).get('chat', {}).get('id', ''))

        if cb_data == 'upcoming_appointments' and cb_chat_id:
            answer_callback_query(cb_id)           # dismiss loading spinner immediately
            _send_upcoming_to_chat(cb_chat_id)

        return JsonResponse({'ok': True})

    # ── 2. Regular text message / command ─────────────────────────────────────
    message   = data.get('message', {})
    chat      = message.get('chat', {})
    chat_id   = str(chat.get('id', ''))
    text      = message.get('text', '').strip()

    if not chat_id or not text:
        return JsonResponse({'ok': True})

    from .utils import send_telegram_message, send_with_inline_keyboard

    # /start — connect business or welcome
    if text.startswith('/start'):
        parts = text.split(maxsplit=1)
        connect_token = parts[1].strip() if len(parts) > 1 else None

        if connect_token:
            try:
                business = Business.objects.get(telegram_connect_token=connect_token)
                business.telegram_chat_id = chat_id
                business.telegram_notifications_enabled = True
                business.telegram_connect_token = ''
                business.save(update_fields=[
                    'telegram_chat_id',
                    'telegram_notifications_enabled',
                    'telegram_connect_token',
                ])
                logger.info(f'[Telegram] Business "{business.name}" connected to chat_id={chat_id}')
                send_with_inline_keyboard(
                    chat_id,
                    f'✅ <b>{business.name}</b> muvaffaqiyatli ulandi!\n\n'
                    f'Yangi qabullar haqida xabar olasiz. 📲\n'
                    f'Quyidagi tugma orqali bugungi qolgan qabullarni ko\'ring:',
                    _UPCOMING_BTN,
                )
            except Business.DoesNotExist:
                logger.warning(f'[Telegram] Invalid connect_token: {connect_token}')
                send_telegram_message(
                    chat_id,
                    '❌ <b>Havola yaroqsiz yoki muddati o\'tgan.</b>\n\n'
                    'Dashboard → Sozlamalar → Telegram orqali yangi havola oling.',
                )
        else:
            send_with_inline_keyboard(
                chat_id,
                '👋 <b>BookFlow botiga xush kelibsiz!</b>\n\n'
                'Biznesingizni ulash uchun:\n'
                'Dashboard → Sozlamalar → Telegram xabarnomalar → '
                '<b>"Ulanish havolasini yaratish"</b> tugmasini bosing.',
                _UPCOMING_BTN,
            )

    # /stop — disable notifications
    elif text == '/stop':
        try:
            business = Business.objects.get(telegram_chat_id=chat_id)
            business.telegram_notifications_enabled = False
            business.save(update_fields=['telegram_notifications_enabled'])
            send_telegram_message(
                chat_id,
                f'🔕 <b>{business.name}</b> uchun xabarnomalar to\'xtatildi.\n'
                f'Dashboard orqali qayta yoqishingiz mumkin.',
            )
        except Business.DoesNotExist:
            pass

    # /qabullar — show upcoming appointments now
    elif text in ('/qabullar', '/appointments'):
        _send_upcoming_to_chat(chat_id)

    # /help — available commands
    elif text == '/help':
        send_with_inline_keyboard(
            chat_id,
            '📖 <b>Mavjud buyruqlar:</b>\n\n'
            '/qabullar — bugungi qolgan qabullar ro\'yxati\n'
            '/stop — xabarnomalarni to\'xtatish\n'
            '/help — yordam\n\n'
            'Yoki quyidagi tugmadan foydalaning:',
            _UPCOMING_BTN,
        )

    return JsonResponse({'ok': True})
