import io
import qrcode
from qrcode.image.svg import SvgPathImage
from django.conf import settings


def get_business_url(business):
    if business.custom_domain and business.domain_verified:
        return f'https://{business.custom_domain}'
    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
    return f'{site_url.rstrip("/")}/{business.slug}/'


def generate_qr_png(business, box_size=10, border=4):
    url = get_business_url(business)
    qr = qrcode.QRCode(box_size=box_size, border=border)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf


def generate_qr_svg(business, border=1):
    url = get_business_url(business)
    factory = SvgPathImage
    img = qrcode.make(url, image_factory=factory, box_size=10, border=border)
    svg_str = img.to_string()
    buf = io.BytesIO()
    buf.write(svg_str if isinstance(svg_str, bytes) else svg_str.encode('utf-8'))
    buf.seek(0)
    return buf


SIZE_PRESETS = {
    'sticker': {'box_size': 6, 'border': 2, 'label': 'Stiker uchun (5x5 sm)'},
    'visitka': {'box_size': 10, 'border': 3, 'label': 'Vizitka uchun (3x3 sm)'},
    'reception': {'box_size': 16, 'border': 4, 'label': 'Reception uchun (A5 poster)'},
}
