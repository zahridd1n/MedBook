from django.shortcuts import render
from django.db import models
from django.db.models import Count
from django.conf import settings

from superadmin.models import SiteSettings
from business.models import Business
from marketing.models import MarketingVideo
from core.seo import _get_site_settings, get_json_ld_html


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


def _marketing_seo(request, title, description, og_type='website'):
    site_settings = _get_site_settings()
    canonical = request.build_absolute_uri(request.path)
    og_image = site_settings.default_og_image.url if site_settings.default_og_image and hasattr(site_settings.default_og_image, 'url') else ''
    return {
        'meta_title': title,
        'meta_description': description,
        'canonical_url': canonical,
        'hreflangs': [],
        'og_title': title,
        'og_description': description,
        'og_type': og_type,
        'og_image': og_image,
        'json_ld_html': '',
        'seo_enabled': True,
        'meta_keywords': '',
    }


def _context(request):
    lang = _language(request)
    site = SiteSettings.load()
    copy = site.marketing_copy(lang)

    # Published videolarni modeldan olish (agar bo'lsa, defaultlarni bekor qiladi)
    model_videos = MarketingVideo.objects.filter(
        language=lang, is_published=True
    ).order_by('order', 'created_at')
    if model_videos.exists():
        copy['tutorials']['videos'] = [
            {
                'title': v.title,
                'description': v.description,
                'youtube_id': v.youtube_id,
                'file_url': v.file_url(),
                'duration': v.duration,
            }
            for v in model_videos
        ]

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
    ctx = _context(request)
    ctx.update(_marketing_seo(request, ctx['m']['home']['title'], ctx['m']['home']['subtitle']))
    return render(request, 'marketing/home.html', ctx)

def features(request):
    ctx = _context(request)
    ctx.update(_marketing_seo(request, f"Imkoniyatlar — BookFlow", ctx['m']['features']['subtitle']))
    return render(request, 'marketing/features.html', ctx)

def pricing(request):
    ctx = _context(request)
    ctx.update(_marketing_seo(request, f"Tariflar — BookFlow", ctx['m']['pricing']['subtitle']))
    return render(request, 'marketing/pricing.html', ctx)

def faq(request):
    ctx = _context(request)
    ctx.update(_marketing_seo(request, f"Savol-Javob — BookFlow", ctx['m']['faq']['subtitle']))
    return render(request, 'marketing/faq.html', ctx)

def contact(request):
    ctx = _context(request)
    ctx.update(_marketing_seo(request, f"Aloqa — BookFlow", ctx['m']['contact']['subtitle']))
    return render(request, 'marketing/contact.html', ctx)


def tutorials(request):
    ctx = _context(request)
    ctx['tutorial_videos'] = ctx['m']['tutorials']['videos']
    ctx['tutorial_steps'] = ctx['m']['tutorials']['steps']
    ctx.update(_marketing_seo(request, ctx['m']['tutorials']['hero_title'], ctx['m']['tutorials']['hero_subtitle']))
    return render(request, 'marketing/tutorials.html', ctx)


def businesses_directory(request):
    """Public directory of businesses that opted in to show_in_directory."""
    from django.db.models import Count, Q
    from django.utils import timezone
    from business.models import WorkingHours

    lang = _language(request)
    site = SiteSettings.load()
    copy = site.marketing_copy(lang)

    # ─── Filters from GET params ───────────────────────────────────
    category_filter = request.GET.get('category', '').strip()
    city_filter     = request.GET.get('city', '').strip()
    sort_by         = request.GET.get('sort', 'popular')
    open_today      = request.GET.get('open_today', '')
    q               = request.GET.get('q', '').strip()

    # Base queryset
    qs = (
        Business.objects
        .filter(show_in_directory=True, is_active=True, is_blocked=False)
        .prefetch_related('employees', 'working_hours')
        .annotate(employee_count=Count('employees', distinct=True))
    )

    # Search
    if q:
        qs = qs.filter(
            Q(name__icontains=q) |
            Q(about__icontains=q) |
            Q(city__icontains=q) |
            Q(address__icontains=q)
        )

    # Category filter
    if category_filter:
        qs = qs.filter(category=category_filter)

    # City filter
    if city_filter:
        qs = qs.filter(city__iexact=city_filter)

    # Open today filter
    if open_today:
        today_weekday = timezone.localdate().weekday()  # Monday=0, Sunday=6
        open_business_ids = (
            WorkingHours.objects
            .filter(day=today_weekday, is_open=True)
            .values_list('business_id', flat=True)
        )
        qs = qs.filter(id__in=open_business_ids)

    # Sorting
    if sort_by == 'newest':
        qs = qs.order_by('-created_at')
    elif sort_by == 'name':
        qs = qs.order_by('name')
    elif sort_by == 'employees':
        qs = qs.order_by('-employee_count', 'name')
    else:  # 'popular' — enterprise first, then growth, then free
        qs = qs.order_by(
            models.Case(
                models.When(subscription_plan='enterprise', then=0),
                models.When(subscription_plan='growth', then=1),
                default=2,
                output_field=models.IntegerField(),
            ),
            '-employee_count',
            'name',
        )

    # ─── Category counts for filter sidebar ────────────────────────
    category_counts = (
        Business.objects
        .filter(show_in_directory=True, is_active=True, is_blocked=False)
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

    # ─── City list for sidebar ─────────────────────────────────────
    cities = (
        Business.objects
        .filter(show_in_directory=True, is_active=True, is_blocked=False)
        .exclude(city='')
        .values_list('city', flat=True)
        .distinct()
        .order_by('city')
    )

    # ─── Open-today check per business ─────────────────────────────
    today_weekday = timezone.localdate().weekday()
    open_biz_ids = set(
        WorkingHours.objects
        .filter(day=today_weekday, is_open=True)
        .values_list('business_id', flat=True)
    )

    # ─── Build business list with badges ───────────────────────────
    from datetime import timedelta
    thirty_days_ago = timezone.now() - timedelta(days=30)
    businesses_with_meta = []
    for biz in qs:
        badges = []
        if biz.subscription_plan == 'enterprise':
            badges.append('premium')
            badges.append('verified')
        elif biz.subscription_plan == 'growth':
            badges.append('pro')
        if biz.created_at >= thirty_days_ago:
            badges.append('new')

        # Today's working hours
        today_wh = None
        for wh in biz.working_hours.all():
            if wh.day == today_weekday:
                today_wh = wh
                break

        businesses_with_meta.append({
            'biz': biz,
            'badges': badges,
            'is_open_today': biz.id in open_biz_ids,
            'today_wh': today_wh,
            'employee_count': biz.employee_count,
        })

    total_all = Business.objects.filter(show_in_directory=True, is_active=True, is_blocked=False).count()

    context = {
        'site': site,
        'm': copy,
        'current_lang': lang,
        'languages': [('uz', 'UZ'), ('ru', 'RU'), ('en', 'EN')],
        'businesses_with_meta': businesses_with_meta,
        'categories': categories,
        'cities': list(cities),
        'selected_category': category_filter,
        'selected_city': city_filter,
        'sort_by': sort_by,
        'open_today': open_today,
        'search_q': q,
        'cat_labels': cat_labels,
        'cat_icons': CATEGORY_ICONS,
        'total_count': total_all,
        'result_count': len(businesses_with_meta),
    }
    context.update(_marketing_seo(request, 'Bizneslar katalogi — BookFlow', 'Xizmat ko\'rsatuvchi bizneslarning katalogi. Klinika, salon, sartarosh va boshqalar.'))

    return render(request, 'marketing/businesses.html', context)
