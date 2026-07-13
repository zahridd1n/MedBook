from django.core.management.base import BaseCommand
from superadmin.telegram_bot import set_webhook


class Command(BaseCommand):
    help = "Superadmin Telegram bot webhookini o'rnatadi"

    def handle(self, *args, **options):
        if set_webhook():
            self.stdout.write(self.style.SUCCESS('Webhook muvaffaqiyatli o\'rnatildi'))
        else:
            self.stdout.write(self.style.ERROR('Webhook o\'rnatilmadi — token yoki internetni tekshiring'))
