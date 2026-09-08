import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60, name='notifications.send_telegram')
def send_telegram_notification_task(self, chat_id: str, message: str):
    """
    Async Celery task: send a Telegram message with automatic retry.

    Usage:
        send_telegram_notification_task.delay(chat_id, message)

    Retries up to 3 times with 60 second delay on failure.
    """
    from .utils import send_telegram_message
    try:
        success = send_telegram_message(chat_id, message)
        if not success:
            raise Exception(f'Telegram API returned failure for chat_id={chat_id}')
        logger.info(f'[Telegram] Notification sent to chat_id={chat_id}')
        return {'status': 'sent', 'chat_id': chat_id}
    except Exception as exc:
        logger.warning(f'[Telegram] Task attempt {self.request.retries + 1} failed: {exc}')
        raise self.retry(exc=exc)


@shared_task(name='notifications.send_daily_appointments')
def send_daily_appointments_task():
    """
    Sends today's appointments to businesses that have connected a Telegram bot.
    Scheduled to run daily at 08:00 AM (Asia/Tashkent) via Celery Beat.
    """
    from django.utils import timezone
    from business.models import Business
    from appointments.models import Appointment

    today = timezone.localdate()
    logger.info(f'[DailyTask] Running for date: {today}')

    businesses = (
        Business.objects
        .filter(
            is_active=True,
            telegram_notifications_enabled=True,
        )
        .exclude(telegram_chat_id='')
        .exclude(telegram_chat_id__isnull=True)
    )

    # Reja (tarif) tekshiruvi: 
    # faqat haqiqatda Telegram xizmatidan foydalana oladigan bizneslarni qoldiramiz.
    businesses = [biz for biz in businesses if biz.can_use_telegram()]

    logger.info(f'[DailyTask] Telegram ulangan faol bizneslar: {len(businesses)}')

    sent_count = 0
    for biz in businesses:
        try:
            appointments = (
                Appointment.objects
                .filter(business=biz, date=today)
                .exclude(status=Appointment.STATUS_CANCELLED)
                .select_related('customer', 'service', 'employee')
                .order_by('time')
            )

            if not appointments.exists():
                logger.info(f'[DailyTask] {biz.name}: bugun qabul yo\'q, o\'tkazib yuborildi.')
                continue

            date_str = today.strftime('%d.%m.%Y')
            count = appointments.count()
            msg_lines = [
                f"📅 <b>Bugungi qabullar ro'yxati ({date_str})</b>\n",
                f"Sizda bugun jami <b>{count}</b> ta qabul mavjud:\n",
            ]

            for idx, appt in enumerate(appointments, 1):
                time_str = appt.time.strftime('%H:%M') if appt.time else '--:--'
                customer_name = appt.customer.full_name if appt.customer else "Noma'lum"
                service_name = appt.service.name if appt.service else 'Xizmat belgilanmagan'
                emp_name = appt.employee.name if appt.employee else '—'

                msg_lines.append(
                    f"{idx}. 🕒 <b>{time_str}</b> | 👤 {customer_name}\n"
                    f"   💼 {service_name}  👨‍⚕️ {emp_name}\n"
                )

            msg_lines.append("<i>Batafsil ma'lumotni dashboard'dan ko'rishingiz mumkin.</i>")
            final_message = "\n".join(msg_lines)

            send_telegram_notification_task.delay(biz.telegram_chat_id, final_message)
            logger.info(f'[DailyTask] {biz.name}: {count} ta qabul — xabar navbatga qo\'yildi.')
            sent_count += 1

        except Exception as e:
            logger.error(f'[DailyTask] {biz.name} uchun xatolik: {e}', exc_info=True)
            continue

    logger.info(f'[DailyTask] Yakunlandi. {sent_count} ta biznesga xabar jo\'natildi.')
    return {'sent': sent_count, 'date': str(today)}
