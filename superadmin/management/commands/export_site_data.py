import os
import json
import shutil
from datetime import datetime
from django.core.management.base import BaseCommand
from django.core import serializers
from django.conf import settings
from superadmin.models import SiteSettings, PricingPlan, PricingPlanFeature


class Command(BaseCommand):
    help = "Superadmin malumotlari (tariflar, sayt sozlamalari, fayllar)ni eksport qiladi"

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            default=None,
            help='Eksport papka manzili (default: deploy/site_data_<sana>)',
        )

    def handle(self, *args, **options):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = options['output'] or os.path.join(settings.BASE_DIR, 'deploy', f'site_data_{timestamp}')

        os.makedirs(output_dir, exist_ok=True)

        # 1. Superadmin modellarini fixture qilib eksport qilish
        models = [SiteSettings, PricingPlan, PricingPlanFeature]
        fixture_data = []
        for model in models:
            fixture_data.extend(
                json.loads(serializers.serialize('json', model.objects.all()))
            )

        fixture_path = os.path.join(output_dir, 'superadmin_fixture.json')
        with open(fixture_path, 'w', encoding='utf-8') as f:
            json.dump(fixture_data, f, ensure_ascii=False, indent=2)
        self.stdout.write(self.style.SUCCESS(f'Fixture yaratildi: {fixture_path} ({len(fixture_data)} ta obyekt)'))

        # 2. Media fayllarni nusxalash
        media_root = settings.MEDIA_ROOT
        media_dir = os.path.join(output_dir, 'media')
        copied_files = []

        for obj in SiteSettings.objects.all():
            if obj.logo:
                src = os.path.join(media_root, obj.logo.name)
                if os.path.exists(src):
                    dst = os.path.join(media_dir, obj.logo.name)
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.copy2(src, dst)
                    copied_files.append(obj.logo.name)
                    self.stdout.write(f'  Media nusxalandi: {obj.logo.name}')

        self.stdout.write(self.style.SUCCESS(f'Media fayllar nusxalandi ({len(copied_files)} ta)'))

        # 3. README yozish
        readme = f"""# BookFlow - Sayt malumotlari eksporti
Sana: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Serverni sozlash:

1. Media fayllarni serverga yuklash:
   rsync -avz media/ user@server:/path/to/project/media/

2. Fixtureni serverda yuklash:
   python manage.py loaddata superadmin_fixture.json

3. Yoki bitta buyruq bilan PostgreSQL ga to'g'ridan-to'g'ri import:
   python manage.py loaddata superadmin_fixture.json --database=default
"""
        readme_path = os.path.join(output_dir, 'README.txt')
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme)
        self.stdout.write(self.style.SUCCESS(f'README yozildi: {readme_path}'))

        # 4. ZIP qilish
        zip_path = output_dir + '.zip'
        shutil.make_archive(output_dir, 'zip', output_dir)
        self.stdout.write(self.style.SUCCESS(f'ZIP paket yaratildi: {zip_path}'))

        self.stdout.write(self.style.SUCCESS(f'\n{"="*50}'))
        self.stdout.write(self.style.SUCCESS(f'  Bajarildi! Paket: {zip_path}'))
        self.stdout.write(self.style.SUCCESS(f'  Serverda: python manage.py loaddata superadmin_fixture.json'))
        self.stdout.write(self.style.SUCCESS(f'{"="*50}'))
