from copy import deepcopy

from django.db import models


MARKETING_COPY_DEFAULTS = {
    'uz': {
        'nav': {
            'features': 'Imkoniyatlar',
            'pricing': 'Tariflar',
            'faq': 'Savollar',
            'contact': 'Aloqa',
            'login': 'Kirish',
            'dashboard': 'Dashboard',
            'start': 'Bepul boshlash',
        },
        'home': {
            'eyebrow': 'Onlayn band qilish tizimi',
            'title': 'Biznesingiz bandlovlarini avtomatlashtiring',
            'subtitle': 'Xizmat ko‘rsatuvchi bizneslar uchun mijozlarni onlayn qabul qilish, xodimlar jadvali, mijozlar bazasi va bildirishnomalarni boshqaradigan qulay platforma.',
            'primary_cta': 'Bepul boshlash',
            'secondary_cta': 'Imkoniyatlarni ko‘rish',
            'trust': ['Oson sozlash', 'Tez band qilish', 'Telegram xabarnomalar'],
            'section_eyebrow': 'Kundalik ish uchun',
            'section_title': 'Kamroq qo‘lda ish, ko‘proq band qilingan vaqt.',
            'section_subtitle': 'Administrator, xodim va mijoz uchun aniq va tushunarli jarayon.',
            'journey_eyebrow': 'Mijoz yo‘li',
            'journey_title': 'Mijoz havolani ochadi va bir necha qadamda band qiladi.',
            'journey_subtitle': 'Xizmatni tanlash, xodimni tanlash, vaqt belgilash va tasdiqlash. Mijoz ro‘yxatdan o‘tishi shart emas.',
            'cta_eyebrow': 'Boshlashga tayyor',
            'cta_title': 'Bugunoq zamonaviy band qilish sahifangizni ishga tushiring.',
            'cta_subtitle': 'Biznes profilini to‘ldiring, xizmatlarni qo‘shing va ommaviy havolani mijozlarga yuboring.',
        },
        'features': {
            'eyebrow': 'Imkoniyatlar',
            'title': 'Xizmat bizneslari uchun kerakli boshqaruv vositalari.',
            'subtitle': 'Bandlov, mijozlar, xodimlar, xizmatlar, xabarnomalar va ommaviy sahifa bitta tizimda.',
        },
        'pricing': {
            'eyebrow': 'Tariflar',
            'title': 'Narxlar admin paneldagi tariflardan olinadi.',
            'subtitle': 'Start, Pro va Max tariflari biznesingiz o‘sishiga moslashadi.',
            'monthly': 'oyiga',
            'yearly': 'yillik to‘lovda',
            'free': 'Bepul',
            'current': 'Boshlash',
            'contact': 'Bog‘lanish',
        },
        'faq': {
            'eyebrow': 'FAQ',
            'title': 'Ko‘p beriladigan savollar.',
            'subtitle': 'Tizimni ishga tushirish, bandlov sahifasi va tariflar bo‘yicha qisqa javoblar.',
        },
        'contact': {
            'eyebrow': 'Aloqa',
            'title': 'Bandlov jarayoningizni birga sozlaymiz.',
            'subtitle': 'Savollar, hamkorlik yoki sozlash bo‘yicha biz bilan bog‘laning.',
            'support_title': 'BookFlow aloqa',
            'support_text': 'Quyidagi ma’lumotlar superadmin sozlamalaridan olinadi.',
            'name': 'Ism',
            'email': 'Email',
            'message': 'Xabar',
            'send': 'Xabar yuborish',
        },
        'footer': 'Online bandlov, mijozlar oqimi va kundalik operatsiyalar uchun yagona platforma.',
    },
    'ru': {
        'nav': {
            'features': 'Возможности',
            'pricing': 'Тарифы',
            'faq': 'FAQ',
            'contact': 'Контакты',
            'login': 'Войти',
            'dashboard': 'Панель',
            'start': 'Начать бесплатно',
        },
        'home': {
            'eyebrow': 'Онлайн-бронирование',
            'title': 'Автоматизируйте записи вашего бизнеса',
            'subtitle': 'Платформа для сервисных бизнесов: онлайн-запись клиентов, расписание сотрудников, база клиентов и уведомления в одном месте.',
            'primary_cta': 'Начать бесплатно',
            'secondary_cta': 'Смотреть возможности',
            'trust': ['Легкая настройка', 'Быстрая запись', 'Telegram уведомления'],
            'section_eyebrow': 'Для ежедневной работы',
            'section_title': 'Меньше ручной рутины, больше записанного времени.',
            'section_subtitle': 'Понятный процесс для администратора, сотрудника и клиента.',
            'journey_eyebrow': 'Путь клиента',
            'journey_title': 'Клиент открывает ссылку и бронирует за несколько шагов.',
            'journey_subtitle': 'Выбор услуги, специалиста, времени и подтверждение. Клиенту не нужен аккаунт.',
            'cta_eyebrow': 'Готовы начать',
            'cta_title': 'Запустите современную страницу записи уже сегодня.',
            'cta_subtitle': 'Заполните профиль бизнеса, добавьте услуги и отправьте публичную ссылку клиентам.',
        },
        'features': {
            'eyebrow': 'Возможности',
            'title': 'Инструменты управления для сервисного бизнеса.',
            'subtitle': 'Записи, клиенты, сотрудники, услуги, уведомления и публичная страница в одной системе.',
        },
        'pricing': {
            'eyebrow': 'Тарифы',
            'title': 'Цены берутся из тарифов в админ-панели.',
            'subtitle': 'Тарифы Start, Pro и Max подстраиваются под рост вашего бизнеса.',
            'monthly': 'в месяц',
            'yearly': 'при годовой оплате',
            'free': 'Бесплатно',
            'current': 'Начать',
            'contact': 'Связаться',
        },
        'faq': {
            'eyebrow': 'FAQ',
            'title': 'Частые вопросы.',
            'subtitle': 'Короткие ответы про запуск, страницу записи и тарифы.',
        },
        'contact': {
            'eyebrow': 'Контакты',
            'title': 'Поможем настроить ваш процесс записи.',
            'subtitle': 'Свяжитесь с нами по вопросам настройки, сотрудничества или продукта.',
            'support_title': 'Контакты BookFlow',
            'support_text': 'Эти данные берутся из настроек superadmin.',
            'name': 'Имя',
            'email': 'Email',
            'message': 'Сообщение',
            'send': 'Отправить',
        },
        'footer': 'Единая платформа для онлайн-записи, клиентского потока и ежедневных операций.',
    },
    'en': {
        'nav': {
            'features': 'Features',
            'pricing': 'Pricing',
            'faq': 'FAQ',
            'contact': 'Contact',
            'login': 'Login',
            'dashboard': 'Dashboard',
            'start': 'Start free',
        },
        'home': {
            'eyebrow': 'Online booking system',
            'title': 'Automate bookings for your business',
            'subtitle': 'A practical platform for service businesses to manage online bookings, team schedules, customer records, and notifications.',
            'primary_cta': 'Start free',
            'secondary_cta': 'View features',
            'trust': ['Easy setup', 'Fast booking', 'Telegram alerts'],
            'section_eyebrow': 'For daily work',
            'section_title': 'Less manual work, more booked time.',
            'section_subtitle': 'A clear workflow for admins, employees, and customers.',
            'journey_eyebrow': 'Customer journey',
            'journey_title': 'Customers open your link and book in a few steps.',
            'journey_subtitle': 'Choose a service, pick a specialist, select a time, and confirm. No customer account required.',
            'cta_eyebrow': 'Ready to start',
            'cta_title': 'Launch your modern booking page today.',
            'cta_subtitle': 'Complete your business profile, add services, and share your public booking link.',
        },
        'features': {
            'eyebrow': 'Features',
            'title': 'Management tools for service businesses.',
            'subtitle': 'Bookings, customers, employees, services, notifications, and your public page in one system.',
        },
        'pricing': {
            'eyebrow': 'Pricing',
            'title': 'Prices come from your admin plan settings.',
            'subtitle': 'Start, Pro, and Max plans adapt as your business grows.',
            'monthly': 'per month',
            'yearly': 'yearly billing',
            'free': 'Free',
            'current': 'Start',
            'contact': 'Contact',
        },
        'faq': {
            'eyebrow': 'FAQ',
            'title': 'Frequently asked questions.',
            'subtitle': 'Short answers about setup, public booking pages, and plans.',
        },
        'contact': {
            'eyebrow': 'Contact',
            'title': 'Let us shape your booking workflow.',
            'subtitle': 'Reach out for setup, partnership, or product questions.',
            'support_title': 'BookFlow contact',
            'support_text': 'These details come from superadmin settings.',
            'name': 'Name',
            'email': 'Email',
            'message': 'Message',
            'send': 'Send message',
        },
        'footer': 'One platform for online booking, customer flow, and daily operations.',
    },
}


def deep_merge(base, override):
    merged = deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


class SiteSettings(models.Model):
    """Singleton model for site-wide settings."""

    hero_title = models.CharField(
        max_length=300,
        default='Biznesingiz Bandlovlarini Avtomatlashtiring',
        help_text='Marketing sahifasi bosh sarlavhasi',
    )
    hero_subtitle = models.TextField(
        default="Xizmat ko'rsatuvchi bizneslar uchun eng oddiy navbat tizimi.",
        help_text='Marketing sahifasi taglavhasi',
    )
    marketing_content = models.JSONField(
        default=dict,
        blank=True,
        help_text='Marketing sahifalari matnlari. Kalitlar: uz, ru, en.',
    )

    starter_price = models.PositiveIntegerField(
        default=0, help_text='Start plan narxi (UZS/oy)'
    )
    growth_price_monthly = models.PositiveIntegerField(
        default=99000, help_text='Pro plan oylik narxi (UZS)'
    )
    growth_price_yearly = models.PositiveIntegerField(
        default=79000, help_text='Pro plan yillik narxi (UZS/oy)'
    )
    enterprise_price_monthly = models.PositiveIntegerField(
        default=249000, help_text='Max plan oylik narxi (UZS)'
    )
    enterprise_price_yearly = models.PositiveIntegerField(
        default=199000, help_text='Max plan yillik narxi (UZS/oy)'
    )

    stats_uptime = models.CharField(
        max_length=20, default='99.9%', help_text="Uptime ko'rsatkichi"
    )
    stats_appointments = models.CharField(
        max_length=50, default='20,000+', help_text='Jami bandlovlar soni'
    )
    stats_businesses = models.CharField(
        max_length=50, default='500+', help_text='Faol bizneslar soni'
    )

    logo = models.ImageField(
        upload_to='site_logos/',
        null=True, blank=True,
        help_text='Sayt logotipi',
    )
    contact_phone = models.CharField(
        max_length=50,
        default='+998 90 123 45 67',
        help_text='Aloqa telefon raqami',
    )
    contact_email = models.CharField(
        max_length=150,
        default='support@BookFlow.com',
        help_text='Aloqa email manzili',
    )
    contact_telegram = models.CharField(
        max_length=150,
        default='https://t.me/BookFlowBot',
        help_text='Telegram bot yoki guruh havolasi',
    )
    payment_card_number = models.CharField(
        max_length=50,
        default='9860 0101 2345 6789',
        help_text="Karta raqami (to'lov uchun)",
    )
    payment_card_holder = models.CharField(
        max_length=200,
        default='SUPER ADMIN',
        help_text='Karta egasining ismi familyasi',
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'

    def __str__(self):
        return 'Site Settings'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def marketing_copy(self, language='uz'):
        language = language if language in MARKETING_COPY_DEFAULTS else 'uz'
        copy = deep_merge(
            MARKETING_COPY_DEFAULTS[language],
            self.marketing_content.get(language, {}),
        )
        if language == 'uz':
            copy['home']['title'] = self.hero_title or copy['home']['title']
            copy['home']['subtitle'] = self.hero_subtitle or copy['home']['subtitle']
        return copy

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
