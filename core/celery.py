import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('core')
app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.beat_schedule = {
    'send-daily-appointments-morning': {
        'task': 'notifications.send_daily_appointments',
        'schedule': crontab(hour=8, minute=0),
    },
}

app.autodiscover_tasks()
