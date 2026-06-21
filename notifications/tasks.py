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
