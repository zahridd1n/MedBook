import re
from django.http import Http404
from django.conf import settings


PRIMARY_DOMAIN_PATTERN = re.compile(
    r'^(.+\.)?' + re.escape(settings.PRIMARY_DOMAIN) + r'(:\d+)?$'
)


class CustomDomainMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(':')[0].lower()

        # Skip primary domain, localhost, IP addresses
        if PRIMARY_DOMAIN_PATTERN.match(host) or host in ('localhost', '127.0.0.1', '::1') or host.startswith('10.') or host.startswith('192.168.'):
            return self.get_response(request)

        from business.models import Business
        try:
            business = Business.objects.get(custom_domain=host, domain_verified=True, is_active=True)
        except Business.DoesNotExist:
            raise Http404('Bu domen uchun biznes topilmadi')

        request.custom_business = business
        request.custom_business_slug = business.slug

        # Rewrite the path so Django routes via slug
        path = request.path_info
        if not path.startswith('/' + business.slug + '/') and path != '/' + business.slug:
            new_path = '/' + business.slug + path
            request.path_info = new_path
            request.path = new_path
            if request.META.get('SCRIPT_NAME'):
                request.path_info = request.path_info[len(request.META['SCRIPT_NAME']):]

        return self.get_response(request)
