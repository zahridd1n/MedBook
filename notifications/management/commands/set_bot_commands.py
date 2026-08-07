"""
Management command to register bot commands with Telegram (setMyCommands).
Run once after deployment or when bot commands change.

Usage:
    python manage.py set_bot_commands
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Register bot commands with Telegram via setMyCommands API"

    def handle(self, *args, **options):
        from notifications.utils import set_bot_commands
        self.stdout.write("Registering Telegram bot commands...")
        result = set_bot_commands()
        if result.get('ok'):
            self.stdout.write(self.style.SUCCESS("✅ Bot commands registered successfully."))
        else:
            self.stdout.write(self.style.ERROR(f"❌ Failed: {result}"))
