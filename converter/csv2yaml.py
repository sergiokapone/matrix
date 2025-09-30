import pandas as pd
import yaml
from pathlib import Path

def csv_to_yaml_mappings(csv_file, yaml_template_file=None, output_file=None):
    """
    Конвертує CSV файл у YAML mappings

    CSV формат:
    Шифр | Назва дисципліни | Компетентності | Результати навчання
    ЗО 01 | Математичний аналіз | ЗК 1, ЗК 2, ФК 6 | ПРН 1, ПРН 2
    """

    try:
        # Читаємо CSV
        df = pd.read_csv(csv_file, encoding='utf-8')

        # Очищуємо заголовки від зайвих пробілів
        df.columns = df.columns.str.strip()

        # Можливі варіанти назв колонок
        code_col = find_column(df, ['шифр', 'код', 'code', 'шифр дисципліни'])
        name_col = find_column(df, ['назва', 'дисципліна', 'назва дисципліни', 'name', 'discipline'])
        comp_col = find_column(df, ['компетентності', 'компетенції', 'competencies'])
        prn_col = find_column(df, ['результати', 'програмні результати', 'прн', 'program_results', 'results'])

        if not all([code_col, name_col, comp_col, prn_col]):
            missing = []
            if not code_col: missing.append("Шифр/Код")
            if not name_col: missing.append("Назва дисципліни")
            if not comp_col: missing.append("Компетентності")
            if not prn_col: missing.append("Результати навчання")

            print(f"❌ Не знайдено колонки: {', '.join(missing)}")
            print(f"📋 Доступні колонки: {', '.join(df.columns.tolist())}")
            return False

        # Завантажуємо існуючий YAML шаблон або створюємо базовий
        if yaml_template_file and Path(yaml_template_file).exists():
            with open(yaml_template_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            print(f"📂 Завантажено шаблон: {yaml_template_file}")
        else:
            config = create_basic_yaml_structure()
            print("📝 Створено базову YAML структуру")

        # Парсимо CSV та створюємо mappings
        mappings = {}
        disciplines_from_csv = {}
        errors = []

        for index, row in df.iterrows():
            try:
                # Отримуємо дані з рядка
                code = str(row[code_col]).strip()
                name = str(row[name_col]).strip()
                competencies_str = str(row[comp_col]).strip() if pd.notna(row[comp_col]) else ""
                results_str = str(row[prn_col]).strip() if pd.notna(row[prn_col]) else ""

                if not code or code == 'nan':
                    continue

                # Парсимо компетентності
                competencies = parse_items_list(competencies_str)
                program_results = parse_items_list(results_str)

                # Додаємо до mappings
                if competencies or program_results:
                    mappings[code] = {
                        "competencies": competencies,
                        "program_results": program_results
                    }

                # Додаємо дисципліну
                if name and name != 'nan':
                    disciplines_from_csv[code] = name

            except Exception as e:
                errors.append(f"Рядок {index + 2}: {str(e)}")

        # Оновлюємо конфігурацію
        config["mappings"] = mappings

        # Додаємо нові дисципліни (якщо їх немає у шаблоні)
        if "disciplines" not in config:
            config["disciplines"] = {}

        for code, name in disciplines_from_csv.items():
            if code not in config["disciplines"]:
                config["disciplines"][code] = name

        # Зберігаємо результат
        if not output_file:
            output_file = Path(csv_file).with_suffix('.yaml')

        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False,
                     indent=2, sort_keys=False)

        # Звіт
        print(f"✅ Конвертація завершена: {output_file}")
        print(f"📊 Оброблено дисциплін: {len(mappings)}")
        print(f"📊 Додано нових дисциплін: {len(disciplines_from_csv)}")

        if errors:
            print(f"\n⚠️ Помилки ({len(errors)}):")
            for error in errors[:5]:  # Показуємо перші 5 помилок
                print(f"  • {error}")
            if len(errors) > 5:
                print(f"  ... та ще {len(errors) - 5} помилок")

        return True

    except Exception as e:
        print(f"❌ Помилка читання CSV: {e}")
        return False

def find_column(df, possible_names):
    """Знаходить колонку за можливими назвами"""
    df_cols_lower = [col.lower().strip() for col in df.columns]

    for name in possible_names:
        name_lower = name.lower().strip()
        if name_lower in df_cols_lower:
            return df.columns[df_cols_lower.index(name_lower)]

    # Пошук по частковому збігу
    for name in possible_names:
        name_lower = name.lower().strip()
        for i, col in enumerate(df_cols_lower):
            if name_lower in col or col in name_lower:
                return df.columns[i]

    return None

def parse_items_list(items_str):
    """
    Парсить рядок з переліком кодів
    Приклад: "ЗК 1, ЗК 2, ФК 6" → ["ЗК 1", "ЗК 2", "ФК 6"]
    """
    if not items_str or items_str == 'nan':
        return []

    # Розділяємо по комах, крапці з комою, або переносу рядка
    items = []
    raw_items = items_str.replace(';', ',').replace('\n', ',').split(',')

    for item in raw_items:
        item = item.strip()
        if item and item != '-' and item.lower() != 'немає':
            # Нормалізуємо формат (додаємо пробіл між літерами і цифрами)
            import re
            item = re.sub(r'([А-Я]+)(\d+)', r'\1 \2', item)
            items.append(item)

    return items

def create_basic_yaml_structure():
    """Створює базову YAML структуру"""
    return {
        "metadata": {
            "title": "Освітньо-професійна програма (згенеровано з CSV)",
            "university": "Національний технічний університет України \"КПІ ім. Ігоря Сікорського\"",
            "faculty": "НН Фізико-технічний інститут",
            "department": "Кафедра прикладної фізики", 
            "specialty": "105 Прикладна фізика",
            "website": "https://osvita.kpi.ua",
            "year": "2024",
            "degree": "Бакалавр",
            "created_date": pd.Timestamp.now().strftime("%Y-%m-%d"),
            "last_updated": pd.Timestamp.now().strftime("%Y-%m-%d"),
            "credits_total": 240,

        },
        "disciplines": {},
        "competencies": {},
        "program_results": {},
        "mappings": {}
    }

def create_csv_template(output_file="template.csv"):
    """Створює CSV шаблон для заповнення"""

    template_data = {
        "Шифр": ["ЗО 01", "ЗО 02", "ПО 01", "ПО 02"],
        "Назва дисципліни": [
            "Математичний аналіз",
            "Алгебра та геометрія",
            "Програмування",
            "Комп'ютерна графіка"
        ],
        "Компетентності": [
            "ЗК 1, ЗК 2, ФК 6, ФК 7",
            "ЗК 1, ЗК 2, ФК 7",
            "ЗК 1, ЗК 5, ФК 5, ФК 10",
            "ЗК 5, ФК 5, ФК 10"
        ],
        "Результати навчання": [
            "ПРН 1, ПРН 2",
            "ПРН 2",
            "ПРН 4, ПРН 16",
            "ПРН 15, ПРН 16"
        ]
    }

    df = pd.DataFrame(template_data)
    df.to_csv(output_file, index=False, encoding='utf-8')

    print(f"📄 CSV шаблон створено: {output_file}")
    print("💡 Заповніть його та використайте для конвертації у YAML")

def validate_csv_before_conversion(csv_file):
    """Перевіряє CSV файл перед конвертацією"""
    try:
        df = pd.read_csv(csv_file, encoding='utf-8')

        print(f"📋 Аналіз CSV файлу: {csv_file}")
        print(f"📊 Рядків: {len(df)}")
        print(f"📊 Колонок: {len(df.columns)}")
        print("\n📝 Колонки:")
        for i, col in enumerate(df.columns):
            print(f"  {i+1}. {col}")

        print("\n📖 Перші 3 рядки:")
        print(df.head(3).to_string())

        # Перевірка на порожні клітинки
        empty_cells = df.isnull().sum()
        if empty_cells.any():
            print("\n⚠️ Порожні клітинки:")
            for col, count in empty_cells.items():
                if count > 0:
                    print(f"  {col}: {count} порожніх")

        return True

    except Exception as e:
        print(f"❌ Помилка читання CSV: {e}")
        return False

