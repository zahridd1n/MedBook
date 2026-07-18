import json
import logging
from django.core.cache import cache
from django.conf import settings
from django.urls import reverse
from django.utils import translation

logger = logging.getLogger(__name__)

CACHE_TTL = 3600  # 1 soat — SEO metadata tez o'zgarmaydi
SEO_CACHE_PREFIX = 'seo_ctx'

_cache_available = True


def _cache_get(key):
    global _cache_available
    if not _cache_available:
        return None
    try:
        return cache.get(key)
    except Exception as e:
        _cache_available = False
        logger.warning(f'SEO cache disabled (Redis not available): {e}')
        return None


def _cache_set(key, value, timeout):
    global _cache_available
    if not _cache_available:
        return
    try:
        cache.set(key, value, timeout)
    except Exception as e:
        _cache_available = False
        logger.warning(f'SEO cache disabled (Redis not available): {e}')


def get_canonical_url(request, business=None):
    url = request.build_absolute_uri(request.path)
    return url


def get_hreflangs(request, slug):
    lang_codes = ['uz', 'ru']
    if hasattr(settings, 'LANGUAGES'):
        lang_codes = [code for code, _ in settings.LANGUAGES]
    hreflangs = []
    base_url = request.build_absolute_uri(request.path)
    for code in lang_codes:
        if code == 'uz':
            url = base_url
        else:
            sep = '&' if '?' in base_url else '?'
            url = f'{base_url}{sep}lang={code}'
        hreflangs.append((code, url))
    return hreflangs


def get_seo_context(request, business=None, page_type='home', post=None, employee=None):
    if not business:
        return _get_empty_seo()

    lang = translation.get_language() or 'uz'
    cache_key = f'{SEO_CACHE_PREFIX}:{business.id}:{page_type}:{lang}'

    cached = _cache_get(cache_key)
    if cached:
        return cached

    ctx = _build_seo_context(request, business, page_type, post, employee)

    _cache_set(cache_key, ctx, CACHE_TTL)
    return ctx


def invalidate_seo_cache(business_id):
    pattern = f'{SEO_CACHE_PREFIX}:{business_id}:*'
    try:
        from django_redis import get_redis_connection
        r = get_redis_connection('default')
        keys = r.keys(pattern)
        if keys:
            r.delete(*keys)
    except Exception:
        cache.delete_pattern(pattern)


def invalidate_all_seo_cache():
    try:
        from django_redis import get_redis_connection
        r = get_redis_connection('default')
        keys = r.keys(f'{SEO_CACHE_PREFIX}:*')
        if keys:
            r.delete(*keys)
    except Exception:
        pass


def _get_empty_seo():
    return {
        'meta_title': '',
        'meta_description': '',
        'meta_keywords': '',
        'og_title': '',
        'og_description': '',
        'og_image': '',
        'og_type': 'website',
        'canonical_url': '',
        'hreflangs': [],
        'json_ld': [],
    }


def _build_seo_context(request, business, page_type, post=None, employee=None):
    site_settings = _get_site_settings()
    canonical = get_canonical_url(request, business)

    base_title = business.meta_title or business.name
    base_description = business.meta_description or business.about[:150] if business.about else site_settings.default_meta_description
    base_keywords = business.meta_keywords or ''
    base_og_image = _get_og_image_url(business.og_image) or _get_og_image_url(business.logo) or _get_og_image_url(site_settings.default_og_image) or ''

    meta_title = base_title
    meta_description = base_description
    og_title = base_title
    og_description = base_description
    og_image = base_og_image
    og_type = 'website'
    json_ld = []
    hreflangs = get_hreflangs(request, business.slug)

    if page_type == 'home':
        meta_title = f"{base_title} | Online Band Qilish | {business.city}" if business.city else f"{base_title} | Online Band Qilish"
        og_type = 'website'
        json_ld.append(build_jsonld_local_business(business))

        faqs = list(business.faqs.filter(is_active=True).order_by('order')[:10])
        if faqs:
            json_ld.append(build_jsonld_faq(faqs))

    elif page_type == 'employee' and employee:
        emp_title = f"{employee.name} — {business.name}"
        meta_title = employee.meta_title or emp_title if hasattr(employee, 'meta_title') and employee.meta_title else emp_title
        meta_description = employee.meta_description or employee.bio[:150] if employee.bio else meta_description
        og_title = meta_title
        og_description = meta_description
        og_type = 'profile'
        json_ld.append(build_jsonld_person(employee, business))

    elif page_type == 'blog_list':
        meta_title = f"Blog — {business.name}"
        meta_description = f"{business.name} blog sahifasi. Eng so'nggi maqolalar va yangiliklar."
        og_type = 'blog'

    elif page_type == 'blog_detail' and post:
        post_title = post.meta_title or post.title
        post_desc = post.meta_description or post.excerpt or meta_description
        meta_title = f"{post_title} — {business.name}"
        meta_description = post_desc
        og_title = meta_title
        og_description = post_desc
        og_image = _get_og_image_url(post.og_image) or _get_og_image_url(post.featured_image) or og_image
        og_type = 'article'
        json_ld.append(build_jsonld_blog_post(post, business))

    elif page_type == 'booking':
        meta_title = f"Online Band Qilish — {business.name}"
        meta_description = f"{business.name} ga onlayn qabulga yoziling. Xizmatlar, xodimlar va vaqtni tanlang."
        og_type = 'website'

    return {
        'meta_title': meta_title,
        'meta_description': meta_description,
        'meta_keywords': base_keywords,
        'og_title': og_title,
        'og_description': og_description,
        'og_image': og_image,
        'og_type': og_type,
        'canonical_url': canonical,
        'hreflangs': hreflangs,
        'json_ld': json_ld,
        'show_advanced_seo': business.can_use_advanced_seo(),
    }


def _get_site_settings():
    cache_key = 'site_settings_obj'
    cached = _cache_get(cache_key)
    if cached:
        return cached
    from superadmin.models import SiteSettings
    obj = SiteSettings.load()
    _cache_set(cache_key, obj, 300)
    return obj


def _get_og_image_url(image_field):
    if not image_field:
        return ''
    try:
        url = image_field.url
        if url.startswith('http'):
            return url
        if url.startswith('/'):
            return f"{settings.SITE_URL.rstrip('/')}{url}"
        return url
    except Exception:
        return ''


def build_jsonld_local_business(business):
    schema_type = _get_schema_type(business.category)
    data = {
        '@context': 'https://schema.org',
        '@type': schema_type,
        'name': business.name,
        'description': business.about[:300] if business.about else '',
        'url': f"{settings.SITE_URL.rstrip('/')}/{business.slug}/",
        'telephone': business.phone or '',
        'image': _get_og_image_url(business.logo) or '',
    }
    if business.address:
        data['address'] = {
            '@type': 'PostalAddress',
            'streetAddress': business.address,
            'addressLocality': business.city or '',
            'addressCountry': 'UZ',
        }
    if business.latitude and business.longitude:
        data['geo'] = {
            '@type': 'GeoCoordinates',
            'latitude': str(business.latitude),
            'longitude': str(business.longitude),
        }
    wh = list(business.working_hours.filter(is_open=True))
    if wh:
        data['openingHoursSpecification'] = [
            {
                '@type': 'OpeningHoursSpecification',
                'dayOfWeek': _day_to_schema(h.day),
                'opens': h.open_time.strftime('%H:%M') if h.open_time else '09:00',
                'closes': h.close_time.strftime('%H:%M') if h.close_time else '18:00',
            }
            for h in wh
        ]
    return data


def build_jsonld_blog_post(post, business):
    return {
        '@context': 'https://schema.org',
        '@type': 'BlogPosting',
        'headline': post.title,
        'description': post.excerpt or post.meta_description or '',
        'image': _get_og_image_url(post.featured_image) or '',
        'author': {
            '@type': 'Organization',
            'name': business.name,
        },
        'publisher': {
            '@type': 'Organization',
            'name': business.name,
            'logo': _get_og_image_url(business.logo) or '',
        },
        'datePublished': post.created_at.isoformat() if post.created_at else '',
        'dateModified': post.updated_at.isoformat() if post.updated_at else '',
        'mainEntityOfPage': {
            '@type': 'WebPage',
            '@id': f"{settings.SITE_URL.rstrip('/')}/{business.slug}/blog/{post.slug}/",
        },
    }


def build_jsonld_faq(faqs):
    return {
        '@context': 'https://schema.org',
        '@type': 'FAQPage',
        'mainEntity': [
            {
                '@type': 'Question',
                'name': faq.question,
                'acceptedAnswer': {
                    '@type': 'Answer',
                    'text': faq.answer[:500],
                },
            }
            for faq in faqs
        ],
    }


def build_jsonld_breadcrumb(items):
    item_list = []
    for i, (name, url) in enumerate(items):
        item_list.append({
            '@type': 'ListItem',
            'position': i + 1,
            'name': name,
            'item': url,
        })
    return {
        '@context': 'https://schema.org',
        '@type': 'BreadcrumbList',
        'itemListElement': item_list,
    }


def build_jsonld_person(employee, business):
    return {
        '@context': 'https://schema.org',
        '@type': 'Person',
        'name': employee.name,
        'description': employee.bio[:300] if employee.bio else '',
        'image': employee.photo.url if employee.photo and hasattr(employee.photo, 'url') else '',
        'worksFor': {
            '@type': 'Organization',
            'name': business.name,
        },
    }


def _get_schema_type(category):
    mapping = {
        'clinic': 'MedicalBusiness',
        'dental': 'DentalClinic',
        'beauty': 'BeautySalon',
        'barber': 'BarberShop',
        'education': 'EducationalOrganization',
        'auto': 'AutoRepair',
        'other': 'LocalBusiness',
    }
    return mapping.get(category, 'LocalBusiness')


def _day_to_schema(day):
    days = [
        'Monday', 'Tuesday', 'Wednesday',
        'Thursday', 'Friday', 'Saturday', 'Sunday',
    ]
    return days[day] if 0 <= day < 7 else 'Monday'


def get_json_ld_html(json_ld_list):
    if not json_ld_list:
        return ''
    html = ''
    for item in json_ld_list:
        html += f'<script type="application/ld+json">{json.dumps(item, ensure_ascii=False)}</script>\n'
    return html
