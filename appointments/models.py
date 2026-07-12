from django.db import models
from django.utils import timezone
from business.models import Business
from services.models import Service
from employees.models import Employee
from customers.models import Customer


class Appointment(models.Model):
    STATUS_NEW = 'new'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_NEW, 'Yangi'),
        (STATUS_CONFIRMED, 'Tasdiqlangan'),
        (STATUS_COMPLETED, 'Yakunlangan'),
        (STATUS_CANCELLED, 'Bekor qilingan'),
    ]
    STATUS_COLORS = {
        STATUS_NEW: 'primary',
        STATUS_CONFIRMED: 'success',
        STATUS_COMPLETED: 'secondary',
        STATUS_CANCELLED: 'danger',
    }

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='appointments')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='appointments')
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, related_name='appointments')
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='appointments')
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW)
    notes = models.TextField(blank=True, help_text='Mijoz eslatmasi')
    doctor_notes = models.TextField(blank=True, help_text='Shifokor/xodim qaydlari, tashxis, tavsiyalar')
    end_time = models.TimeField(null=True, blank=True)
    google_event_id = models.CharField(max_length=200, blank=True, help_text='Google Calendar event ID')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-time']
        indexes = [
            models.Index(fields=['business', 'date']),
            models.Index(fields=['business', 'status']),
            models.Index(fields=['customer']),
        ]

    def save(self, *args, **kwargs):
        if self.service and self.time:
            from datetime import datetime, timedelta
            dt = datetime.combine(self.date, self.time)
            self.end_time = (dt + timedelta(minutes=self.service.duration)).time()
        super().save(*args, **kwargs)

    @property
    def status_color(self):
        return self.STATUS_COLORS.get(self.status, 'secondary')

    @property
    def is_today(self):
        return self.date == timezone.localdate()

    def __str__(self):
        return f'{self.customer.full_name} – {self.service} on {self.date} {self.time}'
