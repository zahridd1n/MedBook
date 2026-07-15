import logging
import sys
from django.core.management.base import BaseCommand
from django.conf import settings
from superadmin.telegram_bot import _bot_request, get_admins, send_message

logger = logging.getLogger(__name__)

# Fix windows unicode
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


class Command(BaseCommand):
    help = "Superadmin Telegram botni sinash — test xabar yuboradi"

    def handle(self, *args, **options):
        token = getattr(settings, 'SUPERADMIN_BOT_TOKEN', '')
        if not token:
            self.stdout.write(self.style.ERROR('SUPERADMIN_BOT_TOKEN .env da sozlanmagan'))
            return

        self.stdout.write(f'Token (oxirgi 4): ...{token[-4:]}')

        # 1. Bot info
        self.stdout.write('\n1. Bot ma\'lumotlari tekshirilmoqda...')
        info = _bot_request('getMe')
        if info and info.get('ok'):
            bot = info['result']
            self.stdout.write(self.style.SUCCESS(f'   OK Bot: @{bot.get("username")} ({bot.get("first_name")})'))
        else:
            self.stdout.write(self.style.ERROR(f'   Xatolik Bot topilmadi: {info}'))
            self.stdout.write('   -> Token noto\'g\'ri yoki internet yo\'q')
            return

        # 2. Admins
        admins = get_admins()
        self.stdout.write(f'\n2. Admin chat ID lar: {admins if admins else "— (bo\'sh)"}')
        if not admins:
        self.stdout.write(self.style.WARNING('   WARNING SUPERADMIN_CHAT_IDS .env da sozlanmagan'))
        self.stdout.write('   Masalan: SUPERADMIN_CHAT_IDS=123456789,987654321')

        # 3. Test message
        self.stdout.write('\n3. Test xabar yuborilmoqda...')
        for chat_id in admins:
            result = send_message(
                chat_id,
                '<b>Test xabar</b>\n\n'
                'Agar bu xabarni ko\'rayotgan bo\'lsangiz, bot to\'g\'ri sozlangan.\n\n'
                f'Chat ID: <code>{chat_id}</code>\n'
                f'Server: {getattr(settings, "SITE_URL", "?")}'
            )
            if result and result.get('ok'):
                self.stdout.write(self.style.SUCCESS(f'   OK {chat_id} ga xabar yuborildi'))
            else:
                self.stdout.write(self.style.ERROR(f'   Xatolik {chat_id} ga yuborilmadi: {result}'))
                if result and not result.get('ok'):
                    desc = result.get('description', '')
                    self.stdout.write(f'      Sabab: {desc}')
