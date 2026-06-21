from django.db import models
from business.models import Business


class Notification(models.Model):
    TYPE_BOOKING = 'booking'
    TYPE_SYSTEM = 'system'
    TYPE_REMINDER = 'reminder'

    TYPE_CHOICES = [
        (TYPE_BOOKING, 'New Booking'),
        (TYPE_SYSTEM, 'System'),
        (TYPE_REMINDER, 'Reminder'),
    ]

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_BOOKING)
    is_read = models.BooleanField(default=False)
    related_appointment_id = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['business', 'is_read'])]

    def __str__(self):
        return f'[{self.business.name}] {self.title}'
