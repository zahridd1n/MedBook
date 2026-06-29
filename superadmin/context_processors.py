from .models import SiteSettings


def site_settings(request):
    """Make SiteSettings available in all templates as `site_settings`."""
    return {'site_settings': SiteSettings.load()}
