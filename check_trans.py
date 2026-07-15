import polib, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
po = polib.pofile('locale/ru/LC_MESSAGES/django.po')
issues = []
for e in po:
    if e.msgstr and ('"' in e.msgstr or "'" in e.msgstr or '<' in e.msgstr or '>' in e.msgstr):
        issues.append(f'msgid: {e.msgid!r} -> msgstr: {e.msgstr!r}')
if issues:
    for i in issues:
        print(i)
else:
    print('No problematic characters found')
print(f'\nTotal entries: {len(po)}')
