from django.db import models


class SiteSettings(models.Model):
    """
    Singleton model for site-wide settings.
    Only one row should exist — use SiteSettings.load() to get/create it.
    """

    # ─── Hero Section ─────────────────────────────────────────────────────────
    hero_title = models.CharField(
        max_length=300,
        default='Biznesingiz Bandlovlarini Avtomatlashtiring',
        help_text='Marketing sahifasi bosh sarlavhasi',
    )
    hero_subtitle = models.TextField(
        default='Xizmat ko\'rsatuvchi bizneslar uchun eng oddiy navbat tizimi.',
        help_text='Marketing sahifasi taglavhasi',
    )

    # ─── Pricing (UZS) ───────────────────────────────────────────────────────
    starter_price = models.PositiveIntegerField(
        default=0, help_text='Starter plan narxi (UZS/oy)'
    )
    growth_price_monthly = models.PositiveIntegerField(
        default=99000, help_text='Growth plan oylik narxi (UZS)'
    )
    growth_price_yearly = models.PositiveIntegerField(
        default=79000, help_text='Growth plan yillik narxi (UZS/oy)'
    )
    enterprise_price_monthly = models.PositiveIntegerField(
        default=249000, help_text='Enterprise plan oylik narxi (UZS)'
    )
    enterprise_price_yearly = models.PositiveIntegerField(
        default=199000, help_text='Enterprise plan yillik narxi (UZS/oy)'
    )

    # ─── Stats displayed on marketing page ────────────────────────────────────
    stats_uptime = models.CharField(
        max_length=20, default='99.9%', help_text='Uptime ko\'rsatkichi'
    )
    stats_appointments = models.CharField(
        max_length=50, default='20,000+', help_text='Jami bandlovlar soni'
    )
    stats_businesses = models.CharField(
        max_length=50, default='500+', help_text='Faol bizneslar soni'
    )

    # ─── Contact and Branding ─────────────────────────────────────────────
    logo = models.ImageField(
        upload_to='site_logos/',
        null=True, blank=True,
        help_text='Sayt logotipi (Oq/shaffof tavsiya etiladi)'
    )
    contact_phone = models.CharField(
        max_length=50,
        default='+998 90 123 45 67',
        help_text='Aloqa telefon raqami'
    )
    contact_email = models.CharField(
        max_length=150,
        default='support@booksaas.com',
        help_text='Aloqa email manzili'
    )
    contact_telegram = models.CharField(
        max_length=150,
        default='https://t.me/BookSaaSBot',
        help_text='Telegram bot yoki guruh havolasi'
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'

    def __str__(self):
        return 'Site Settings'

    def save(self, *args, **kwargs):
        # Enforce singleton — always use pk=1
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
