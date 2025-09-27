import argparse
import sys
from pathlib import Path
from exporters.excel_exporter import generate_matrices_from_yaml
from exporters.html_report import generate_html_report
from core.statistics import show_statistics
from core.data_validator import validate_data
from interactive.filling import interactive_fill_mappings
from templator.curriculum_template import create_yaml_template
from converter.csv2yaml import csv_to_yaml_mappings, create_csv_template, validate_csv_before_conversion


def main_menu():
    """
    Головне меню програми
    """
    # Парсинг аргументів командного рядка
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
        "--html", "-t", help="Згенерувати тільки HTML та вийти", action="store_true"
    )
    parser.add_argument(
        "--stats", "-s", action="store_true", help="Показати статистику та вийти"
    )
    parser.add_argument(
        "--csv", "-c", help="Конвертувати CSV в YAML", metavar="CSV_FILE"
    )

    args = parser.parse_args()
    # yaml_file = args.yaml_file
    yaml_file = Path("data") / args.yaml_file

    base_dir = Path(__file__).parent.resolve()

    # Швидкі команди без меню

    # Швидка CSV конвертація
    if args.csv:
        csv_path = Path(args.csv)
        if not csv_path.exists():
            print(f"❌ CSV файл не знайдено: {args.csv}")
            return
        
        output_file = csv_path.with_suffix('.yaml')
        success = csv_to_yaml_mappings(args.csv, output_file=output_file)
        
        if success:
            print(f"✅ CSV конвертовано в YAML: {output_file}")
        return

    if args.excel:

        # Автоматичне ім’я Excel-файлу
        output_file = base_dir / Path(args.yaml_file).with_suffix(".xlsx")


        generate_matrices_from_yaml(yaml_file, output_file)
        print(f"📑 Excel файл збережено: {output_file}")
        return


    if args.html:
        if not Path(yaml_file).exists():
            print(f"❌ Файл {yaml_file} не знайдено!")
            return
        generate_html_report(yaml_file)
        return

    if args.stats:
        if not Path(yaml_file).exists():
            print(f"❌ Файл {yaml_file} не знайдено!")
            return
        show_statistics(yaml_file)
        return

    # Інтерактивне меню
    while True:
        print("\n" + "=" * 60)
        print("🚀 ГЕНЕРАТОР МАТРИЦЬ КОМПЕТЕНЦІЙ")
        print("=" * 60)
        print(f"📁 Робочий файл: {yaml_file}")
        if not Path(yaml_file).exists():
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

        choice = input("Оберіть опцію (0-8): ").strip()

        try:
            if choice == "1":
                if not Path(yaml_file).exists():
                    print(f"❌ Файл {yaml_file} не знайдено!")
                    print("📝 Створіть спочатку шаблон (опція 6)")
                else:
                    interactive_fill_mappings(yaml_file)

            elif choice == "2":
                if not Path(yaml_file).exists():
                    print(f"❌ Файл {yaml_file} не знайдено!")
                else:
                    excel_file = input(
                        f"Назва Excel файлу (Enter для {Path(yaml_file).stem}.xlsx): "
                    ).strip()
                    if not excel_file:
                        excel_file = f"{Path(yaml_file).stem}.xlsx"
                    generate_matrices_from_yaml(yaml_file, excel_file)

            elif choice == "3":
                if not Path(yaml_file).exists():
                    print(f"❌ Файл {yaml_file} не знайдено!")
                else:
                    generate_html_report(yaml_file)

            elif choice == "4":
                if not Path(yaml_file).exists():
                    print(f"❌ Файл {yaml_file} не знайдено!")
                else:
                    show_statistics(yaml_file)

            elif choice == "5":
                if not Path(yaml_file).exists():
                    print(f"❌ Файл {yaml_file} не знайдено!")
                else:
                    validate_data(yaml_file)

            elif choice == "6":
                if Path(yaml_file).exists():
                    overwrite = input(
                        f"⚠️  Файл {yaml_file} вже існує. Перезаписати? (y/N): "
                    )
                    if overwrite.lower() != "y":
                        print("❌ Скасовано")
                        continue
                create_yaml_template(yaml_file)

            elif choice == "7":
                new_file = input("Введіть шлях до YAML файлу: ").strip()
                if new_file:
                    yaml_file = new_file
                    print(f"✅ Робочий файл змінено на: {yaml_file}")
     
            elif choice == "8":
                print("\n📋 CSV → YAML КОНВЕРТЕР")
                print("1. Створити CSV шаблон")
                print("2. Конвертувати існуючий CSV")
                print("3. Валідувати CSV файл")
                
                sub_choice = input("Оберіть дію (1-3): ").strip()
                
                if sub_choice == "1":
                    template_name = input("Назва CSV шаблону (Enter для 'template.csv'): ").strip()
                    if not template_name:
                        template_name = "template.csv"
                    create_csv_template(template_name)
                    
                elif sub_choice == "2":
                    csv_file = input("Шлях до CSV файлу: ").strip()
                    if not csv_file:
                        print("❌ Не вказано файл")
                        continue
                    
                    if not Path(csv_file).exists():
                        print(f"❌ Файл не знайдено: {csv_file}")
                        continue
                    
                    output_file = Path(csv_file).with_suffix('.yaml')
                    success = csv_to_yaml_mappings(csv_file=csv_file, output_file=output_file)
                    
                    if success:
                        print(f"✅ Конвертація завершена: {output_file}")
                        
                elif sub_choice == "3":
                    csv_file = input("Шлях до CSV файлу для валідації: ").strip()
                    if csv_file and Path(csv_file).exists():
                        validate_csv_before_conversion(csv_file)
                    else:
                        print("❌ Файл не знайдено")

            elif choice == "0":
                print("👋 До побачення!")
                break

            else:
                print("❌ Невірний вибір! Оберіть від 0 до 7")

        except KeyboardInterrupt:
            print("\n👋 Програму перервано користувачем")
            break
        except Exception as e:
            print(f"❌ Помилка: {e}")

        input("\nНатисніть Enter для продовження...")


if __name__ == "__main__":
    # Додаємо приклади використання
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h", "help"]:
        print("""
🚀 ГЕНЕРАТОР МАТРИЦЬ КОМПЕТЕНЦІЙ

Використання:
  python matrix2.py                          # Інтерактивне меню (curriculum.yaml)
  python matrix2.py bachelor.yaml           # Інтерактивне меню (bachelor.yaml)
  python matrix2.py bachelor.yaml --excel bachelor.xlsx   # Тільки Excel
  python matrix2.py bachelor.yaml --html                  # Тільки HTML
  python matrix2.py bachelor.yaml --stats                 # Тільки статистика

Приклади:
  python matrix2.py bachelor.yaml -e bachelor_matrices.xlsx
  python matrix2.py master.yaml -h  
  python matrix2.py curriculum.yaml -s
        """)
        sys.exit(0)

    main_menu()
