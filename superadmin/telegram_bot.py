import json
import logging
import requests
from django.conf import settings
from django.urls import reverse

logger = logging.getLogger(__name__)

API_URL = 'https://api.telegram.org/bot'


def _bot_request(method, params=None, files=None):
    token = getattr(settings, 'SUPERADMIN_BOT_TOKEN', '')
    if not token:
        logger.warning('[SuperadminBot] Token not configured')
        return None
    url = f'{API_URL}{token}/{method}'
    try:
        resp = requests.post(url, data=params, files=files, timeout=15)
        data = resp.json()
        if not data.get('ok'):
            logger.warning('[SuperadminBot] API error: %s', data)
        return data
    except requests.RequestException as e:
        logger.error('[SuperadminBot] Request failed: %s', e)
        return None


def get_admins():
    raw = getattr(settings, 'SUPERADMIN_CHAT_IDS', '')
    return [int(c.strip()) for c in raw.split(',') if c.strip()]


def send_message(chat_id, text, parse_mode='HTML'):
    return _bot_request('sendMessage', {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': parse_mode,
    })


def send_photo(chat_id, photo_path, caption='', parse_mode='HTML', reply_markup=None):
    params = {'chat_id': chat_id}
    if caption:
        params['caption'] = caption
        params['parse_mode'] = parse_mode
    if reply_markup:
        params['reply_markup'] = json.dumps(reply_markup)
    with open(photo_path, 'rb') as f:
        return _bot_request('sendPhoto', params, files={'photo': f})


def notify_payment(payment):
    admins = get_admins()
    if not admins:
        logger.warning('[SuperadminBot] No admin chat IDs configured')
        return

    business = payment.business
    plan_label = dict(business.PLAN_CHOICES).get(payment.plan, payment.plan)
    status_label = dict(payment.STATUS_CHOICES).get(payment.status, payment.status)

    admin_url = settings.SITE_URL.rstrip('/') + reverse('admin:business_payment_change', args=[payment.pk])

    caption = (
        f"💳 <b>Yangi to'lov</b>\n\n"
        f"🏢 <b>Biznes:</b> {business.name}\n"
        f"👤 <b>Egasi:</b> {business.owner.get_full_name() or business.owner.email}\n"
        f"📞 <b>Telefon:</b> {business.phone or '—'}\n"
        f"📋 <b>Tarif:</b> {plan_label}\n"
        f"💰 <b>Summa:</b> {payment.amount:,} UZS\n"
        f"📝 <b>Izoh:</b> {payment.note or '—'}\n"
        f"📌 <b>Holat:</b> {status_label}\n\n"
        f"🔗 <a href='{admin_url}'>Admin panelda ko'rish</a>"
    )

    keyboard = {
        'inline_keyboard': [
            [
                {'text': '✅ Tasdiqlash', 'callback_data': f'approve_{payment.pk}'},
                {'text': '❌ Rad etish', 'callback_data': f'reject_{payment.pk}'},
            ],
            [
                {'text': '🔗 Admin panel', 'url': admin_url},
            ],
        ]
    }

    for chat_id in admins:
        if payment.receipt and hasattr(payment.receipt, 'path') and payment.receipt.path:
            try:
                send_photo(chat_id, payment.receipt.path, caption=caption, reply_markup=keyboard)
            except Exception as e:
                logger.error('[SuperadminBot] Photo send failed for %s: %s', chat_id, e)
                send_message(chat_id, caption, reply_markup=keyboard)
        else:
            send_message(chat_id, caption, reply_markup=keyboard)


def notify_payment_approved(payment):
    admins = get_admins()
    if not admins:
        return
    for chat_id in admins:
        send_message(
            chat_id,
            f"✅ <b>To'lov tasdiqlandi</b>\n\n"
            f"🏢 {payment.business.name}\n"
            f"💰 {payment.amount:,} UZS\n"
            f"📋 {payment.get_plan_display()}"
        )


def notify_payment_rejected(payment):
    admins = get_admins()
    if not admins:
        return
    for chat_id in admins:
        send_message(
            chat_id,
            f"❌ <b>To'lov rad etildi</b>\n\n"
            f"🏢 {payment.business.name}\n"
            f"💰 {payment.amount:,} UZS\n"
            f"📋 {payment.get_plan_display()}"
        )


def handle_callback(chat_id, callback_data):
    """Handle inline keyboard callbacks (approve/reject)."""
    from business.models import Payment

    action, payment_id = callback_data.split('_', 1)
    payment_id = int(payment_id)

    try:
        payment = Payment.objects.get(pk=payment_id)
    except Payment.DoesNotExist:
        send_message(chat_id, "❌ To'lov topilmadi.")
        return

    if action == 'approve':
        if payment.status == 'approved':
            send_message(chat_id, "✅ Bu to'lov avval tasdiqlangan.")
            return
        payment.status = 'approved'
        payment.save()
        notify_payment_approved(payment)
        send_message(chat_id, f"✅ To'lov tasdiqlandi: {payment.business.name} — {payment.amount:,} UZS")

    elif action == 'reject':
        if payment.status == 'rejected':
            send_message(chat_id, "❌ Bu to'lov avval rad etilgan.")
            return
        payment.status = 'rejected'
        payment.save()
        notify_payment_rejected(payment)
        send_message(chat_id, f"❌ To'lov rad etildi: {payment.business.name} — {payment.amount:,} UZS")


def set_webhook():
    token = getattr(settings, 'SUPERADMIN_BOT_TOKEN', '')
    if not token:
        logger.warning('[SuperadminBot] Token not configured, cannot set webhook')
        return False
    site_url = getattr(settings, 'SITE_URL', '').rstrip('/')
    webhook_url = f'{site_url}/telegram/superadmin-webhook/{token}/'
    result = _bot_request('setWebhook', {'url': webhook_url})
    if result and result.get('ok'):
        logger.info('[SuperadminBot] Webhook set to %s', webhook_url)
        return True
    logger.warning('[SuperadminBot] Failed to set webhook: %s', result)
    return False
