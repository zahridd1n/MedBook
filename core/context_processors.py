from django.conf import settings


def global_seo_defaults(request):
    from core.seo import _get_site_settings
    ss = _get_site_settings()
    return {
        'site_settings': ss,
        'global_default_meta_description': ss.default_meta_description or '',
        'global_default_og_image': ss.default_og_image.url if ss.default_og_image and hasattr(ss.default_og_image, 'url') else '',
        'google_site_verification': ss.google_site_verification or '',
        'yandex_verification': ss.yandex_verification or '',
        'site_url': settings.SITE_URL,
        'primary_domain': settings.PRIMARY_DOMAIN,
    }
