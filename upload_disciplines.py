import sys
import os
import requests
import argparse
import yaml

from slugify import slugify  # pip install python-slugify
from pathlib import Path
from dotenv import load_dotenv

def main():
    # Парсинг аргументів командного рядка
    parser = argparse.ArgumentParser(description='Створення сторінок WordPress з HTML файлів')
    parser.add_argument('yaml_file', help='Шлях до YAML файлу з даними дисциплін')
    parser.add_argument('--disciplines-dir', default='disciplines', 
                       help='Папка з HTML файлами (за замовчуванням: disciplines)')
    parser.add_argument('--id', default='disciplines', 
                       help='ID Батьківської сторінки')
    
    args = parser.parse_args()
    
    # Словник існуючих посилань WordPress
    WP_LINKS = {
    }
    
    # Конфігурація
    DISCIPLINES_DIR = Path(args.disciplines_dir)
    YAML_FILE = Path(args.yaml_file)
    load_dotenv()  # читає .env файл
    WP_AUTH = (os.getenv("WP_USER"), os.getenv("WP_PASSWORD"))
    WP_URL = "https://apd.ipt.kpi.ua/wp-json/wp/v2/pages"

    PARENT_ID = args.id  # <-- сюди беремо ID з аргументів

    # Перевіряємо існування файлів та папок
    if not YAML_FILE.exists():
        print(f"❌ YAML файл не знайдено: {YAML_FILE}")
        sys.exit(1)
        
    if not DISCIPLINES_DIR.exists():
        print(f"❌ Папка disciplines не знайдена: {DISCIPLINES_DIR}")
        sys.exit(1)

    # Завантажуємо YAML
    try:
        with open(YAML_FILE, encoding="utf-8") as f:
            yaml_data = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Помилка читання YAML файлу: {e}")
        sys.exit(1)

    print(f"📁 Використовуємо YAML файл: {YAML_FILE}")
    print(f"📂 Папка з HTML файлами: {DISCIPLINES_DIR}")
    print("-" * 60)

    # Перебираємо файли в папці disciplines
    for html_file in DISCIPLINES_DIR.glob("*.html"):
        if html_file.name.lower() == "index.html":
            continue  # пропускаємо індексну

        # Витягуємо код дисципліни з імені файлу
        discipline_code = html_file.stem.replace('_', ' ')
        
        # Перевіряємо, чи існує вже посилання для цієї дисципліни
        if discipline_code in WP_LINKS:
            print(f"⏭️  Дисципліна {discipline_code} вже існує: {WP_LINKS[discipline_code]}")
            continue
        
        discipline_info = yaml_data['disciplines'].get(discipline_code)

        if not discipline_info:
            print(f"❌ Дисципліна {discipline_code} не знайдена в YAML, пропускаємо...")
            continue

        # Формуємо title
        title = f"{discipline_code}: {discipline_info['name']}"

        # Читаємо HTML контент
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ Помилка читання файлу {html_file}: {e}")
            continue

        # Генеруємо slug латиницею
        slug = slugify(title)

        # Дані для WP
        data = {
            'title': title,
            'slug': slug,
            'parent': PARENT_ID,
            'content': content,
            'status': 'publish'
        }

        # Відправка POST запиту
        try:
            response = requests.post(WP_URL, json=data, auth=WP_AUTH)

            if response.status_code == 201:
                created_link = response.json().get('link')
                print(f"✅ Створено сторінку: {title} → {created_link}")
                # Додаємо нове посилання до словника (для відображення в кінці)
                WP_LINKS[discipline_code] = created_link
            else:
                print(f"❌ Помилка для {title}: {response.status_code} → {response.text}")
        except Exception as e:
            print(f"❌ Помилка запиту для {title}: {e}")

    print("-" * 60)
    print("📋 Підсумок - всі посилання:")
    for code, link in sorted(WP_LINKS.items()):
        print(f'    "{code}": "{link}",')
    print("-" * 60)

    OUTPUT_FILE = Path("wp_links.py")  # файл для збереження посилань

    # Записуємо словник у файл
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("WP_LINKS = {\n")
        for code, link in sorted(WP_LINKS.items()):
            f.write(f'    "{code}": "{link}",\n')
        f.write("}\n")

    print(f"📋 Словник WP_LINKS записано у файл {OUTPUT_FILE}")

if __name__ == "__main__":
    main()