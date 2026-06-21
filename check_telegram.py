import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'
django.setup()

from notifications.utils import get_bot_info, get_webhook_info
from django.conf import settings

print("=" * 45)
print("TELEGRAM BOT TEKSHIRUV")
print("=" * 45)
print(f"Token (oxirgi 6): ...{settings.TELEGRAM_BOT_TOKEN[-6:]}")
print(f"Username: {settings.TELEGRAM_BOT_USERNAME}")
print()

info = get_bot_info()
if info:
    print("✅ Bot muvaffaqiyatli topildi!")
    print(f"   Ism     : {info.get('first_name')}")
    print(f"   Username: @{info.get('username')}")
    print(f"   Bot ID  : {info.get('id')}")
else:
    print("❌ Bot topilmadi — token noto'g'ri yoki internet yo'q")

print()
wh = get_webhook_info()
if wh.get('url'):
    print(f"Webhook: {wh.get('url')}")
else:
    print("Webhook: Hali o'rnatilmagan (localhost'da normal)")
print("=" * 45)
