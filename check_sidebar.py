import re

with open('templates/base_dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

groups = re.findall(
    r'<div class="sb-group" data-group="([^"]+)">(.*?)</div>\s*</div>',
    content, re.DOTALL
)
print(f'Found {len(groups)} sidebar groups:')
for name, inner in groups:
    has_body = 'data-body' in inner
    has_arrow = 'data-arrow' in inner
    has_head = 'data-head' in inner
    onclick = 'toggleGroup' in inner
    print(f'  {name}: head={has_head} body={has_body} arrow={has_arrow} onclick={onclick}')
