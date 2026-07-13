import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from business.models import Payment
from .telegram_bot import notify_payment

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Payment)
def payment_saved_handler(sender, instance, created, **kwargs):
    if instance.status == 'pending':
        try:
            notify_payment(instance)
        except Exception as e:
            logger.error('[SuperadminBot] Failed to notify payment %s: %s', instance.pk, e)
