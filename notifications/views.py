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


# ─── Dashboard: Notifications List ───────────────────────────────────────────

@login_required
def notification_list(request):
    business = get_object_or_404(Business, owner=request.user)
    notifications = business.notifications.all()
    # Mark all as read when opening the page
    business.notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'dashboard/notifications/list.html', {
        'business': business,
        'notifications': notifications,
    })


@login_required
def unread_count(request):
    """JSON endpoint polled by the navbar badge every 30 seconds."""
    try:
        count = request.user.business.notifications.filter(is_read=False).count()
    except Business.DoesNotExist:
        count = 0
    return JsonResponse({'count': count})


# ─── Telegram Webhook ─────────────────────────────────────────────────────────

@csrf_exempt
def telegram_webhook(request, token):
    """
    Receive updates from Telegram Bot API.

    Telegram sends POST requests here whenever:
    - Someone sends /start <connect_token> to the bot
    - Other messages (ignored for now)

    Security: we validate the token in the URL against TELEGRAM_BOT_TOKEN.
    """
    # ── Security check ──────────────────────────────────────────────────────
    if token != settings.TELEGRAM_BOT_TOKEN:
        logger.warning(f'Telegram webhook: invalid token received')
        return HttpResponse(status=403)

    if request.method != 'POST':
        return HttpResponse(status=405)

    # ── Parse update ────────────────────────────────────────────────────────
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

    # ── Handle /start command ────────────────────────────────────────────────
    if text.startswith('/start'):
        parts = text.split(maxsplit=1)
        connect_token = parts[1].strip() if len(parts) > 1 else None

        from .utils import send_telegram_message

        if connect_token:
            try:
                business = Business.objects.get(telegram_connect_token=connect_token)

                # Save chat_id and enable notifications
                business.telegram_chat_id = chat_id
                business.telegram_notifications_enabled = True
                business.telegram_connect_token = ''  # one-time use — invalidate
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
            # /start without token — generic welcome
            from .utils import send_telegram_message
            send_telegram_message(
                chat_id,
                '👋 <b>Welcome to BookSaaS Bot!</b>\n\n'
                'To connect your business and receive booking notifications, '
                'go to your dashboard → Settings → Telegram Notifications '
                'and click <b>"Generate Connection Link"</b>.'
            )

    # ── Handle /stop command ─────────────────────────────────────────────────
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
