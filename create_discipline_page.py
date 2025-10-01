import shutil
import os
import sys
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from slugify import slugify
from dotenv import load_dotenv
from slugify import slugify
import yaml

from core.yaml_handler import load_yaml_data
from core.wp_uploader import update_wordpress_page
from core.path_validator import validate_paths

from index_parser.index_parse import parse_index_links


YAML_LECTURERS = Path("data") / "lecturers.yaml"


def get_mapped_competencies(discipline_code, mappings, all_competencies):
    """Отримує компетенції для конкретної дисципліни розділені на загальні та фахові"""
    if discipline_code not in mappings:
        return [], []

    mapped_comps = mappings[discipline_code].get("competencies", [])

    general_competencies = []
    professional_competencies = []

    for comp_code in mapped_comps:
        if comp_code in all_competencies:
            comp_desc = all_competencies[comp_code]
            if comp_code.startswith("ЗК"):
                general_competencies.append((comp_code, comp_desc))
            elif comp_code.startswith("ФК"):
                professional_competencies.append((comp_code, comp_desc))

    return general_competencies, professional_competencies


def get_mapped_program_results(discipline_code, mappings, all_program_results):
    """Отримує програмні результати для конкретної дисципліни"""
    if discipline_code not in mappings:
        return []

    mapped_results = mappings[discipline_code].get("program_results", [])

    program_results = []
    for prn_code in mapped_results:
        if prn_code in all_program_results:
            program_results.append((prn_code, all_program_results[prn_code]))

    return program_results


def load_discipline_data(yaml_file, discipline_code):
    """Завантажує дані дисципліни та лекторів"""
    data = load_yaml_data(yaml_file)
    lecturers = load_yaml_data(YAML_LECTURERS)

    all_disciplines = data["disciplines"]

    # Проверяем и объединяем выборочные дисциплины
    if "elevative_disciplines" in data:
        all_disciplines.update(data["elevative_disciplines"])

    # all_disciplines = {**data["disciplines"], **data["elevative_disciplines"]}

    if discipline_code not in all_disciplines:
        print(f"❌ Дисципліна {discipline_code} не знайдена!")
        return None, None, None

    # Шукаємо дисципліну в обох словниках
    discipline = all_disciplines[discipline_code]

    # Розгортаємо lecturer_id в повні дані лектора
    if "lecturer_id" in discipline:
        lecturer_id = discipline["lecturer_id"]
        discipline["lecturer"] = lecturers.get(lecturer_id)

    return data, discipline, lecturers


def prepare_discipline_context(discipline_code, discipline, data):
    """Підготовка контексту для шаблону дисципліни"""
    metadata = data.get("metadata", {})

    general_comps, professional_comps = get_mapped_competencies(
        discipline_code, data.get("mappings", {}), data.get("competencies", {})
    )
    program_results = get_mapped_program_results(
        discipline_code, data.get("mappings", {}), data.get("program_results", {})
    )

    return {
        "discipline_code": discipline_code,
        "discipline": discipline,
        "metadata": metadata,
        "general_competencies": general_comps,
        "professional_competencies": professional_comps,
        "mapped_program_results": program_results,
    }


def get_jinja_environment():
    """Створює Jinja2 Environment з шаблонами"""
    templates_dir = os.path.join(os.path.dirname(__file__), "templates")
    return Environment(loader=FileSystemLoader(templates_dir), autoescape=True)


def render_template(template_file, context):
    """Рендерить HTML через Jinja2 шаблон"""
    env = get_jinja_environment()
    template = env.get_template(template_file)
    return template.render(context)


def save_html_file(content, output_file):
    """Зберігає HTML контент у файл"""
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)


def get_safe_filename(discipline_code):
    """Створює безпечне ім'я файлу з коду дисципліни"""
    return discipline_code.replace(" ", "_").replace("/", "_")


def generate_discipline_page(
    yaml_file,
    discipline_code,
    output_file=None,
    template_file="discipline_template.html",
):
    """Генерує HTML сторінку для конкретної дисципліни через Jinja2 шаблон"""

    data, discipline, lecturers = load_discipline_data(yaml_file, discipline_code)
    if data is None:
        return False

    context = prepare_discipline_context(discipline_code, discipline, data)
    html_content = render_template(template_file, context)

    if not output_file:
        safe_name = get_safe_filename(discipline_code)
        output_file = f"discipline_{safe_name}.html"

    save_html_file(html_content, output_file)
    print(f"✅ Сторінка дисципліни створена: {output_file}")
    return True


def create_output_directory(output_dir):
    """Створює директорію для виводу"""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    return output_path


def generate_all_disciplines(
    yaml_file, output_dir="disciplines", template_file="discipline_template.html"
):
    """Генерує сторінки для всіх дисциплін"""

    data = load_yaml_data(yaml_file)
    output_path = create_output_directory(output_dir)
    disciplines = data.get("disciplines", {}) | data.get("elevative_disciplines", {})

    print(f"🚀 Генерація сторінок для {len(disciplines)} дисциплін...")
    print(f"📄 Шаблон: {template_file}")

    success_count = 0
    for discipline_code in disciplines.keys():
        safe_name = get_safe_filename(discipline_code)
        output_file = output_path / f"{safe_name}.html"

        if generate_discipline_page(yaml_file, discipline_code, output_file, template_file):
            success_count += 1

    print(f"✅ Успішно створено {success_count} сторінок у папці {output_dir}")


def calculate_subdiscipline_totals(discipline):
    """Розраховує загальні кредити та форми контролю для піддисциплін"""
    if "subdisciplines" not in discipline or not discipline["subdisciplines"]:
        return discipline.get("credits", 0), discipline.get("control", "")

    total_credits = sum(
        sub.get("credits", 0) for sub in discipline["subdisciplines"].values()
    )

    controls = list(
        {
            sub.get("control")
            for sub in discipline["subdisciplines"].values()
            if sub.get("control")
        }
    )

    return total_credits, ", ".join(controls)


def prepare_disciplines_with_totals(disciplines):
    """Підготовка дисциплін з розрахованими підсумками"""
    for _, discipline in disciplines.items():
        total_credits, all_controls = calculate_subdiscipline_totals(discipline)
        discipline["total_credits"] = total_credits
        discipline["all_controls"] = all_controls

    return disciplines


def generate_index_page(yaml_file, output_file="index.html"):
    """Генерує індексну сторінку зі списком всіх дисциплін через Jinja2 шаблон"""

    data = load_yaml_data(yaml_file)
    metadata = data.get("metadata", {})
    disciplines = data.get("disciplines", {}) | data.get("elevative_disciplines", {})

    disciplines = prepare_disciplines_with_totals(disciplines)

    context = {
        "metadata": metadata,
        "disciplines": disciplines
    }

    html_content = render_template("index_template.html", context)
    save_html_file(html_content, output_file)

    print(f"📋 Індексна сторінка створена: {output_file}")


def validate_yaml_file(yaml_file):
    """Перевіряє існування YAML файлу"""
    if not Path(yaml_file).exists():
        print(f"❌ YAML файл не знайдено: {yaml_file}")
        return False
    return True


def clean_output_directory(output_dir='disciplines'):
    """Видаляє директорію з усім вмістом"""
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)


def handle_single_discipline(yaml_file, discipline_code, template):
    """Обробка генерації однієї дисципліни"""
    output_dir = create_output_directory("disciplines")
    safe_name = get_safe_filename(discipline_code)
    output_file = output_dir / f"{safe_name}.html"
    generate_discipline_page(yaml_file, discipline_code, output_file, template)


def handle_all_disciplines(yaml_file, clean=False):
    """Обробка генерації всіх дисциплін"""

    output_dir = create_output_directory("disciplines")
    if clean:
        clean_output_directory(output_dir)

    generate_all_disciplines(yaml_file, output_dir)


def handle_index_generation(yaml_file, output):
    """Обробка генерації індексної сторінки"""
    output_dir = create_output_directory("disciplines")
    output_file = Path(output) if output else output_dir / "index.html"
    generate_index_page(yaml_file, output_file)


# === WordPress Upload Functions ===

def get_parent_id(yaml_data):
    """Отримання PARENT_ID з YAML"""
    try:
        return yaml_data['metadata']['page_id']
    except KeyError:
        print("❌ У YAML немає ключа 'page_id' у metadata")
        sys.exit(1)


def read_html_file(file_path):
    """Читання HTML файлу"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"❌ Помилка читання файлу {file_path}: {e}")
        return None


def upload_html_files(disciplines_dir, yaml_data, parent_id):
    """Завантаження всіх HTML файлів на WordPress та підготовка YAML-структури"""
    wp_links = {}
    
    # Об'єднуємо обидва словники дисциплін
    all_disciplines = {**yaml_data['disciplines'], **yaml_data.get('elevative_disciplines', {})}

    for html_file in disciplines_dir.glob("*.html"):
        if html_file.name.lower() == "index.html":
            continue

        discipline_code = html_file.stem.replace('_', ' ')
        discipline_info = all_disciplines.get(discipline_code)

        if not discipline_info:
            print(f"❌ Дисципліна {discipline_code} не знайдена в YAML, пропускаємо...")
            continue

        content = read_html_file(html_file)
        if content is None:
            continue

        title = f"{discipline_code}: {discipline_info['name']}"
        slug = slugify(title)

        success, link, message = update_wordpress_page(
            content=content,
            slug=slug,
            data={
                'title': title,
                'slug': slug,
                'parent': parent_id,
                'status': 'publish'
            }
        )

        if success:
            print(f"{message}: {title} → {link}")
            wp_links[discipline_code] = link
        else:
            print(f"❌ {title}: {message}")

    # Собираем финальную структуру для сохранения в YAML
    metadata = {
        "year": yaml_data.get("metadata", {}).get("year", ""),
        "degree": yaml_data.get("metadata", {}).get("degree", "")
    }

    wp_data = {
        "year": metadata["year"],
        "degree": metadata["degree"],
        "links": wp_links
    }

    return wp_data

def print_upload_summary(wp_links):
    """Виведення підсумкової інформації про завантаження"""
    print("-" * 60)
    print("📋 Підсумок - всі посилання:")
    for code, link in sorted(wp_links.items()):
        print(f'    "{code}": "{link}",')
    print("-" * 60)


def save_wp_links_yaml(wp_data, output_file="wp_links.yaml"):
    """Сохраняет WP ссылки + метаданные в YAML"""
    output_path = Path(output_file)
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(wp_data, f, allow_unicode=True)
    print(f"📋 WP ссылки сохранены в {output_file}")


def handle_upload(yaml_file, disciplines_dir, check_dir=True):
    """Обробка завантаження на WordPress"""
    load_dotenv()

    disciplines_path = Path(disciplines_dir)

    if check_dir and not disciplines_path.exists():
        print(f"❌ Папка {disciplines_dir} не існує! Спочатку згенеруйте сторінки за допомогою --all")
        return

    yaml_data = load_yaml_data(yaml_file)
    parent_id = get_parent_id(yaml_data)

    print("-" * 60)
    print("🚀 Завантаження на WordPress...")
    print("-" * 60)

    wp_data = upload_html_files(disciplines_path, yaml_data, parent_id)

    yaml_name = Path(yaml_file).stem

    save_wp_links_yaml(wp_data, f"wp_links_{yaml_name}.yaml")


# def handle_upload_only(yaml_file, args): 
#     """Только загрузка в WP (без генерации)""" 
#     output_dir = args.output if args.output else "disciplines" 
#     disciplines_dir = Path(output_dir) 
#     if not disciplines_dir.exists(): 
#         print(f"❌ Папка {output_dir} не існує! Спочатку згенеруйте сторінки за допомогою --all") 
#         return

def get_index_slug(yaml_file):
    """Формирует slug для index страницы на основе year и degree"""
    try:
        year = yaml_file['metadata']['year']
        degree = yaml_file['metadata']['degree']
    except KeyError as e:
        print(f"❌ В YAML нет ключа {e} в metadata для index slug")
        sys.exit(1)

    # латинизация и lower

    slug = slugify(f"op_{degree}-{year}")
    return slug


def upload_index_page(yaml_data, index_file):
    """Обновление index.html на WordPress по существующему ID"""
    content = read_html_file(index_file)
    if content is None:
        return

    page_id = yaml_data['metadata'].get('page_id')
    if not page_id:
        print("❌ В YAML нет ключа 'page_id' для обновления страницы index")
        return

    slug = get_index_slug(yaml_data)
    title = f"Освітні компоненти: {yaml_data['metadata'].get('degree', '')} {yaml_data['metadata'].get('year', '')}"

    success, link, message = update_wordpress_page(
        content=content,
        slug=slug,
        data={
            'title': title,
            'slug': slug,
            'parent': 16,
            'status': 'publish'
        },
        page_id=page_id  # обновляем существующую страницу
    )

    if success:
        print(f"✅ Index обновлен: {title} → {link}")
        return link
    else:
        print(f"❌ Index: {message}")
        return None


def handle_upload_index(yaml_file, output_dir=None):
    """Обработка загрузки index.html"""
    yaml_data = load_yaml_data(yaml_file)

    # По умолчанию папка вывода
    output_dir = Path(output_dir) if output_dir else Path("disciplines")
    index_file = output_dir / "index.html"

    if not index_file.exists():
        print(f"❌ Файл {index_file} не найден, сначала сгенерируйте его с --index")
        return

    upload_index_page(yaml_data, index_file)


def handle_parse_index(yaml_file, output_dir=None):
    """
    Хендлер для CLI: вызывает функцию parse_index_links из модуля.
    
    yaml_file: путь к YAML (для совместимости, не используется)
    output_dir: папка с index.html, по умолчанию 'disciplines'
    """

    output_dir = Path(output_dir) if output_dir else Path("disciplines")
    index_file = output_dir / "index.html"
    parse_index_links(index_file, data_yaml=yaml_file)


def print_usage_examples():
    """Виводить приклади використання CLI з усіма доступними опціями"""
    print("❌ Оберіть одну з опцій: --discipline, --all, --index, --parse-index, --upload, --upload-index")
    print("💡 Приклади використання:")
    print("  python create_discipline_page.py data.yaml -d 'ПО 01'                # Генерація однієї дисципліни")
    print("  python create_discipline_page.py data.yaml --all                     # Генерація всіх дисциплін")
    print("  python create_discipline_page.py data.yaml --all --upload            # Генерація та завантаження всіх дисциплін на WP")
    print("  python create_discipline_page.py data.yaml --upload                  # Завантаження вже згенерованих сторінок")
    print("  python create_discipline_page.py data.yaml --index                   # Генерація індексної сторінки")
    print("  python create_discipline_page.py data.yaml --parse-index             # Підстановка WP посилань у index.html")
    print("  python create_discipline_page.py data.yaml --upload-index            # Завантаження index.html на WP")
    print("  python create_discipline_page.py data.yaml --index --parse-index --upload-index")
    print("      # Генерація індексу, підстановка посилань і завантаження на WP")
    print("  python create_discipline_page.py data.yaml --all --template custom_template.html")



def parse_arguments():
    """Парсинг аргументів командного рядка"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Генератор сторінок дисциплін для WordPress"
    )
    parser.add_argument("yaml_file", help="Шлях до YAML файлу з даними")
    parser.add_argument(
        "--discipline", "-d", help="Код конкретної дисципліни для генерації"
    )

    parser.add_argument("--upload-index", "-ui", action="store_true", help="Загрузить index.html на WordPress")

    parser.add_argument(
        "--template",
        "-t",
        default="discipline_template.html",
        help="Файл шаблону в папці templates/",
    )
    parser.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="Генерувати сторінки для всіх дисциплін",
    )
    parser.add_argument(
        "--index", "-i", action="store_true", help="Створити індексну сторінку"
    )
    parser.add_argument("--output", "-o", help="Вихідний файл або папка")
    parser.add_argument(
        "--clean", "-c", action="store_true", help="Очистити каталог перед генерацією"
    )
    parser.add_argument(
        "--upload", "-u", action="store_true",
        help="Завантажити згенеровані сторінки на WordPress"
    )

    parser.add_argument(
        "--parse-index", "-pi", action="store_true", help="Підставити в файл index.html посилання на сайт"
    )


    return parser.parse_args()


def main():
    """Головна функція з CLI інтерфейсом"""
    args = parse_arguments()
    yaml_file = Path("data") / args.yaml_file

    if not validate_yaml_file(yaml_file):
        return

    # Словник дій CLI
    cli_actions = {
        'clean': lambda: clean_output_directory(),
        'discipline': lambda: handle_single_discipline(yaml_file, args.discipline, args.template),
        'all': lambda: handle_all_disciplines(yaml_file, args),
        'upload': lambda: handle_upload(yaml_file, args.output or "disciplines", check_dir=True),
        'index': lambda: handle_index_generation(yaml_file, args.output),
        'parse_index': lambda: handle_parse_index(yaml_file, args.output),
        'upload_index': lambda: handle_upload_index(yaml_file, args.output),

    }

    # Визначаємо пріоритет команд
    executed = False
    for action_name in cli_actions.keys():
        if getattr(args, action_name, False):
            cli_actions[action_name]()
            executed = True

    # Якщо жодна команда не вказана
    if not executed:
        print_usage_examples()


if __name__ == "__main__":
    main()
