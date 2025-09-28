#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import yaml
import requests
from requests.auth import HTTPBasicAuth
from jinja2 import Environment, FileSystemLoader
import os
from datetime import datetime
import re
from dotenv import load_dotenv

# Конфігурація
WP_SITE_URL = "https://apd.ipt.kpi.ua"
load_dotenv()  # Завантаження змінних оточення з .env файлу
WP_AUTH = (os.getenv("WP_USER"), os.getenv("WP_PASSWORD"))
WP_URL = "https://apd.ipt.kpi.ua/wp-json/wp/v2/pages"

def update_wordpress_page(content, page_id=None, site_url=None):
    """Оновлення сторінки WordPress"""
    if site_url is None:
        site_url = WP_SITE_URL
        
    url = f"{site_url}/wp-json/wp/v2/pages/{page_id}"
    # auth = HTTPBasicAuth(WP_USERNAME, WP_PASSWORD)
    
    data = {
        'content': content,
        'status': 'publish'
    }
    
    check_response = requests.get(WP_URL, auth=WP_AUTH)

    if check_response.status_code == 200:
        existing_pages = check_response.json()
        if existing_pages:
            # page_id = existing_pages[0]['id']
            print(f"♻️ Оновлюємо існуючу сторінку з id={page_id})")

            # Оновлюємо сторінку через POST (бо PUT/DELETE заборонені сервером)
            update_url = f"{WP_URL}/{page_id}"
            update_response = requests.post(update_url, json=data, auth=WP_AUTH)

            if update_response.status_code == 200:
                created_link = update_response.json().get('link')
                print(f"✅ Оновлено сторінку: {created_link}")
            else:
                print(f"❌ Помилка оновлення: {update_response.status_code} → {update_response.text}")

def load_yaml_data(yaml_file=None):
    """Завантаження даних з YAML"""
    with open(yaml_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def prepare_disciplines(disciplines):
    """Підготовка дисциплін для шаблону"""
    general = []
    professional = []
    
    for code in sorted(disciplines.keys(), key=lambda x: int(re.findall(r'\d+', x)[0])):
        discipline = disciplines[code]
        
        # Форматування посилання
        name = discipline['name']

        
        item = {
            'code': code,
            'name': name,
            'credits': discipline.get('credits', 'N/A'),
            'control': discipline.get('control', 'N/A'),
            'syllabus_url': discipline.get('syllabus_url'),
            'description': discipline.get('description', ''),
            'lecturer': discipline.get('lecturer'),
            'subdisciplines': discipline.get('subdisciplines', {}),
        }
        
        if code.startswith('ЗО'):
            general.append(item)
        elif code.startswith('ПО'):
            # Перевіряємо чи це дослідницький компонент
            professional.append(item)
    
    return general, professional

def generate_content():
    """Генерація HTML контенту"""
    # Завантажуємо дані
    data = load_yaml_data()
    metadata = data.get('metadata', {})
    disciplines = data.get('disciplines', {})
    
    # Підготовуємо дисципліни
    general, professional = prepare_disciplines(disciplines)
    
    # Налаштовуємо Jinja2
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('syllabus_page.html')
    
    # Контекст для шаблону
    context = {
        'metadata': metadata,
        'current_date': datetime.now().strftime('%d.%m.%Y'),
        'general_disciplines': general,
        'professional_disciplines': professional
    }
    
    return template.render(context)


def main():
    """Головна функція з CLI опціями"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Простий генератор силабусів',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Приклади:
  python syllabi_generator.py                    # Звичайний запуск
  python syllabi_generator.py --preview-only     # Тільки превью
  python syllabi_generator.py --page-id 123      # Кастомний ID сторінки
  python syllabi_generator.py --yaml data/test.yaml  # Інший YAML файл
        '''
    )
    
    parser.add_argument('--preview-only', '-p', 
                       action='store_true',
                       help='Тільки створити превью, не оновлювати WordPress')
    
    parser.add_argument('--page-id', 
                       type=int, 
                       help=f'ID сторінки WordPress')
    
    parser.add_argument('--yaml', 
                       default='data/program_data.yaml',
                       help='Шлях до YAML файлу (за замовчуванням: data/program_data.yaml)')
    
    parser.add_argument('--template', 
                       default='templates/syllabus_template.html',
                       help='Шлях до шаблону (за замовчуванням: templates/syllabus_template.html)')
    
    parser.add_argument('--site-url', 
                       default=WP_SITE_URL,
                       help=f'URL сайту (за замовчуванням: {WP_SITE_URL})')
    
    parser.add_argument('--preview-file', 
                       default='preview.html',
                       help='Ім\'я файлу превью (за замовчуванням: preview.html)')
    

    
    args = parser.parse_args()
    
    print("🚀 Генерація силабусів...")
    print(f"📁 YAML файл: {args.yaml}")
    print(f"📄 Шаблон: {args.template}")
    
    try:
        # Генеруємо контент з параметрами з CLI
        content = generate_content_with_template(args.template, args.yaml)
        print("📝 Контент згенеровано")
        
        # Збереження превью
        with open(args.preview_file, 'w', encoding='utf-8') as f:
            f.write(f'<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Превью силабусів</title></head><body>{content}</body></html>')
        print(f"👀 Превью збережено в {args.preview_file}")
        
        # Оновлення WordPress (якщо не тільки превью)
        if not args.preview_only:
            print(f"🌐 Оновлення сторінки ID: {args.page_id}")
            success = update_wordpress_page(content, args.page_id, args.site_url)
            if success:
                print("🎉 Готово!")
        else:
            print("📋 Режим тільки превью - WordPress не оновлюється")
        
    except Exception as e:
        print(f"❌ Помилка: {e}")
        exit(1)

def generate_content_with_template(template_path, yaml_file=None):
    """Генерація HTML контенту з кастомним шаблоном"""
    # Завантажуємо дані
    data = load_yaml_data(yaml_file)
    metadata = data.get('metadata', {})
    disciplines = data.get('disciplines', {})
    
    # Підготовуємо дисципліни
    general, professional = prepare_disciplines(disciplines)
    
    # Налаштовуємо Jinja2 з кастомним шляхом
    import os
    template_dir = os.path.dirname(template_path)
    template_name = os.path.basename(template_path)
    
    env = Environment(loader=FileSystemLoader(template_dir or '.'))
    template = env.get_template(template_name)
    
    # Контекст для шаблону
    context = {
        'page_title': 'Силабуси освітньо-наукової програми підготовки магістрів',
        'metadata': metadata,
        'current_date': datetime.now().strftime('%d.%m.%Y'),
        'general_disciplines': general,
        'professional_disciplines': professional, 
    }
    
    return template.render(context)

if __name__ == "__main__":
    main()