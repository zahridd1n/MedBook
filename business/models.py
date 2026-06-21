import secrets
from django.db import models
from django.conf import settings
from django.utils.text import slugify


class Business(models.Model):
    CATEGORY_CHOICES = [
        ('clinic', 'Clinic'), ('dental', 'Dental Clinic'),
        ('beauty', 'Beauty Salon'), ('barber', 'Barber Shop'),
        ('education', 'Educational Center'), ('auto', 'Auto Service'),
        ('other', 'Other'),
    ]

    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='business'
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    about = models.TextField(blank=True)
    logo = models.ImageField(upload_to='business/logos/', blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=300, blank=True)
    city = models.CharField(max_length=100, blank=True)
    telegram = models.CharField(max_length=100, blank=True, help_text='Telegram username for public display')
    instagram = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)

    # ─── Telegram Bot Integration ────────────────────────────────────────────
    telegram_chat_id = models.CharField(
        max_length=50, blank=True,
        help_text='Auto-filled when business owner connects via bot'
    )
    telegram_notifications_enabled = models.BooleanField(
        default=False,
        help_text='Send booking notifications to Telegram'
    )
    telegram_connect_token = models.CharField(
        max_length=64, blank=True,
        help_text='One-time token used in the bot /start deep link'
    )
    # ─────────────────────────────────────────────────────────────────────────

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Business'
        verbose_name_plural = 'Businesses'
        indexes = [models.Index(fields=['slug'])]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            slug = base
            n = 1
            while Business.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{n}'
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    # ─── Telegram helpers ────────────────────────────────────────────────────
    def generate_connect_token(self):
        """Generate a fresh one-time token; save and return it."""
        self.telegram_connect_token = secrets.token_urlsafe(32)
        self.save(update_fields=['telegram_connect_token'])
        return self.telegram_connect_token

    def get_telegram_connect_url(self):
        """
        Returns a t.me deep link the owner clicks in Telegram to connect.
        Requires TELEGRAM_BOT_USERNAME set in settings.
        """
        bot_username = getattr(settings, 'TELEGRAM_BOT_USERNAME', '')
        if not bot_username or not self.telegram_connect_token:
            return None
        return f'https://t.me/{bot_username}?start={self.telegram_connect_token}'

    @property
    def telegram_connected(self):
        return bool(self.telegram_chat_id)
    # ─────────────────────────────────────────────────────────────────────────

    def __str__(self):
        return self.name


class WorkingHours(models.Model):
    DAYS = [
        (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'),
        (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday'),
    ]
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='working_hours')
    day = models.IntegerField(choices=DAYS)
    is_open = models.BooleanField(default=True)
    open_time = models.TimeField(null=True, blank=True)
    close_time = models.TimeField(null=True, blank=True)

    class Meta:
        unique_together = ('business', 'day')
        ordering = ['day']

    def __str__(self):
        return f'{self.business.name} – {self.get_day_display()}'


class FAQ(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='faqs')
    question = models.CharField(max_length=300)
    answer = models.TextField()
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.question
