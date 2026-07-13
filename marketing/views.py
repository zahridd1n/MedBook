from django.shortcuts import render
from django.db.models import Count

from superadmin.models import SiteSettings
from business.models import Business


CATEGORY_LABELS = {
    'uz': {
        'clinic': 'Klinika', 'dental': 'Stomatologiya', 'beauty': 'Go\'zallik saloni',
        'barber': 'Sartaroshxona', 'education': 'O\'quv markaz', 'auto': 'Avto xizmat', 'other': 'Boshqa',
    },
    'ru': {
        'clinic': 'Клиника', 'dental': 'Стоматология', 'beauty': 'Салон красоты',
        'barber': 'Парикмахерская', 'education': 'Учебный центр', 'auto': 'Автосервис', 'other': 'Другое',
    },
    'en': {
        'clinic': 'Clinic', 'dental': 'Dental Clinic', 'beauty': 'Beauty Salon',
        'barber': 'Barber Shop', 'education': 'Educational Center', 'auto': 'Auto Service', 'other': 'Other',
    },
}

CATEGORY_ICONS = {
    'clinic': 'hospital', 'dental': 'bandaid', 'beauty': 'stars',
    'barber': 'scissors', 'education': 'mortarboard', 'auto': 'car-front', 'other': 'grid',
}


SUPPORTED_LANGUAGES = ('uz', 'ru', 'en')


FEATURES = {
    'uz': [
        ('calendar2-week', 'Bandlovlarni boshqarish', 'Sana, vaqt, status, xizmat, xodim va mijoz ma’lumotlari bitta joyda.'),
        ('palette2', 'Brendlangan ommaviy sahifa', 'Logo, ranglar, xizmatlar, xodimlar va biznes ma’lumotlari mijozga chiroyli ko‘rinadi.'),
        ('person-badge', 'Xodimlar jadvali', 'Xodimlarni xizmatlarga biriktiring va mavjud vaqtlarni aniq ko‘rsating.'),
        ('telegram', 'Telegram xabarnomalar', 'Yangi bandlovlar va muhim o‘zgarishlar Telegram orqali keladi.'),
    ],
    'ru': [
        ('calendar2-week', 'Управление записями', 'Дата, время, статус, услуга, сотрудник и клиент в одном рабочем месте.'),
        ('palette2', 'Брендированная публичная страница', 'Логотип, цвета, услуги, сотрудники и данные бизнеса выглядят аккуратно для клиента.'),
        ('person-badge', 'Расписание сотрудников', 'Назначайте сотрудников на услуги и показывайте точную доступность.'),
        ('telegram', 'Telegram уведомления', 'Новые записи и важные изменения приходят в Telegram.'),
    ],
    'en': [
        ('calendar2-week', 'Appointment management', 'Date, time, status, service, employee, and customer details in one workspace.'),
        ('palette2', 'Branded public page', 'Logo, colors, services, employees, and business details look polished for customers.'),
        ('person-badge', 'Employee schedules', 'Assign employees to services and show accurate availability.'),
        ('telegram', 'Telegram notifications', 'New bookings and important changes arrive through Telegram.'),
    ],
}

FAQS = {
    'uz': [
        ('Bandlov sahifasini qanchada ishga tushiraman?', 'Biznes ma’lumotlari, xizmatlar va xodimlarni qo‘shsangiz, havolani shu kunning o‘zida ulashishingiz mumkin.'),
        ('Mijoz ro‘yxatdan o‘tishi kerakmi?', 'Yo‘q. Mijoz ommaviy sahifani ochib xizmat, xodim va vaqtni tanlaydi.'),
        ('Narxlar qayerdan olinadi?', 'Marketing sahifadagi Start, Pro va Max narxlari superadmin sozlamalaridagi tariflardan olinadi.'),
        ('Kontakt va logo ham bazadanmi?', 'Ha. Logo, telefon, email va Telegram havolasi SiteSettings modelidan chiqadi.'),
    ],
    'ru': [
        ('Как быстро можно запустить страницу записи?', 'После добавления данных бизнеса, услуг и сотрудников ссылку можно отправить клиентам в тот же день.'),
        ('Клиенту нужен аккаунт?', 'Нет. Клиент открывает публичную страницу и выбирает услугу, сотрудника и время.'),
        ('Откуда берутся цены?', 'Цены Start, Pro и Max на маркетинговой странице берутся из настроек superadmin.'),
        ('Контакты и логотип тоже из базы?', 'Да. Логотип, телефон, email и Telegram ссылка берутся из модели SiteSettings.'),
    ],
    'en': [
        ('How fast can I launch the booking page?', 'After adding business details, services, and employees, you can share the link the same day.'),
        ('Do customers need an account?', 'No. Customers open the public page and choose a service, employee, and time.'),
        ('Where do prices come from?', 'Start, Pro, and Max prices on the marketing page come from superadmin settings.'),
        ('Are contacts and logo database-driven too?', 'Yes. Logo, phone, email, and Telegram link come from the SiteSettings model.'),
    ],
}

PLAN_FEATURES = {
    'uz': {
        'start': ['1 xodim', '50 bandlov/oy', 'Ommaviy sahifa'],
        'pro': ['5 xodim', 'Cheksiz bandlov', 'Brending', 'Telegram'],
        'max': ['Cheksiz xodim', 'Custom CSS', 'API imkoniyati', 'Priority support'],
    },
    'ru': {
        'start': ['1 сотрудник', '50 записей/мес', 'Публичная страница'],
        'pro': ['5 сотрудников', 'Безлимитные записи', 'Брендинг', 'Telegram'],
        'max': ['Безлимитные сотрудники', 'Custom CSS', 'API возможности', 'Priority support'],
    },
    'en': {
        'start': ['1 employee', '50 bookings/month', 'Public page'],
        'pro': ['5 employees', 'Unlimited bookings', 'Branding', 'Telegram'],
        'max': ['Unlimited employees', 'Custom CSS', 'API access', 'Priority support'],
    },
}

STAT_LABELS = {
    'uz': {'uptime': 'uptime', 'appointments': 'bandlovlar', 'businesses': 'faol bizneslar'},
    'ru': {'uptime': 'uptime', 'appointments': 'записей', 'businesses': 'активных бизнесов'},
    'en': {'uptime': 'uptime', 'appointments': 'bookings', 'businesses': 'active businesses'},
}


def _language(request):
    requested = request.GET.get('lang')
    if requested in SUPPORTED_LANGUAGES:
        request.session['marketing_language'] = requested
        return requested
    return request.session.get('marketing_language', 'uz')


def _money(amount):
    if not amount:
        return '0 UZS'
    return f'{amount:,}'.replace(',', ' ') + ' UZS'


def _plans(site, copy, lang):
    from superadmin.models import PricingPlan
    plans = PricingPlan.objects.filter(is_active=True).prefetch_related('features')
    result = []
    for p in plans:
        result.append({
            'id': p.slug,
            'name': p.name,
            'price': _money(p.price_monthly),
            'yearly_price': _money(p.price_yearly) if p.price_yearly else None,
            'period': copy['pricing']['monthly'],
            'yearly_label': copy['pricing']['yearly'],
            'featured': p.is_popular,
            'features': [f.text for f in p.features.filter(is_included=True).order_by('order')],
        })
    return result


def _context(request):
    lang = _language(request)
    site = SiteSettings.load()
    copy = site.marketing_copy(lang)
    return {
        'site': site,
        'm': copy,
        'current_lang': lang,
        'languages': [('uz', 'UZ'), ('ru', 'RU'), ('en', 'EN')],
        'features': FEATURES[lang],
        'faqs': FAQS[lang],
        'plans': _plans(site, copy, lang),
        'stat_labels': STAT_LABELS[lang],
    }


def home(request):
    return render(request, 'marketing/home.html', _context(request))

def features(request):
    return render(request, 'marketing/features.html', _context(request))

def pricing(request):
    return render(request, 'marketing/pricing.html', _context(request))

def faq(request):
    return render(request, 'marketing/faq.html', _context(request))

def contact(request):
    return render(request, 'marketing/contact.html', _context(request))


def tutorials(request):
    ctx = _context(request)
    ctx['tutorial_videos'] = ctx['m']['tutorials']['videos']
    ctx['tutorial_steps'] = ctx['m']['tutorials']['steps']
    return render(request, 'marketing/tutorials.html', ctx)


def businesses_directory(request):
    """Public directory of businesses that opted in to show_in_directory."""
    lang = _language(request)
    site = SiteSettings.load()
    copy = site.marketing_copy(lang)

    category_filter = request.GET.get('category', '')
    qs = Business.objects.filter(show_in_directory=True, is_active=True).order_by('name')
    if category_filter:
        qs = qs.filter(category=category_filter)

    category_counts = (
        Business.objects
        .filter(show_in_directory=True, is_active=True)
        .values('category')
        .annotate(cnt=Count('id'))
        .order_by('category')
    )
    cat_labels = CATEGORY_LABELS[lang]
    categories = [
        {
            'value': row['category'],
            'label': cat_labels.get(row['category'], row['category']),
            'icon': CATEGORY_ICONS.get(row['category'], 'grid'),
            'count': row['cnt'],
        }
        for row in category_counts
    ]

    context = {
        'site': site,
        'm': copy,
        'current_lang': lang,
        'languages': [('uz', 'UZ'), ('ru', 'RU'), ('en', 'EN')],
        'businesses': qs,
        'categories': categories,
        'selected_category': category_filter,
        'cat_labels': cat_labels,
        'cat_icons': CATEGORY_ICONS,
        'total_count': Business.objects.filter(show_in_directory=True, is_active=True).count(),
    }
    return render(request, 'marketing/businesses.html', context)
