"""
Management command: normalize_cities
Mavjud Business yozuvlaridagi shahar nomlarini standart yozuvga o'tkazadi.
Misol: "toshkent", "Tashkent", "TOSHKENT" → "Toshkent"

Foydalanish:
    python manage.py normalize_cities           # dry-run (o'zgartirmaydi)
    python manage.py normalize_cities --apply   # haqiqatda saqlaydi
"""
from django.core.management.base import BaseCommand
from business.models import Business
from business.forms import _CITY_LOWER_MAP


class Command(BaseCommand):
    help = "Mavjud bizneslar uchun shahar nomlarini normallashtiradi"

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Haqiqatda o\'zgartirish (bo\'lmasa dry-run)',
        )

    def handle(self, *args, **options):
        apply = options['apply']
        changed = []

        for biz in Business.objects.exclude(city='').order_by('name'):
            original = biz.city
            normalized = _CITY_LOWER_MAP.get(original.lower())
            if normalized is None:
                # Title-case qilish
                normalized = original.strip().title()

            if normalized != original:
                changed.append((biz.id, biz.name, original, normalized))
                if apply:
                    biz.city = normalized
                    biz.save(update_fields=['city'])

        if not changed:
            self.stdout.write(self.style.SUCCESS("✅ Barcha shahar nomlari allaqachon standart."))
            return

        self.stdout.write(f"\n{'DRY-RUN' if not apply else 'QOLLANDI'} — {len(changed)} ta o'zgarish:\n")
        self.stdout.write(f"{'ID':<6} {'Biznes nomi':<30} {'Eski':<20} {'Yangi'}")
        self.stdout.write("-" * 75)
        for bid, bname, old, new in changed:
            self.stdout.write(f"{bid:<6} {bname[:28]:<30} {old:<20} {new}")

        if not apply:
            self.stdout.write(
                self.style.WARNING(
                    f"\n⚠️  Haqiqatda saqlash uchun: python manage.py normalize_cities --apply"
                )
            )
        else:
            self.stdout.write(self.style.SUCCESS(f"\n✅ {len(changed)} ta biznes shahari normallashtirildi."))
