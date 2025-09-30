from pathlib import Path
from converter.csv2yaml import csv_to_yaml_mappings, create_csv_template, validate_csv_before_conversion
from exporters.excel_exporter import generate_matrices_from_yaml
from exporters.html_report import generate_html_report
from core.statistics import show_statistics
from templator.curriculum_template import create_yaml_template
from utils.file_utils import check_file_exists
from interactive.filling import interactive_fill_mappings
from core.data_validator import validate_data


def handle_csv_conversion(csv_path_str):
    """Обробка конвертації CSV в YAML"""
    csv_path = Path(csv_path_str)
    
    if not csv_path.exists():
        print(f"❌ CSV файл не знайдено: {csv_path_str}")
        return False
    
    output_file = csv_path.with_suffix('.yaml')
    success = csv_to_yaml_mappings(csv_path_str, output_file=output_file)
    
    if success:
        print(f"✅ CSV конвертовано в YAML: {output_file}")
    
    return success


def handle_excel_export(yaml_file, args, base_dir):
    """Обробка експорту в Excel"""
    output_file = base_dir / Path(args.yaml_file).with_suffix(".xlsx")
    generate_matrices_from_yaml(yaml_file, output_file)
    print(f"📑 Excel файл збережено: {output_file}")


def handle_html_generation(yaml_file):
    """Обробка генерації HTML звіту"""
    if not Path(yaml_file).exists():
        print(f"❌ Файл {yaml_file} не знайдено!")
        return False
    
    generate_html_report(yaml_file)
    return True


def handle_statistics(yaml_file):
    """Обробка відображення статистики"""
    if not Path(yaml_file).exists():
        print(f"❌ Файл {yaml_file} не знайдено!")
        return False
    
    show_statistics(yaml_file)
    return True


def handle_interactive_filling(yaml_file):
    """Опція 1: Інтерактивне заповнення"""
    if not check_file_exists(yaml_file):
        print(f"❌ Файл {yaml_file} не знайдено!")
        print("📝 Створіть спочатку шаблон (опція 6)")
        return
    
    interactive_fill_mappings(yaml_file)


def handle_excel_generation(yaml_file):
    """Опція 2: Генерація Excel"""
    if not check_file_exists(yaml_file):
        print(f"❌ Файл {yaml_file} не знайдено!")
        return
    
    excel_file = input(
        f"Назва Excel файлу (Enter для {Path(yaml_file).stem}.xlsx): "
    ).strip()
    
    if not excel_file:
        excel_file = f"{Path(yaml_file).stem}.xlsx"
    
    generate_matrices_from_yaml(yaml_file, excel_file)


def handle_html_report(yaml_file):
    """Опція 3: HTML звіт"""
    if not check_file_exists(yaml_file):
        print(f"❌ Файл {yaml_file} не знайдено!")
        return
    
    generate_html_report(yaml_file)


def handle_data_validation(yaml_file):
    """Опція 5: Валідація даних"""
    if not check_file_exists(yaml_file):
        print(f"❌ Файл {yaml_file} не знайдено!")
        return
    
    validate_data(yaml_file)


def handle_template_creation(yaml_file):
    """Опція 6: Створити YAML шаблон"""
    if check_file_exists(yaml_file):
        overwrite = input(
            f"⚠️  Файл {yaml_file} вже існує. Перезаписати? (y/N): "
        )
        if overwrite.lower() != "y":
            print("❌ Скасовано")
            return
    
    create_yaml_template(yaml_file)


def handle_file_change():
    """Опція 7: Змінити робочий файл"""
    new_file = input("Введіть шлях до YAML файлу: ").strip()
    
    if new_file:
        print(f"✅ Робочий файл змінено на: {new_file}")
        return new_file
    
    return None


def handle_csv_submenu():
    """Опція 8: CSV конвертер (підменю)"""
    print("\n📋 CSV → YAML КОНВЕРТЕР")
    print("1. Створити CSV шаблон")
    print("2. Конвертувати існуючий CSV")
    print("3. Валідувати CSV файл")
    
    sub_choice = input("Оберіть дію (1-3): ").strip()
    
    if sub_choice == "1":
        handle_csv_template_creation()
    elif sub_choice == "2":
        handle_csv_file_conversion()
    elif sub_choice == "3":
        handle_csv_validation()


def handle_csv_template_creation():
    """Створення CSV шаблону"""
    template_name = input("Назва CSV шаблону (Enter для 'template.csv'): ").strip()
    
    if not template_name:
        template_name = "template.csv"
    
    create_csv_template(template_name)


def handle_csv_file_conversion():
    """Конвертація CSV файлу в YAML"""
    csv_file = input("Шлях до CSV файлу: ").strip()
    
    if not csv_file:
        print("❌ Не вказано файл")
        return
    
    if not Path(csv_file).exists():
        print(f"❌ Файл не знайдено: {csv_file}")
        return
    
    output_file = Path(csv_file).with_suffix('.yaml')
    success = csv_to_yaml_mappings(csv_file=csv_file, output_file=output_file)
    
    if success:
        print(f"✅ Конвертація завершена: {output_file}")


def handle_csv_validation():
    """Валідація CSV файлу"""
    csv_file = input("Шлях до CSV файлу для валідації: ").strip()
    
    if csv_file and Path(csv_file).exists():
        validate_csv_before_conversion(csv_file)
    else:
        print("❌ Файл не знайдено")


def handle_quick_commands(args, yaml_file, base_dir):
    """Обробка швидких команд без меню"""
    # CSV конвертація
    if args.csv:
        handle_csv_conversion(args.csv)
        return True
    
    # Excel експорт
    if args.excel:
        handle_excel_export(yaml_file, args, base_dir)
        return True
    
    # HTML звіт
    if args.html:
        handle_html_generation(yaml_file)
        return True
    
    # Статистика
    if args.stats:
        handle_statistics(yaml_file)
        return True
    
    return False

def handle_statistics_display(yaml_file):
    """Опція 4: Показати статистику"""
    if not check_file_exists(yaml_file):
        print(f"❌ Файл {yaml_file} не знайдено!")
        return
    
    show_statistics(yaml_file)