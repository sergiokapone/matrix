import re
from pathlib import Path

index_file = Path("disciplines/index.html")

from wp_links import WP_LINKS


html = index_file.read_text(encoding="utf-8")

# regex шукає href на файли, що починаються з ЗО_ або ПО_
pattern = re.compile(r'href="((ЗО|ПО|ПВ)[ _]\d{2}(?:\.\d+)?)\.html"')

def replace_href(match):
    code = match.group(1).replace('_', ' ').strip()
    print(f"DEBUG: '{code}'")  # подивитися точний текст
    wp_url = WP_LINKS.get(code, "#")
    print(f"DEBUG wp_url: '{wp_url}'")
    return f'href="{wp_url}"'

html_new = pattern.sub(replace_href, html)

index_file.write_text(html_new, encoding="utf-8")
print("✅ href у index.html замінено на WP-посилання для ЗО_XX / ПО_XX")
