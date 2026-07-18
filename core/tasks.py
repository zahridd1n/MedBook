from celery import shared_task
from django.core.cache import cache
from django.conf import settings

from core.seo import invalidate_seo_cache, invalidate_all_seo_cache, SEO_CACHE_PREFIX


@shared_task
def invalidate_business_seo_cache(business_id):
    invalidate_seo_cache(business_id)


@shared_task
def warm_business_seo_cache(business_id):
    from business.models import Business
    try:
        business = Business.objects.get(id=business_id, is_active=True)
    except Business.DoesNotExist:
        return

    from django.http import HttpRequest
    req = HttpRequest()
    req.META['HTTP_HOST'] = settings.PRIMARY_DOMAIN
    req.path = f'/{business.slug}/'
    req.build_absolute_uri = lambda uri: f"https://{settings.PRIMARY_DOMAIN}{uri or req.path}"

    from core.seo import get_seo_context
    for page_type in ['home', 'booking', 'blog_list']:
        cache_key = f'{SEO_CACHE_PREFIX}:{business.id}:{page_type}:uz'
        if not cache.get(cache_key):
            get_seo_context(req, business, page_type)


@shared_task
def generate_sitemap():
    from django.contrib.sitemaps import Sitemap
    from business.models import Business
    from blog.models import BlogPost
    from django.urls import reverse

    urls = []

    # Marketing pages
    for name in ['marketing:home', 'marketing:features', 'marketing:pricing', 'marketing:faq', 'marketing:contact', 'marketing:businesses', 'marketing:tutorials']:
        try:
            urls.append({
                'loc': f"{settings.SITE_URL.rstrip('/')}{reverse(name)}",
                'changefreq': 'monthly',
                'priority': '0.7',
            })
        except Exception:
            pass

    # Businesses
    businesses = Business.objects.filter(is_active=True).only('slug', 'updated_at')
    for b in businesses:
        urls.append({
            'loc': f"{settings.SITE_URL.rstrip('/')}/{b.slug}/",
            'lastmod': b.updated_at.isoformat() if b.updated_at else '',
            'changefreq': 'weekly',
            'priority': '0.8',
        })
        urls.append({
            'loc': f"{settings.SITE_URL.rstrip('/')}/{b.slug}/book/",
            'changefreq': 'monthly',
            'priority': '0.6',
        })
        urls.append({
            'loc': f"{settings.SITE_URL.rstrip('/')}/{b.slug}/blog/",
            'changefreq': 'weekly',
            'priority': '0.7',
        })

    # Blog posts
    posts = BlogPost.objects.filter(is_published=True).select_related('business').only('slug', 'business__slug', 'updated_at')
    for p in posts:
        urls.append({
            'loc': f"{settings.SITE_URL.rstrip('/')}/{p.business.slug}/blog/{p.slug}/",
            'lastmod': p.updated_at.isoformat() if p.updated_at else '',
            'changefreq': 'monthly',
            'priority': '0.6',
        })

    # Employees
    from employees.models import Employee
    employees = Employee.objects.filter(is_active=True, is_visible_on_public=True).select_related('business').only('id', 'business__slug')
    for e in employees:
        urls.append({
            'loc': f"{settings.SITE_URL.rstrip('/')}/{e.business.slug}/employees/{e.id}/",
            'changefreq': 'monthly',
            'priority': '0.5',
        })

    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for u in urls:
        sitemap_xml += '  <url>\n'
        sitemap_xml += f'    <loc>{u["loc"]}</loc>\n'
        if u.get('lastmod'):
            sitemap_xml += f'    <lastmod>{u["lastmod"]}</lastmod>\n'
        sitemap_xml += f'    <changefreq>{u["changefreq"]}</changefreq>\n'
        sitemap_xml += f'    <priority>{u["priority"]}</priority>\n'
        sitemap_xml += '  </url>\n'
    sitemap_xml += '</urlset>'

    cache.set('sitemap_xml', sitemap_xml, 86400)
    return len(urls)
