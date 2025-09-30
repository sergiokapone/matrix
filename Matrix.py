import argparse
import sys
from pathlib import Path
from handlers.handlers import handle_csv_conversion
from handlers.handlers import handle_interactive_filling
from handlers.handlers import handle_excel_generation
from handlers.handlers import handle_html_report
from handlers.handlers import handle_data_validation
from handlers.handlers import handle_template_creation
from handlers.handlers import handle_file_change
from handlers.handlers import handle_csv_submenu
from handlers.handlers import handle_quick_commands
from handlers.handlers import handle_statistics_display
from utils.file_utils import  check_file_exists





def parse_command_line_args():
    """Парсинг аргументів командного рядка"""
    parser = argparse.ArgumentParser(description="Генератор матриць компетенцій")
    parser.add_argument(
        "yaml_file",
        nargs="?",
        default="curriculum.yaml",
        help="Шлях до YAML файлу (за замовчуванням: curriculum.yaml)",
    )
    parser.add_argument(
        "--excel", "-x",
        action="store_true",
        help="Експортувати у Excel (файл створиться автоматично)"
    )
    parser.add_argument(
        "--html", "-t", 
        action="store_true",
        help="Згенерувати тільки HTML та вийти"
    )
    parser.add_argument(
        "--stats", "-s", 
        action="store_true", 
        help="Показати статистику та вийти"
    )
    parser.add_argument(
        "--csv", "-c", 
        help="Конвертувати CSV в YAML", 
        metavar="CSV_FILE"
    )
    
    return parser.parse_args()


def print_main_menu(yaml_file):
    """Відображення головного меню"""
    print("\n" + "=" * 60)
    print("🚀 ГЕНЕРАТОР МАТРИЦЬ КОМПЕТЕНЦІЙ")
    print("=" * 60)
    print(f"📁 Робочий файл: {yaml_file}")
    
    if not check_file_exists(yaml_file):
        print("⚠️  Файл не існує - створіть шаблон (опція 6)")
    
    print("=" * 60)
    print("1. 📝 Інтерактивне заповнення відповідностей")
    print("2. 📊 Генерація Excel матриць")
    print("3. 🌐 HTML звіт (відкрити в браузері)")
    print("4. 📈 Показати статистику")
    print("5. 🔍 Валідація даних")
    print("6. 📄 Створити новий YAML шаблон")
    print("7. 📂 Змінити робочий файл")
    print("8. 📋 CSV → YAML конвертер")
    print("0. ❌ Вихід")
    print("=" * 60)



def process_menu_choice(choice, yaml_file):
    """Обробка вибору користувача в меню"""
    if choice == "1":
        handle_interactive_filling(yaml_file)
    elif choice == "2":
        handle_excel_generation(yaml_file)
    elif choice == "3":
        handle_html_report(yaml_file)
    elif choice == "4":
        handle_statistics_display(yaml_file)
    elif choice == "5":
        handle_data_validation(yaml_file)
    elif choice == "6":
        handle_template_creation(yaml_file)
    elif choice == "7":
        new_file = handle_file_change()
        if new_file:
            return new_file
    elif choice == "8":
        handle_csv_submenu()
    elif choice == "0":
        print("👋 До побачення!")
        return "exit"
    else:
        print("❌ Невірний вибір! Оберіть від 0 до 8")
    
    return yaml_file


def run_interactive_menu(yaml_file):
    """Запуск інтерактивного меню"""
    while True:
        print_main_menu(yaml_file)
        choice = input("Оберіть опцію (0-8): ").strip()
        
        try:
            result = process_menu_choice(choice, yaml_file)
            
            if result == "exit":
                break
            elif result and result != yaml_file:
                yaml_file = result
                
        except KeyboardInterrupt:
            print("\n👋 Програму перервано користувачем")
            break
        except Exception as e:
            print(f"❌ Помилка: {e}")
        
        input("\nНатисніть Enter для продовження...")





def print_help_message():
    """Виведення довідкової інформації"""
    print("""
🚀 ГЕНЕРАТОР МАТРИЦЬ КОМПЕТЕНЦІЙ

Використання:
  python matrix2.py                          # Інтерактивне меню (curriculum.yaml)
  python matrix2.py bachelor.yaml           # Інтерактивне меню (bachelor.yaml)
  python matrix2.py bachelor.yaml --excel   # Тільки Excel
  python matrix2.py bachelor.yaml --html    # Тільки HTML
  python matrix2.py bachelor.yaml --stats   # Тільки статистика
  python matrix2.py --csv mappings.csv      # Конвертувати CSV в YAML

Приклади:
  python matrix2.py bachelor.yaml -x
  python matrix2.py master.yaml -t  
  python matrix2.py curriculum.yaml -s
  python matrix2.py -c data/mappings.csv
    """)


def main_menu():
    """Головна функція програми"""
    # Обробка --help
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h", "help"]:
        print_help_message()
        sys.exit(0)
    
    # Парсинг аргументів
    args = parse_command_line_args()
    yaml_file = Path("data") / args.yaml_file
    base_dir = Path(__file__).parent.resolve()
    
    # Швидкі команди
    if handle_quick_commands(args, yaml_file, base_dir):
        return
    
    # Інтерактивне меню
    run_interactive_menu(yaml_file)


if __name__ == "__main__":
    main_menu()