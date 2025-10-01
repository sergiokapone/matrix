import yaml
from pathlib import Path
import re

def parse_index_links(index_file_path="disciplines/index.html", data_yaml=None):
    """
    Подставляет WP ссылки в index.html из YAML.
    Проверяет year и degree перед заменой.
    """
    index_file = Path(index_file_path)
    if not index_file.exists():
        print(f"❌ Файл {index_file} не найден")
        return
    
    data_yaml_stem = Path(data_yaml).stem
    wp_links_yaml = Path("wp_links") / f"wp_links_{data_yaml_stem}.yaml"

    # Загружаем WP ссылки из YAML
    with open(wp_links_yaml, encoding="utf-8") as f:
        wp_data = yaml.safe_load(f)
    wp_links = wp_data.get("links", {})
    wp_year = wp_data.get("year", "")
    wp_degree = wp_data.get("degree", "")

    # Проверяем соответствие метаданных с основным YAML (если указан)
    if data_yaml:
        with open(data_yaml, encoding="utf-8") as f:
            meta_data = yaml.safe_load(f)
        year = meta_data.get("metadata", {}).get("year", "")
        degree = meta_data.get("metadata", {}).get("degree", "")
        if wp_year != year or wp_degree != degree:
            print(f"❌ Метаданные не совпадают: WP ({wp_year}/{wp_degree}) vs YAML ({year}/{degree}). Парсинг отменен.")
            return

    html = index_file.read_text(encoding="utf-8")
    pattern = re.compile(r'href="((ЗО|ПО|ПВ)[ _]\d{2}(?:\.\d+)?)\.html"')

    def replace_href(match):
        code = match.group(1).replace('_', ' ').strip()
        wp_url = wp_links.get(code, "#")
        return f'href="{wp_url}"'

    html_new = pattern.sub(replace_href, html)
    index_file.write_text(html_new, encoding="utf-8")
    print(f"✅ href в {index_file} заменены на WP ссылки для ЗО_XX / ПО_XX")
