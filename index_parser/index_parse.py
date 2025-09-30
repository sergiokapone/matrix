import re
from pathlib import Path
from wp_links import WP_LINKS

def replace_href(match):
    code = match.group(1).replace('_', ' ').strip()
    wp_url = WP_LINKS.get(code, "#")
    return f'href="{wp_url}"'

def parse_index_links(index_file_path="disciplines/index.html"):
    """
    Заменяет href на WP ссылки для ЗО_XX / ПО_XX в указанном index.html.
    """
    index_file = Path(index_file_path)

    if not index_file.exists():
        print(f"❌ Файл {index_file} не найден")
        return

    html = index_file.read_text(encoding="utf-8")

    # regex ищет href на файлы, начинающиеся с ЗО_, ПО_ или ПВ_
    pattern = re.compile(r'href="((ЗО|ПО|ПВ)[ _]\d{2}(?:\.\d+)?)\.html"')

    html_new = pattern.sub(replace_href, html)
    index_file.write_text(html_new, encoding="utf-8")
    print(f"✅ href в {index_file} заменены на WP ссылки для ЗО_XX / ПО_XX")
