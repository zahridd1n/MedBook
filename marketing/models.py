from django.db import models
from django.core.cache import cache


class MarketingVideo(models.Model):
    LANGUAGE_CHOICES = [
        ('uz', 'O\'zbek'),
        ('ru', 'Русский'),
        ('en', 'English'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    youtube_id = models.CharField(max_length=100, blank=True, default='', help_text='YouTube video ID (masalan: dQw4w9WgXcQ)')
    file = models.FileField(upload_to='marketing/videos/', blank=True, null=True, help_text='Yuklangan MP4 video fayl')
    duration = models.CharField(max_length=20, default='5:00', help_text='Video davomiyligi (masalan: 5:30)')
    order = models.PositiveIntegerField(default=0)
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default='uz')
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = 'Marketing video'
        verbose_name_plural = 'Marketing videolar'

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        cache.delete(f'marketing_videos_{self.language}')

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        cache.delete(f'marketing_videos_{self.language}')

    def file_url(self):
        if self.file and hasattr(self.file, 'url'):
            return self.file.url
        return ''
