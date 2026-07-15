from copy import deepcopy

from django.db import models
from django.utils import timezone
from django.urls import reverse
from business.models import Business


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
            'tutorials': "Qo'llanma",
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
        'tutorials': {
            'nav': 'Qo\'llanma',
            'home_eyebrow': 'Video qo\'llanma',
            'home_title': 'Tizimdan qanday foydalanishni o\'rganing',
            'home_subtitle': 'Bosqichma-bosqich video ko\'rsatmalar bilan BookFlow ni tezda o\'rganing.',
            'home_cta': 'Barcha videolar',
            'hero_eyebrow': 'Video qo\'llanma',
            'hero_title': 'BookFlow video qo\'llanma',
            'hero_subtitle': 'Tizimning har bir qismini video formatda o\'rganing. Ro\'yxatdan o\'tishdan boshlab, mijozlarni qabul qilishgacha.',
            'videos': [
                {
                    'title': 'Tizimga kirish va boshqaruv paneli',
                    'description': 'Ro\'yxatdan o\'tish, tizimga kirish va dashboard boshqaruvi bilan tanishing.',
                    'youtube_id': '',
                    'file_url': '',
                    'duration': '5:30',
                },
                {
                    'title': 'Xizmatlarni qo\'shish va tahrirlash',
                    'description': 'Biznesingiz xizmatlarini qo\'shish, narxlarni belgilash va kategoriyalash.',
                    'youtube_id': '',
                    'file_url': '',
                    'duration': '7:15',
                },
                {
                    'title': 'Xodimlar jadvalini sozlash',
                    'description': 'Xodimlarni xizmatlarga biriktirish va ish jadvalini belgilash.',
                    'youtube_id': '',
                    'file_url': '',
                    'duration': '6:45',
                },
                {
                    'title': 'Ommaviy bron sahifasini sozlash',
                    'description': 'Mijozlarga ko\'rinadigan bron sahifasini logo, ranglar va ma\'lumotlar bilan shaxsiylashtirish.',
                    'youtube_id': '',
                    'file_url': '',
                    'duration': '8:20',
                },
                {
                    'title': 'Bandlovlarni boshqarish',
                    'description': 'Yangi bandlovlarni qabul qilish, o\'zgartirish va bekor qilish.',
                    'youtube_id': '',
                    'file_url': '',
                    'duration': '6:00',
                },
                {
                    'title': 'Telegram xabarnomalarni ulash',
                    'description': 'Telegram botini sozlash va avtomatik xabarnomalar olish.',
                    'youtube_id': '',
                    'file_url': '',
                    'duration': '4:45',
                },
            ],
            'steps_title': 'Tizimni o\'rganish bosqichlari',
            'steps': [
                {'title': 'Ro\'yxatdan o\'ting', 'description': 'Bepul hisob yarating va tizimga kiring.'},
                {'title': 'Profilni to\'ldiring', 'description': 'Biznes nomi, manzili, logotip va aloqa ma\'lumotlarini kiriting.'},
                {'title': 'Xizmatlarni qo\'shing', 'description': 'Xizmat nomi, narxi, davomiyligi va tavsifini belgilang.'},
                {'title': 'Xodimlarni biriktiring', 'description': 'Xodimlarni xizmatlarga tayinlang va jadvalini sozlang.'},
                {'title': 'Havolani ulashing', 'description': 'Ommaviy bron sahifasini mijozlarga yuboring.'},
            ],
        },
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
            'tutorials': 'Инструкции',
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
        'tutorials': {
            'nav': 'Инструкции',
            'home_eyebrow': 'Видео инструкции',
            'home_title': 'Научитесь работать с системой',
            'home_subtitle': 'Пошаговые видеоинструкции помогут быстро освоить BookFlow.',
            'home_cta': 'Все видео',
            'hero_eyebrow': 'Видео инструкции',
            'hero_title': 'Видеоинструкции BookFlow',
            'hero_subtitle': 'Изучите каждый раздел системы в видеоформате. От регистрации до приёма клиентов.',
            'videos': [
                {
                    'title': 'Вход в систему и панель управления',
                    'description': 'Регистрация, вход и навигация по панели управления.',
                    'youtube_id': '',
                    'file_url': '',
                    'duration': '5:30',
                },
                {
                    'title': 'Добавление услуг',
                    'description': 'Добавление услуг бизнеса, установка цен и категоризация.',
                    'youtube_id': '',
                    'file_url': '',
                    'duration': '7:15',
                },
                {
                    'title': 'Расписание сотрудников',
                    'description': 'Назначение сотрудников на услуги и настройка графика работы.',
                    'youtube_id': '',
                    'file_url': '',
                    'duration': '6:45',
                },
                {
                    'title': 'Настройка публичной страницы записи',
                    'description': 'Персонализация страницы записи логотипом, цветами и информацией.',
                    'youtube_id': '',
                    'file_url': '',
                    'duration': '8:20',
                },
                {
                    'title': 'Управление записями',
                    'description': 'Приём, изменение и отмена записей клиентов.',
                    'youtube_id': '',
                    'file_url': '',
                    'duration': '6:00',
                },
                {
                    'title': 'Подключение Telegram уведомлений',
                    'description': 'Настройка Telegram бота и автоматических уведомлений.',
                    'youtube_id': '',
                    'file_url': '',
                    'duration': '4:45',
                },
            ],
            'steps_title': 'Этапы изучения системы',
            'steps': [
                {'title': 'Зарегистрируйтесь', 'description': 'Создайте бесплатную учётную запись и войдите в систему.'},
                {'title': 'Заполните профиль', 'description': 'Укажите название бизнеса, адрес, логотип и контактные данные.'},
                {'title': 'Добавьте услуги', 'description': 'Определите название, цену, длительность и описание услуги.'},
                {'title': 'Назначьте сотрудников', 'description': 'Привяжите сотрудников к услугам и настройте расписание.'},
                {'title': 'Отправьте ссылку', 'description': 'Опубликуйте публичную страницу записи для клиентов.'},
            ],
        },
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
            'tutorials': 'Tutorials',
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
        'tutorials': {
            'nav': 'Tutorials',
            'home_eyebrow': 'Video tutorials',
            'home_title': 'Learn how to use the system',
            'home_subtitle': 'Step-by-step video guides to help you master BookFlow quickly.',
            'home_cta': 'All videos',
            'hero_eyebrow': 'Video tutorials',
            'hero_title': 'BookFlow video tutorials',
            'hero_subtitle': 'Learn every part of the system in video format. From registration to accepting customers.',
            'videos': [
                {
                    'title': 'Login and dashboard overview',
                    'description': 'Registration, login, and navigating the dashboard.',
                    'youtube_id': '',
                    'file_url': '',
                    'duration': '5:30',
                },
                {
                    'title': 'Adding services',
                    'description': 'Adding business services, setting prices, and categorizing.',
                    'youtube_id': '',
                    'file_url': '',
                    'duration': '7:15',
                },
                {
                    'title': 'Employee schedules',
                    'description': 'Assigning employees to services and setting work schedules.',
                    'youtube_id': '',
                    'file_url': '',
                    'duration': '6:45',
                },
                {
                    'title': 'Setting up the public booking page',
                    'description': 'Customizing the booking page with logo, colors, and business info.',
                    'youtube_id': '',
                    'file_url': '',
                    'duration': '8:20',
                },
                {
                    'title': 'Managing appointments',
                    'description': 'Accepting, modifying, and canceling customer appointments.',
                    'youtube_id': '',
                    'file_url': '',
                    'duration': '6:00',
                },
                {
                    'title': 'Telegram notifications setup',
                    'description': 'Configuring the Telegram bot for automatic notifications.',
                    'youtube_id': '',
                    'file_url': '',
                    'duration': '4:45',
                },
            ],
            'steps_title': 'Learning roadmap',
            'steps': [
                {'title': 'Sign up', 'description': 'Create a free account and log in to the system.'},
                {'title': 'Complete your profile', 'description': 'Add business name, address, logo, and contact details.'},
                {'title': 'Add services', 'description': 'Define service name, price, duration, and description.'},
                {'title': 'Assign employees', 'description': 'Link employees to services and configure schedules.'},
                {'title': 'Share the link', 'description': 'Publish your public booking page for customers.'},
            ],
        },
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
        help_text='Sayt logotipi (qorong\'i/dark rejim uchun)',
    )
    logo_light = models.ImageField(
        upload_to='site_logos/',
        null=True, blank=True,
        help_text='Sayt logotipi (yorug\'/light rejim uchun). Bo\'sh qoldirilsa, dark logo ishlatiladi.',
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


class PricingPlan(models.Model):
    name = models.CharField(max_length=50, help_text="Tarif nomi (masalan: Start, Pro, Max)")
    slug = models.SlugField(max_length=20, unique=True, help_text="Sistemadagi ID (masalan: free, growth, enterprise)")
    description = models.CharField(max_length=200, blank=True, help_text="Qisqacha ta'rif")
    
    price_monthly = models.PositiveIntegerField(default=0, help_text="Oylik to'lov summasi (UZS)")
    price_yearly = models.PositiveIntegerField(default=0, help_text="Yillik to'lovda bir oy uchun summa (UZS)")
    
    # Biznes mantiq cheklovlari
    max_employees = models.IntegerField(null=True, blank=True, help_text="Maksimal xodimlar soni (Bo'sh bo'lsa cheksiz)")
    max_appointments_monthly = models.IntegerField(null=True, blank=True, help_text="Oylik maksimal bandlovlar (Bo'sh bo'lsa cheksiz)")
    
    allow_telegram = models.BooleanField(default=False, help_text="Telegram xabarnomalar va bot")
    allow_email = models.BooleanField(default=True, help_text="Email xabarnomalar")
    allow_custom_domain = models.BooleanField(default=False, help_text="Shaxsiy domen ulash imkoniyati")
    allow_branding = models.BooleanField(default=False, help_text="Shaxsiy brending (Logotip va hk)")
    allow_custom_css = models.BooleanField(default=False, help_text="Custom CSS imkoniyati")
    allow_google_calendar = models.BooleanField(default=False, help_text="Google Calendar sinxronizatsiyasi")
    allow_api = models.BooleanField(default=False, help_text="API va Webhooklar")
    allow_white_label = models.BooleanField(default=False, help_text="White Label (BookFlow brendini yashirish)")
    
    is_active = models.BooleanField(default=True, help_text="Aktiv tarif (Saytda ko'rinadi)")
    is_popular = models.BooleanField(default=False, help_text="Tavsiya etiladigan tarif belgisi (Mashhur)")
    order = models.PositiveIntegerField(default=0, help_text="Tartib raqami (kichigi oldin chiqadi)")

    class Meta:
        ordering = ['order']
        verbose_name = "Pricing Plan"
        verbose_name_plural = "Pricing Plans"

    def __str__(self):
        return f"{self.name} ({self.price_monthly} UZS)"

    @property
    def price_label(self):
        if self.price_monthly == 0:
            return "0 UZS"
        return f"{self.price_monthly:,} UZS".replace(",", " ")


class PricingPlanFeature(models.Model):
    plan = models.ForeignKey(PricingPlan, related_name='features', on_delete=models.CASCADE)
    text = models.CharField(max_length=200, help_text="Funksiya matni (Masalan: 'Cheksiz qabullar')")
    is_included = models.BooleanField(default=True, help_text="Ushbu tarifda bor yoki yo'q (chizib ko'rsatish uchun)")
    order = models.PositiveIntegerField(default=0, help_text="Ro'yxatdagi tartib raqami")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.plan.name} - {self.text}"


class BusinessSubscription(Business):
    class Meta:
        proxy = True
        app_label = 'superadmin'
        verbose_name = "Obuna"
        verbose_name_plural = "Obunalar"
        permissions = [
            ('manage_subscriptions', "Obunalarni boshqarish"),
            ('view_subscription_stats', "Obuna statistikasini ko'rish"),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_subscription_plan_display()})"

    @property
    def is_expired(self):
        return bool(self.subscription_end and self.subscription_end < timezone.now())

    @property
    def is_trialing(self):
        return self.subscription_status == 'trial'

    @property
    def days_until_expiry(self):
        if not self.subscription_end:
            return None
        remaining = (self.subscription_end - timezone.now()).days
        return max(0, remaining)
