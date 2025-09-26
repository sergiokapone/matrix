import argparse
import sys
from pathlib import Path
from exporters.excel_exporter import generate_matrices_from_yaml
from exporters.html_report import generate_html_report


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
    parser.add_argument("--excel", "-e", help="Згенерувати тільки Excel та вийти")
    parser.add_argument(
        "--html", "-t", help="Згенерувати тільки HTML та вийти", action="store_true"
    )
    parser.add_argument(
        "--stats", "-s", action="store_true", help="Показати статистику та вийти"
    )

    args = parser.parse_args()
    # yaml_file = args.yaml_file
    yaml_file = Path("data") / args.yaml_file
    # Швидкі команди без меню
    if args.excel:
        if not Path(yaml_file).exists():
            print(f"❌ Файл {yaml_file} не знайдено!")
            return
        generate_matrices_from_yaml(yaml_file, args.excel)
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
        print("0. ❌ Вихід")
        print("=" * 60)

        choice = input("Оберіть опцію (0-7): ").strip()

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
