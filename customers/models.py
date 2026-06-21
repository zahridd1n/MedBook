from django.db import models
from business.models import Business


class Customer(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='customers')
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['full_name']
        indexes = [
            models.Index(fields=['business', 'phone']),
            models.Index(fields=['business']),
        ]

    @property
    def appointment_count(self):
        return self.appointments.count()

    @property
    def last_visit(self):
        last = self.appointments.filter(status='completed').order_by('-date').first()
        return last.date if last else None

    def __str__(self):
        return f'{self.full_name} ({self.phone})'
