import secrets
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
import json


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
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        help_text='Joylashuv kengligi (xarita orqali kiritiladi)',
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        help_text='Joylashuv uzunligi (xarita orqali kiritiladi)',
    )
    telegram = models.CharField(max_length=100, blank=True, help_text='Telegram username for public display')
    instagram = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)

    # ─── Marketing Directory ───────────────────────────────────────────────────
    show_in_directory = models.BooleanField(
        default=False,
        help_text='Marketing sahifasidagi bizneslar ro\'yxatida ko\'rsatish',
    )

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
    NAVBAR_STYLE_CHOICES = [
        ('glass', 'Glass Ultra — Vision Pro uslubi'),
        ('minimal', 'Minimal Luxury — Linear uslubi'),
        ('modern', 'Modern Creative — Framer uslubi'),
    ]
    navbar_style = models.CharField(
        max_length=20, choices=NAVBAR_STYLE_CHOICES, default='glass',
        help_text='Sahifa menyusi uslubi (pullik tariflar uchun)',
    )
    custom_css = models.TextField(
        blank=True,
        help_text='Maxsus CSS (faqat Max tarif)',
    )

    # ─── Custom Domain ─────────────────────────────────────────────────────────
    custom_domain = models.CharField(
        max_length=255, blank=True, null=True, unique=True,
        help_text='Masalan: booking.meningklinikam.uz',
    )
    domain_verified = models.BooleanField(default=False)
    domain_verify_token = models.CharField(
        max_length=64, blank=True, default='',
        help_text='DNS TXT record uchun token (avtomatik generatsiya qilinadi)',
    )
    # ─────────────────────────────────────────────────────────────────────────

    # ─── Google Calendar Integration ──────────────────────────────────────────
    google_credentials = models.JSONField(
        null=True, blank=True,
        help_text='Google OAuth credentials (token, refresh_token, etc)',
    )
    google_calendar_id = models.CharField(
        max_length=200, blank=True, default='primary',
        help_text='Google Calendar ID (default: primary)',
    )
    google_calendar_sync_enabled = models.BooleanField(default=False)
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

    # ─── SEO ────────────────────────────────────────────────────────────────────
    meta_title = models.CharField(max_length=70, blank=True, help_text='SEO title (bo\'sh bo\'lsa biznes nomi ishlatiladi)')
    meta_description = models.CharField(max_length=160, blank=True, help_text='Meta description (bo\'sh bo\'lsa "about" ishlatiladi)')
    meta_keywords = models.CharField(max_length=255, blank=True, help_text='Meta keywords (vergul bilan ajrating)')
    og_image = models.ImageField(upload_to='business/og/', blank=True, null=True, help_text='Open Graph rasm (link yuborilganda chiqadi)')
    # ─────────────────────────────────────────────────────────────────────────

    # ─── White Label ───────────────────────────────────────────────────────────
    white_label_enabled = models.BooleanField(default=False, help_text='White Label (BookFlow brendi yashirish)')
    # ─────────────────────────────────────────────────────────────────────────

    # ─── API & Webhook ─────────────────────────────────────────────────────────
    api_key = models.CharField(max_length=64, blank=True, default='', help_text='API kaliti (avtomatik generatsiya)')
    api_key_created = models.DateTimeField(null=True, blank=True, help_text='API kaliti yaratilgan vaqt')
    webhook_url = models.URLField(blank=True, default='', help_text='Webhook URL manzili')
    # ─────────────────────────────────────────────────────────────────────────

    is_active = models.BooleanField(default=True)
    is_blocked = models.BooleanField(
        default=False,
        help_text='Admin tomonidan bloklangan biznes dashboardga kira olmaydi',
    )

    # ─── Subscription / Payment ───────────────────────────────────────────────
    PLAN_CHOICES = [
        ('free',       'Start'),
        ('growth',     'Pro'),
        ('enterprise', 'Max'),
    ]
    SUB_STATUS_CHOICES = [
        ('trial',     'Sinov'),
        ('active',    'Faol'),
        ('expired',   'Muddati tugagan'),
        ('cancelled', 'Bekor qilingan'),
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
    # Har bir tarif uchun cheklovlar va narxlar
    @property
    def plan_data(self):
        from superadmin.models import PricingPlan
        plan = PricingPlan.objects.filter(slug=self.subscription_plan).first()
        if not plan:
            # Fallback to free plan if not found
            plan = PricingPlan.objects.filter(slug='free').first()
        
        if plan:
            return {
                'max_employees': plan.max_employees,
                'max_appointments_monthly': plan.max_appointments_monthly,
                'telegram': plan.allow_telegram,
                'email': plan.allow_email,
                'custom_domain': plan.allow_custom_domain,
                'branding': plan.allow_branding,
                'custom_css': plan.allow_custom_css,
                'google_calendar': plan.allow_google_calendar,
                'api': plan.allow_api,
                'white_label': plan.allow_white_label,
                'advanced_seo': plan.allow_advanced_seo,
                'price_monthly': plan.price_monthly,
                'price_label': plan.price_label,
            }
        
        # Absolute fallback if db is empty
        return {
            'max_employees': 1,
            'max_appointments_monthly': 50,
            'telegram': False,
            'email': True,
            'custom_domain': False,
            'branding': False,
            'custom_css': False,
            'google_calendar': False,
            'api': False,
            'white_label': False,
            'advanced_seo': False,
            'price_monthly': 0,
            'price_label': "0 UZS",
        }

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
        return self.plan_data.get('telegram', False)

    def can_use_custom_domain(self):
        return self.plan_data.get('custom_domain', False)

    def can_use_custom_css(self):
        return self.plan_data.get('custom_css', False)

    def can_use_api(self):
        return self.plan_data.get('api', False)

    def can_use_google_calendar(self):
        return self.plan_data.get('google_calendar', False)

    def can_use_branding(self):
        return self.plan_data.get('branding', False)

    def can_use_white_label(self):
        return self.plan_data.get('white_label', False)

    def can_use_advanced_seo(self):
        return self.plan_data.get('advanced_seo', False)

    def can_use_analytics(self):
        return self.subscription_plan != 'free'

    @property
    def plan_display(self):
        from superadmin.models import PricingPlan
        plan = PricingPlan.objects.filter(slug=self.subscription_plan).first()
        if plan:
            return plan.name
        return dict(self.PLAN_CHOICES).get(self.subscription_plan, 'Start')

    @property
    def plan_price_label(self):
        return self.plan_data.get('price_label', '0 UZS')

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


class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('approved', 'Tasdiqlangan'),
        ('rejected', 'Bekor qilingan'),
    ]

    DURATION_CHOICES = [
        ('3months', '3 oylik (90 kun)'),
        ('yearly',  '1 yillik (365 kun)'),
    ]

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='payments')
    plan = models.CharField(max_length=50, help_text='Tarif slug (masalan: growth, enterprise)')
    duration = models.CharField(
        max_length=20, choices=DURATION_CHOICES, default='3months',
        help_text="Obuna davomiyligi: 3 oylik yoki 1 yillik",
    )
    amount = models.PositiveIntegerField(help_text='To\'lov summasi (UZS)')
    receipt = models.FileField(upload_to='payments/receipts/', help_text='Chek rasmi')
    note = models.TextField(blank=True, help_text='Foydalanuvchi izohi')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    rejected_reason = models.TextField(blank=True, help_text='Rad etish sababi (superadmin)')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def get_plan_display(self):
        from superadmin.models import PricingPlan
        plan_obj = PricingPlan.objects.filter(slug=self.plan).first()
        return plan_obj.name if plan_obj else self.plan

    def __str__(self):
        return f'{self.business.name} – {self.get_plan_display()} ({self.get_status_display()})'


class QRCodeScan(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='qr_scans')
    scanned_at = models.DateTimeField(auto_now_add=True)
    user_agent = models.TextField(blank=True, default='')
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    referrer = models.CharField(max_length=500, blank=True, default='')

    class Meta:
        ordering = ['-scanned_at']
        verbose_name = 'QR Code Scan'
        verbose_name_plural = 'QR Code Scans'
        indexes = [
            models.Index(fields=['business', 'scanned_at']),
        ]

    def __str__(self):
        return f'{self.business.name} – {self.scanned_at}'
