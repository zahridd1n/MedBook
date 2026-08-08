import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('core')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Vaqt zonasi — Celery Beat crontab shu timezone'da ishlaydi
app.conf.timezone = 'Asia/Tashkent'
app.conf.enable_utc = True   # Ichki saqlash UTC da, lekin schedule Tashkent'da

app.conf.beat_schedule = {
    'send-daily-appointments-morning': {
        'task': 'notifications.send_daily_appointments',
        'schedule': crontab(hour=8, minute=0),
        'options': {'expires': 3600},   # 1 soat ichida bajarilmasa eskiradi
    },
}

app.autodiscover_tasks()
