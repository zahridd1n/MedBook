import polib, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Check strings used in JavaScript context
js_keys = ['Hozir', 'daqiqa oldin', 'soat oldin', 'kun oldin',
           "Bildirishnomalar yo'q", 'Xatolik yuz berdi', 'Yuklanmoqda...',
           'Asosiy', 'Sayt', 'Biznes', 'Premium', 'Hisob']

po = polib.pofile('locale/ru/LC_MESSAGES/django.po')
for e in po:
    if e.msgid in js_keys:
        if e.msgstr and ("'" in e.msgstr):
            print(f'ISSUE: JS-unsafe single quote in translation of {e.msgid!r}')
            print(f'  RU msgstr: {e.msgstr!r}')
        else:
            print(f'OK: {e.msgid!r} -> {e.msgstr!r}')
