from django.db import models
from business.models import Business


class Service(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    duration = models.PositiveIntegerField(help_text='Duration in minutes')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'name']
        indexes = [models.Index(fields=['business', 'is_active'])]

    @property
    def duration_display(self):
        if self.duration >= 60:
            h, m = divmod(self.duration, 60)
            return f'{h}h {m}m' if m else f'{h}h'
        return f'{self.duration}m'

    def __str__(self):
        return f'{self.name} ({self.business.name})'
