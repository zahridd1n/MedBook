"""
Barcha template va Python fayllarida tarif nomlarini
Start / Pro / Max ga standartlashtiradi.
"""
import os, pathlib, re

ROOT = pathlib.Path(r'E:\projects\booking')

# (eski pattern, yangi matn) — regex replacement juftlari
REPLACEMENTS = [
    # Uzbek uzun nomlar
    (r"Boshlang['']ich\s*\(free\)",  "Start"),
    (r"Boshlang['']ich",             "Start"),
    (r"O['']sish\s*\(Pro\)",         "Pro"),
    (r"O['']sish\s*/\s*Pro",         "Pro"),
    (r"O['']sish",                   "Pro"),
    (r"Max\s*\(Max\)",        "Max"),
    (r"Max\s*/\s*Max",        "Max"),
    (r"Max",                  "Max"),
    # Comment satrlari ichida ham
    (r"#\s*──\s*Boshlang['']ich.*──", "# ── Start (free) ──"),
    (r"#\s*──\s*O['']sish.*──",       "# ── Pro (growth) ──"),
    (r"#\s*──\s*Max.*──",      "# ── Max (enterprise) ──"),
]

EXTS = {'.html', '.py'}
SKIP_DIRS = {'.venv', '__pycache__', 'migrations', 'staticfiles', 'media', '.git'}

changed_files = []

for path in ROOT.rglob('*'):
    if path.is_dir():
        continue
    if any(part in SKIP_DIRS for part in path.parts):
        continue
    if path.suffix not in EXTS:
        continue

    try:
        original = path.read_text(encoding='utf-8')
    except Exception:
        continue

    text = original
    for pattern, replacement in REPLACEMENTS:
        text = re.sub(pattern, replacement, text)

    if text != original:
        path.write_text(text, encoding='utf-8')
        changed_files.append(str(path.relative_to(ROOT)))

print(f"✅ {len(changed_files)} fayl o'zgartirildi:")
for f in changed_files:
    print(f"   {f}")
