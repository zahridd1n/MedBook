import logging
import json
from urllib.request import Request, urlopen
from urllib.error import URLError
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Appointment
from business.google_calendar import create_event, update_event, delete_event

logger = logging.getLogger(__name__)


def send_webhook(business, appointment):
    if not business.webhook_url or not business.api_key:
        return
    data = {
        'event': 'appointment.created',
        'id': appointment.id,
        'date': str(appointment.date),
        'time': str(appointment.time),
        'status': appointment.status,
        'customer_name': appointment.customer.full_name if appointment.customer else '',
        'customer_phone': appointment.customer.phone if appointment.customer else '',
        'service_name': appointment.service.name if appointment.service else '',
        'employee_name': appointment.employee.full_name if appointment.employee else '',
        'price': appointment.price,
    }
    try:
        req = Request(
            business.webhook_url,
            data=json.dumps(data).encode('utf-8'),
            headers={
                'Content-Type': 'application/json',
                'X-API-Key': business.api_key,
                'X-Webhook-Source': 'bookflow',
            },
            method='POST',
        )
        urlopen(req, timeout=5)
    except URLError as e:
        logger.warning(f'Webhook error for {business.slug}: {e}')
    except Exception as e:
        logger.error(f'Webhook unexpected error for {business.slug}: {e}')


@receiver(post_save, sender=Appointment)
def sync_appointment_to_google_calendar(sender, instance, created, **kwargs):
    business = instance.business
    if not business.google_calendar_sync_enabled or not business.google_credentials:
        return
    creds = business.google_credentials
    cal_id = business.google_calendar_id or 'primary'
    event_id = instance.google_event_id or ''

    if instance.status == 'cancelled':
        if event_id:
            delete_event(creds, cal_id, event_id)
            Appointment.objects.filter(pk=instance.pk).update(google_event_id='')
        return

    if created:
        new_event_id = create_event(creds, cal_id, instance)
        if new_event_id:
            Appointment.objects.filter(pk=instance.pk).update(google_event_id=new_event_id)
    else:
        if event_id:
            update_event(creds, cal_id, event_id, instance)


@receiver(post_save, sender=Appointment)
def send_webhook_on_appointment(sender, instance, created, **kwargs):
    if created and instance.status != 'cancelled':
        send_webhook(instance.business, instance)


@receiver(post_delete, sender=Appointment)
def delete_appointment_from_google_calendar(sender, instance, **kwargs):
    if instance.google_event_id:
        business = instance.business
        if business.google_credentials:
            delete_event(
                business.google_credentials,
                business.google_calendar_id or 'primary',
                instance.google_event_id,
            )
