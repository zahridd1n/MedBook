import json
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings

from .models import Notification
from business.models import Business

logger = logging.getLogger(__name__)


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
        return 'Hozir'
    if diff < timedelta(hours=1):
        m = int(diff.total_seconds() / 60)
        return f'{m} daqiqa oldin'
    if diff < timedelta(days=1):
        h = int(diff.total_seconds() / 3600)
        return f'{h} soat oldin'
    if diff < timedelta(days=7):
        d = diff.days
        return f'{d} kun oldin'
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


# ─── Telegram Webhook ─────────────────────────────────────────────────────────

@csrf_exempt
def telegram_webhook(request, token):
    if token != settings.TELEGRAM_BOT_TOKEN:
        logger.warning(f'Telegram webhook: invalid token received')
        return HttpResponse(status=403)

    if request.method != 'POST':
        return HttpResponse(status=405)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)

    logger.debug(f'[Telegram webhook] Update: {data}')

    message = data.get('message', {})
    chat = message.get('chat', {})
    chat_id = str(chat.get('id', ''))
    chat_name = chat.get('first_name', '') or chat.get('title', '')
    text = message.get('text', '').strip()

    if not chat_id or not text:
        return JsonResponse({'ok': True})

    if text.startswith('/start'):
        parts = text.split(maxsplit=1)
        connect_token = parts[1].strip() if len(parts) > 1 else None

        from .utils import send_telegram_message

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
                send_telegram_message(
                    chat_id,
                    f'✅ <b>Successfully Connected!</b>\n\n'
                    f'Your business <b>{business.name}</b> is now linked to this chat.\n\n'
                    f'You will receive a notification here every time a new booking is made.\n\n'
                    f'<i>You can manage notifications from your dashboard.</i>'
                )
            except Business.DoesNotExist:
                logger.warning(f'[Telegram] Invalid connect_token: {connect_token}')
                send_telegram_message(
                    chat_id,
                    '❌ <b>Invalid or expired link.</b>\n\n'
                    'Please go back to your dashboard and generate a new connection link.'
                )
        else:
            from .utils import send_telegram_message
            send_telegram_message(
                chat_id,
                '👋 <b>Welcome to BookFlow Bot!</b>\n\n'
                'To connect your business and receive booking notifications, '
                'go to your dashboard → Settings → Telegram Notifications '
                'and click <b>"Generate Connection Link"</b>.'
            )

    elif text == '/stop':
        from .utils import send_telegram_message
        try:
            business = Business.objects.get(telegram_chat_id=chat_id)
            business.telegram_notifications_enabled = False
            business.save(update_fields=['telegram_notifications_enabled'])
            send_telegram_message(
                chat_id,
                f'🔕 Notifications for <b>{business.name}</b> have been paused.\n'
                f'You can re-enable them from your dashboard.'
            )
        except Business.DoesNotExist:
            pass

    return JsonResponse({'ok': True})
