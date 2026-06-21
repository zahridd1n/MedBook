import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


# ─── Dashboard Notifications ──────────────────────────────────────────────────

def create_notification(business, title, message, notification_type='booking', appointment_id=None):
    """Create an in-dashboard notification for a business."""
    from .models import Notification
    return Notification.objects.create(
        business=business,
        title=title,
        message=message,
        notification_type=notification_type,
        related_appointment_id=appointment_id,
    )


# ─── Telegram Bot API ─────────────────────────────────────────────────────────

def _bot_request(method: str, payload: dict) -> dict:
    """Low-level helper: POST to Telegram Bot API."""
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        logger.warning('TELEGRAM_BOT_TOKEN is not set.')
        return {'ok': False, 'error': 'Token not configured'}
    url = f'https://api.telegram.org/bot{token}/{method}'
    try:
        resp = requests.post(url, json=payload, timeout=10)
        data = resp.json()
        if not data.get('ok'):
            logger.warning(f'Telegram API error [{method}]: {data}')
        return data
    except requests.RequestException as e:
        logger.error(f'Telegram request failed [{method}]: {e}')
        return {'ok': False, 'error': str(e)}


def send_telegram_message(chat_id: str, text: str) -> bool:
    """
    Send an HTML-formatted message to a chat.
    Returns True on success.
    """
    if not chat_id:
        return False
    result = _bot_request('sendMessage', {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML',
    })
    return result.get('ok', False)


def set_telegram_webhook(site_url: str) -> dict:
    """
    Register the webhook URL with Telegram.
    Call this once after deployment or when the domain changes.
    Returns the Telegram API response dict.
    """
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        return {'ok': False, 'error': 'Token not configured'}
    webhook_url = f'{site_url.rstrip("/")}/telegram/webhook/{token}/'
    return _bot_request('setWebhook', {'url': webhook_url})


def delete_telegram_webhook() -> dict:
    """Remove the registered webhook."""
    return _bot_request('deleteWebhook', {})


def get_webhook_info() -> dict:
    """Get current webhook info from Telegram API."""
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        return {}
    url = f'https://api.telegram.org/bot{token}/getWebhookInfo'
    try:
        resp = requests.get(url, timeout=10)
        return resp.json().get('result', {})
    except Exception:
        return {}


def get_bot_info() -> dict:
    """Get bot username and name."""
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        return {}
    url = f'https://api.telegram.org/bot{token}/getMe'
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        return data.get('result', {})
    except Exception:
        return {}


# ─── Booking Notification Message ────────────────────────────────────────────

def build_booking_message(appointment) -> str:
    """Build a formatted Telegram message for a new booking."""
    c = appointment.customer
    s = appointment.service
    e = appointment.employee
    date_str = appointment.date.strftime('%d %B %Y')
    time_str = appointment.time.strftime('%H:%M')
    emp_str = e.name if e else 'Any available'

    return (
        f'📅 <b>New Booking!</b>\n'
        f'━━━━━━━━━━━━━━━━━\n'
        f'👤 <b>Customer:</b> {c.full_name}\n'
        f'📞 <b>Phone:</b> {c.phone}\n'
        f'💼 <b>Service:</b> {s.name if s else "—"}\n'
        f'👨‍⚕️ <b>Staff:</b> {emp_str}\n'
        f'📆 <b>Date:</b> {date_str}\n'
        f'🕐 <b>Time:</b> {time_str}\n'
        f'━━━━━━━━━━━━━━━━━\n'
        f'<i>Manage in your dashboard</i>'
    )
