import secrets
from django.db import models
from django.conf import settings
from django.utils import timezone
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

    # ─── Branding / Customization ────────────────────────────────────────────
    BUTTON_STYLE_CHOICES = [
        ('rounded', 'Yumaloq (Rounded)'),
        ('square', 'To\'rtburchak (Square)'),
        ('pill', 'Pill shaklida'),
    ]
    SHADOW_CHOICES = [
        ('light', 'Yengil'),
        ('medium', 'O\'rtacha'),
        ('strong', 'Kuchli'),
    ]

    primary_color = models.CharField(
        max_length=7, default='#6366f1',
        help_text='Public sahifa asosiy rangi (hex masalan #6366f1)',
    )
    banner_image = models.ImageField(
        upload_to='business/banners/', blank=True, null=True,
        help_text='Public sahifa banner rasmi (pullik tariflar uchun)',
    )
    button_style = models.CharField(
        max_length=20, choices=BUTTON_STYLE_CHOICES, default='rounded',
        help_text='Tugmalar shakli',
    )
    card_shadow = models.CharField(
        max_length=20, choices=SHADOW_CHOICES, default='medium',
        help_text='Kartochkalar soyasi',
    )
    custom_css = models.TextField(
        blank=True,
        help_text='Maxsus CSS (faqat Korporativ tarif)',
    )
    # ─────────────────────────────────────────────────────────────────────────

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
    is_blocked = models.BooleanField(
        default=False,
        help_text='Admin tomonidan bloklangan biznes dashboardga kira olmaydi',
    )

    # ─── Subscription / Payment ───────────────────────────────────────────────
    PLAN_CHOICES = [
        ('free', 'Free / Starter'),
        ('growth', 'Growth'),
        ('enterprise', 'Enterprise'),
    ]
    SUB_STATUS_CHOICES = [
        ('trial', 'Trial'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]
    subscription_plan = models.CharField(
        max_length=20, choices=PLAN_CHOICES, default='free',
    )
    subscription_status = models.CharField(
        max_length=20, choices=SUB_STATUS_CHOICES, default='trial',
    )
    subscription_start = models.DateTimeField(null=True, blank=True)
    subscription_end = models.DateTimeField(null=True, blank=True)
    # ─────────────────────────────────────────────────────────────────────────

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

    # ─── Plan / Subscription helpers ────────────────────────────────────────
    PLAN_LIMITS = {
        'free':     {'max_employees': 1, 'max_appointments_monthly': 50},
        'growth':   {'max_employees': 5, 'max_appointments_monthly': None},
        'enterprise': {'max_employees': None, 'max_appointments_monthly': None},
    }

    @property
    def plan_data(self):
        return self.PLAN_LIMITS.get(self.subscription_plan, self.PLAN_LIMITS['free'])

    @property
    def max_employees(self):
        return self.plan_data['max_employees']

    @property
    def max_appointments_monthly(self):
        return self.plan_data['max_appointments_monthly']

    def can_add_employee(self):
        mx = self.max_employees
        if mx is None:
            return True
        return self.employees.count() < mx

    def can_create_appointment(self):
        mx = self.max_appointments_monthly
        if mx is None:
            return True
        now = timezone.now()
        count = self.appointments.filter(
            date__year=now.year,
            date__month=now.month,
        ).exclude(status='cancelled').count()
        return count < mx

    def can_use_telegram(self):
        return self.subscription_plan in ('growth', 'enterprise')

    def can_use_custom_domain(self):
        return self.subscription_plan in ('growth', 'enterprise')

    def can_use_custom_css(self):
        return self.subscription_plan == 'enterprise'

    def can_use_api(self):
        return self.subscription_plan == 'enterprise'

    @property
    def plan_display(self):
        return dict(self.PLAN_CHOICES).get(self.subscription_plan, 'Free / Starter')

    def enforce_subscription(self):
        from django.utils import timezone
        now = timezone.now()
        changed = False

        if self.subscription_end and self.subscription_end < now:
            if self.subscription_status != 'expired':
                self.subscription_status = 'expired'
                changed = True
            if self.subscription_plan != 'free':
                self.subscription_plan = 'free'
                changed = True

        if self.subscription_status == 'expired' and self.subscription_plan != 'free':
            self.subscription_plan = 'free'
            changed = True

        if changed:
            self.save(update_fields=['subscription_status', 'subscription_plan'])

        return changed

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
