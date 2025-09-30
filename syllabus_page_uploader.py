#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from core.yaml_handler import load_yaml_data
from core.wp_uploader import update_wordpress_page
from core.wp_uploader import WP_URL


YAML_LECTURERS = Path("data") / "lecturers.yaml"


def load_lecturers_data():
    """Завантаження даних лекторів"""
    return load_yaml_data(YAML_LECTURERS)


def extract_discipline_code_number(code):
    """Витягує номер з коду дисципліни для сортування"""
    numbers = re.findall(r'\d+', code)
    return int(numbers[0]) if numbers else 0


def enrich_discipline_with_lecturer(discipline, lecturers):
    """Додає повні дані лектора до дисципліни"""
    if "lecturer_id" in discipline:
        lecturer_id = discipline["lecturer_id"]
        discipline["lecturer"] = lecturers.get(lecturer_id)
    return discipline


def create_discipline_item(code, discipline):
    """Створює словник з даними дисципліни для шаблону"""
    return {
        'code': code,
        'name': discipline['name'],
        'credits': discipline.get('credits', 'N/A'),
        'control': discipline.get('control', 'N/A'),
        'syllabus_url': discipline.get('syllabus_url'),
        'description': discipline.get('description', ''),
        'lecturer': discipline.get('lecturer'),
        'subdisciplines': discipline.get('subdisciplines', {}),
    }


def categorize_discipline(code, item, general, professional, elevative):
    """Розподіляє дисципліну по категоріях"""
    if code.startswith('ЗО'):
        general.append(item)
    elif code.startswith('ПО'):
        professional.append(item)
    elif code.startswith('ПВ'):
        elevative.append(item)


def prepare_disciplines(disciplines):
    """Підготовка дисциплін для шаблону"""
    general = []
    professional = []
    elevative = []

    lecturers = load_lecturers_data()
    
    sorted_codes = sorted(disciplines.keys(), key=extract_discipline_code_number)
    
    for code in sorted_codes:
        discipline = disciplines[code]
        discipline = enrich_discipline_with_lecturer(discipline, lecturers)
        item = create_discipline_item(code, discipline)
        categorize_discipline(code, item, general, professional, elevative)
            
    return general, professional, elevative


def load_program_data(yaml_file):
    """Завантаження даних програми з YAML"""
    data = load_yaml_data(yaml_file)
    metadata = data.get('metadata', {})
    disciplines = data.get('disciplines', {}) | data.get('elevative_disciplines', {})
    return metadata, disciplines


def setup_jinja_environment(template_path):
    """Налаштування Jinja2 Environment"""
    template_dir = os.path.dirname(template_path)
    template_name = os.path.basename(template_path)
    env = Environment(loader=FileSystemLoader(template_dir or '.'))
    return env, template_name


def create_template_context(metadata, general, professional, elevate):
    """Створення контексту для шаблону"""
    return {
        'page_title': 'Силабуси освітньо-наукової програми підготовки магістрів',
        'metadata': metadata,
        'current_date': datetime.now().strftime('%d.%m.%Y'),
        'general_disciplines': general,
        'professional_disciplines': professional, 
        'elevate_disciplines': elevate, 
    }


def generate_content_with_template(template_path, yaml_file=None):
    """Генерація HTML контенту з кастомним шаблоном"""
    metadata, disciplines = load_program_data(yaml_file)
    general, professional, elevate = prepare_disciplines(disciplines)
    
    env, template_name = setup_jinja_environment(template_path)
    template = env.get_template(template_name)
    
    context = create_template_context(metadata, general, professional, elevate)
    
    return template.render(context)


def save_preview_file(content, preview_file):
    """Збереження превью HTML файлу"""
    html_wrapper = (
        f'<!DOCTYPE html>'
        f'<html>'
        f'<head><meta charset="UTF-8"><title>Превью силабусів</title></head>'
        f'<body>{content}</body>'
        f'</html>'
    )
    
    with open(preview_file, 'w', encoding='utf-8') as f:
        f.write(html_wrapper)
    
    print(f"👀 Превью збережено в {preview_file}")


def upload_to_wordpress(content, page_id, site_url):
    """Завантаження контенту на WordPress"""
    print(f"🌐 Оновлення сторінки ID: {page_id}")
    success = update_wordpress_page(content, page_id, site_url)
    if success:
        print("🎉 Готово!")
    return success


def parse_arguments():
    """Парсинг аргументів командного рядка"""
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
                       default=WP_URL,
                       help=f'URL сайту (за замовчуванням: {WP_URL})')
    
    parser.add_argument('--preview-file', 
                       default='preview.html',
                       help='Ім\'я файлу превью (за замовчуванням: preview.html)')
    
    return parser.parse_args()


def print_generation_info(args):
    """Виведення інформації про генерацію"""
    print("🚀 Генерація силабусів...")
    print(f"📁 YAML файл: {args.yaml}")
    print(f"📄 Шаблон: {args.template}")


def handle_preview_only_mode():
    """Обробка режиму тільки превью"""
    print("📋 Режим тільки превью - WordPress не оновлюється")


def process_syllabi_generation(args):
    """Основна логіка генерації силабусів"""
    print_generation_info(args)
    
    content = generate_content_with_template(args.template, args.yaml)
    print("📝 Контент згенеровано")
    
    save_preview_file(content, args.preview_file)
    
    if not args.preview_only:
        upload_to_wordpress(content, args.page_id, args.site_url)
    else:
        handle_preview_only_mode()


def main():
    """Головна функція з CLI опціями"""
    args = parse_arguments()
    
    try:
        process_syllabi_generation(args)
    except Exception as e:
        print(f"❌ Помилка: {e}")
        exit(1)


if __name__ == "__main__":
    main()