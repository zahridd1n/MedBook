from django.db import models
from business.models import Business
from services.models import Service


class Employee(models.Model):
    DAYS = [
        (0,'Monday'),(1,'Tuesday'),(2,'Wednesday'),
        (3,'Thursday'),(4,'Friday'),(5,'Saturday'),(6,'Sunday'),
    ]
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='employees')
    name = models.CharField(max_length=200)
    position = models.CharField(max_length=200, blank=True)
    photo = models.ImageField(upload_to='employees/photos/', blank=True, null=True)
    bio = models.TextField(blank=True)
    services = models.ManyToManyField(Service, blank=True, related_name='employees')
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'name']
        indexes = [models.Index(fields=['business', 'is_active'])]

    def __str__(self):
        return f'{self.name} ({self.business.name})'


class EmployeeSchedule(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='schedules')
    day = models.IntegerField(choices=Employee.DAYS)
    is_working = models.BooleanField(default=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)

    class Meta:
        unique_together = ('employee', 'day')
        ordering = ['day']

    def __str__(self):
        return f'{self.employee.name} – {self.get_day_display()}'
