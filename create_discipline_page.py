"""
Генератор HTML-сторінок дисциплін для WordPress.

Цей модуль забезпечує повний цикл роботи з навчальними дисциплінами:
- Генерація HTML-сторінок на основі YAML-даних та Jinja2-шаблонів
- Створення індексних сторінок зі списком всіх дисциплін
- Завантаження згенерованих сторінок на WordPress через REST API
- Парсинг та оновлення посилань у індексних файлах

Основні компоненти:
    - Завантаження даних з YAML (дисципліни, компетенції, програмні результати)
    - Рендеринг HTML через Jinja2
    - Інтеграція з WordPress REST API
    - CLI інтерфейс для автоматизації

Приклад використання:
    $ python create_discipline_page.py data.yaml --all
    $ python create_discipline_page.py data.yaml --discipline "ПО 01"
    $ python create_discipline_page.py data.yaml --all --upload
"""

import sys
import shutil
import yaml

from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from slugify import slugify
from dotenv import load_dotenv

from core.yaml_handler import load_yaml_data
from core.wp_uploader import update_wordpress_page

from index_parser.index_parse import parse_index_links


YAML_LECTURERS = Path("data") / "lecturers.yaml"


def get_mapped_competencies(discipline_code: str, mappings: dict, all_competencies) -> tuple[list, list]:
    """
    Отримує компетенції для конкретної дисципліни.
    
    Розділяє компетенції на два типи: загальні (ЗК) та фахові (ФК),
    використовуючи мапінг між дисципліною та компетенціями.
    
    Args:
        discipline_code (str): Код дисципліни (наприклад, "ПО 01").
        mappings (dict): Словник маппінгів дисципліна → компетенції.
        all_competencies (dict): Повний словник всіх компетенцій.
    
    Returns:
        tuple[list, list]: Два списки кортежів (код, опис):
            - general_competencies: Загальні компетенції (ЗК)
            - professional_competencies: Фахові компетенції (ФК)
    
    Example:
        >>> comps = {"ЗК1": "Здатність...", "ФК2": "Вміння..."}
        >>> maps = {"ПО 01": {"competencies": ["ЗК1", "ФК2"]}}
        >>> general, professional = get_mapped_competencies("ПО 01", maps, comps)
        >>> general
        [("ЗК1", "Здатність...")]
    """
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


def get_mapped_program_results(discipline_code: str, mappings: dict, all_program_results) -> list[tuple]:
    """
    Отримує програмні результати навчання для дисципліни.
    
    Args:
        discipline_code (str): Код дисципліни.
        mappings (dict): Словник маппінгів дисципліна → програмні результати.
        all_program_results (dict): Повний словник всіх програмних результатів.
    
    Returns:
        list: Список кортежів (код_результату, опис_результату).
    
    Example:
        >>> results = {"ПРН1": "Демонструвати..."}
        >>> maps = {"ПО 01": {"program_results": ["ПРН1"]}}
        >>> get_mapped_program_results("ПО 01", maps, results)
        [("ПРН1", "Демонструвати...")]
    """
    if discipline_code not in mappings:
        return []

    mapped_results = mappings[discipline_code].get("program_results", [])

    program_results = []
    for prn_code in mapped_results:
        if prn_code in all_program_results:
            program_results.append((prn_code, all_program_results[prn_code]))

    return program_results


def load_discipline_data(yaml_file: str | Path, discipline_code: str) -> tuple [dict | None, dict | None]:
    """
    Завантажує дані дисципліни та інформацію про викладачів.
    
    Об'єднує обов'язкові та вибіркові дисципліни, шукає задану дисципліну
    та розгортає інформацію про викладача за його ID.
    
    Args:
        yaml_file (Path): Шлях до YAML-файлу з даними.
        discipline_code (str): Код дисципліни для пошуку.
    
    Returns:
        tuple: (data, discipline) або (None, None) якщо дисципліну не знайдено.
            - data (dict): Повні дані з YAML-файлу.
            - discipline (dict): Дані конкретної дисципліни з розгорнутим викладачем.
    
    Note:
        Автоматично завантажує дані викладачів з YAML_LECTURERS.
    """
    data = load_yaml_data(yaml_file)
    lecturers = load_yaml_data(YAML_LECTURERS)

    all_disciplines = data["disciplines"]

    # Проверяем и объединяем выборочные дисциплины
    if "elevative_disciplines" in data:
        all_disciplines.update(data["elevative_disciplines"])

    if discipline_code not in all_disciplines:
        print(f"❌ Дисципліна {discipline_code} не знайдена!")
        return None, None

    discipline = all_disciplines[discipline_code]

    # Розгортаємо lecturer_id в повні дані лектора
    if "lecturer_id" in discipline:
        lecturer_id = discipline["lecturer_id"]
        discipline["lecturer"] = lecturers.get(lecturer_id)

    return data, discipline


def prepare_discipline_context(discipline_code: str, discipline: dict, data) -> dict:
    """
    Підготовляє контекст для рендерингу Jinja2-шаблону дисципліни.
    
    Збирає всі необхідні дані: метадані, компетенції (загальні та фахові),
    програмні результати навчання.
    
    Args:
        discipline_code (str): Код дисципліни.
        discipline (dict): Дані дисципліни.
        data (dict): Повні дані з YAML-файлу.
    
    Returns:
        dict: Контекст для шаблону з ключами:
            - discipline_code: Код дисципліни
            - discipline: Повні дані дисципліни
            - metadata: Метадані (рік, ступінь)
            - general_competencies: Загальні компетенції
            - professional_competencies: Фахові компетенції
            - mapped_program_results: Програмні результати
    """
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


def get_jinja_environment() -> Environment:
    """
    Створює налаштоване Jinja2 Environment для рендерингу шаблонів.
    
    Returns:
        Environment: Jinja2 Environment з FileSystemLoader та автоескейпінгом.
    
    Note:
        Шаблони завантажуються з папки 'templates' відносно поточного файлу.
    """
    templates_dir = Path(__file__).parent / "templates"
    return Environment(loader=FileSystemLoader(templates_dir), autoescape=True)


def render_template(template_file: str, context: dict) -> str:
    """
    Рендерить HTML-контент через Jinja2-шаблон.
    
    Args:
        template_file (str): Ім'я файлу шаблону в папці templates/.
        context (dict): Контекст з даними для шаблону.
    
    Returns:
        str: Згенерований HTML-контент.
    
    Example:
        >>> context = {"title": "Дисципліна", "code": "ПО 01"}
        >>> html = render_template("discipline_template.html", context)
    """
    env = get_jinja_environment()
    template = env.get_template(template_file)
    return template.render(context)


def save_html_file(content: str, output_file: str | Path) -> None:
    """
    Зберігає HTML-контент у файл з кодуванням UTF-8.
    
    Args:
        content (str): HTML-контент для збереження.
        output_file (str | Path): Шлях до файлу для збереження.
    """
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)


def get_safe_filename(discipline_code: str) -> str:
    """
    Створює безпечне ім'я файлу з коду дисципліни.
    
    Замінює пробіли та слеші на підкреслення для сумісності з файловою системою.
    
    Args:
        discipline_code (str): Код дисципліни (може містити пробіли та слеші).
    
    Returns:
        str: Безпечне ім'я файлу.
    
    Example:
        >>> get_safe_filename("ПО 01/02")
        "ПО_01_02"
    """
    return discipline_code.replace(" ", "_").replace("/", "_")


def generate_discipline_page(
    yaml_file: str | Path,
    discipline_code: str,
    output_file: str | None = None,
    template_file: str = "discipline_template.html",
) -> bool:
    """
    Генерує HTML-сторінку для конкретної дисципліни.
    
    Завантажує дані, рендерить шаблон та зберігає результат у файл.
    
    Args:
        yaml_file (Path): Шлях до YAML-файлу з даними.
        discipline_code (str): Код дисципліни для генерації.
        output_file (str | Path, optional): Шлях до вихідного файлу.
            Якщо None, генерується автоматично.
        template_file (str, optional): Ім'я Jinja2-шаблону.
            За замовчуванням "discipline_template.html".
    
    Returns:
        bool: True якщо генерація успішна, False якщо дисципліну не знайдено.
    
    Example:
        >>> generate_discipline_page(
        ...     Path("data.yaml"),
        ...     "ПО 01",
        ...     output_file="output/po_01.html"
        ... )
        ✅ Сторінка дисципліни створена: output/po_01.html
        True
    """
    data, discipline = load_discipline_data(yaml_file, discipline_code)
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


def create_output_directory(output_dir: str | Path) -> Path:
    """
    Створює директорію для виводу файлів, якщо вона не існує.
    
    Args:
        output_dir (str | Path): Шлях до директорії.
    
    Returns:
        Path: Path-об'єкт створеної/існуючої директорії.
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    return output_path


def generate_all_disciplines(
    yaml_file: str | Path, output_dir: str = "disciplines", template_file: str = "discipline_template.html"
) -> None:
    """
    Генерує HTML-сторінки для всіх дисциплін з YAML-файлу.
    
    Об'єднує обов'язкові та вибіркові дисципліни і генерує для кожної окрему сторінку.
    
    Args:
        yaml_file (Path): Шлях до YAML-файлу з даними.
        output_dir (str, optional): Папка для збереження файлів.
            За замовчуванням "disciplines".
        template_file (str, optional): Ім'я Jinja2-шаблону.
            За замовчуванням "discipline_template.html".
    
    Note:
        Виводить прогрес у консоль та підсумкову статистику успішно створених сторінок.
    
    Example:
        >>> generate_all_disciplines(
        ...     Path("data.yaml"),
        ...     output_dir="output",
        ...     template_file="custom_template.html"
        ... )
        🚀 Генерація сторінок для 15 дисциплін...
        ✅ Успішно створено 15 сторінок у папці output
    """
    data = load_yaml_data(yaml_file)
    output_path = create_output_directory(output_dir)

    all_disciplines = data.get("disciplines", {})

    # Проверяем и объединяем выборочные дисциплины
    if "elevative_disciplines" in data:
        all_disciplines.update(data["elevative_disciplines"])

    print(f"🚀 Генерація сторінок для {len(all_disciplines)} дисциплін...")
    print(f"📄 Шаблон: {template_file}")

    success_count = 0
    for discipline_code in all_disciplines.keys():
        safe_name = get_safe_filename(discipline_code)
        output_file = output_path / f"{safe_name}.html"

        if generate_discipline_page(yaml_file, discipline_code, output_file, template_file):
            success_count += 1

    print(f"✅ Успішно створено {success_count} сторінок у папці {output_dir}")


def calculate_subdiscipline_totals(discipline: dict) -> tuple[int, str]:
    """
    Розраховує загальні кредити та форми контролю для піддисциплін.
    
    Якщо дисципліна містить піддисципліни, підсумовує їхні кредити
    та об'єднує унікальні форми контролю.
    
    Args:
        discipline (dict): Дані дисципліни, можуть містити ключ "subdisciplines".
    
    Returns:
        tuple[int, str]: Кортеж (загальні_кредити, об'єднані_форми_контролю).
            - total_credits (int): Сума кредитів всіх піддисциплін
            - all_controls (str): Форми контролю через кому (наприклад, "Іспит, Залік")
    
    Example:
        >>> discipline = {
        ...     "subdisciplines": {
        ...         "sub1": {"credits": 3, "control": "Іспит"},
        ...         "sub2": {"credits": 2, "control": "Залік"}
        ...     }
        ... }
        >>> calculate_subdiscipline_totals(discipline)
        (5, "Іспит, Залік")
    """
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


def prepare_disciplines_with_totals(disciplines: dict) -> dict:
    """
    Додає розраховані підсумки до кожної дисципліни.
    
    Для кожної дисципліни розраховує і додає:
    - total_credits: загальна кількість кредитів
    - all_controls: об'єднані форми контролю
    
    Args:
        disciplines (dict): Словник дисциплін {код: дані_дисципліни}.
    
    Returns:
        dict: Той самий словник дисциплін з доданими полями total_credits та all_controls.
    
    Note:
        Модифікує словник in-place, але також повертає його для зручності.
    """
    for _, discipline in disciplines.items():
        total_credits, all_controls = calculate_subdiscipline_totals(discipline)
        discipline["total_credits"] = total_credits
        discipline["all_controls"] = all_controls

    return disciplines


def generate_index_page(yaml_file: str | Path, output_file: str ="index.html") -> None:
    """
    Генерує індексну сторінку зі списком всіх дисциплін.
    
    Створює HTML-файл з таблицею всіх дисциплін (обов'язкових та вибіркових),
    їхніми кредитами та формами контролю.
    
    Args:
        yaml_file (Path): Шлях до YAML-файлу з даними.
        output_file (str | Path, optional): Шлях до вихідного файлу.
            За замовчуванням "index.html".
    
    Note:
        Використовує шаблон "index_template.html" з папки templates/.
        Виводить повідомлення про успішне створення у консоль.
    
    Example:
        >>> generate_index_page(Path("data.yaml"), "disciplines/index.html")
        📋 Індексна сторінка створена: disciplines/index.html
    """
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


def validate_yaml_file(yaml_file: str | Path) -> bool:
    """
    Перевіряє існування YAML-файлу.
    
    Args:
        yaml_file (Path): Шлях до YAML-файлу.
    
    Returns:
        bool: True якщо файл існує, False якщо ні.
    
    Note:
        Виводить повідомлення про помилку у консоль при відсутності файлу.
    """
    if not Path(yaml_file).exists():
        print(f"❌ YAML файл не знайдено: {yaml_file}")
        return False
    return True


def clean_output_directory(output_dir: str ='disciplines') -> None:
    """
    Видаляє директорію з усім вмістом.
    
    Args:
        output_dir (str, optional): Шлях до директорії для видалення.
            За замовчуванням 'disciplines'.
    
    Warning:
        Видаляє директорію рекурсивно без підтвердження!
    """
    if Path(output_dir).exists():
        shutil.rmtree(output_dir)


def handle_single_discipline(yaml_file: str | Path, discipline_code: str, template: str):
    """
    Обробляє генерацію однієї дисципліни через CLI.
    
    Args:
        yaml_file (Path): Шлях до YAML-файлу з даними.
        discipline_code (str): Код дисципліни для генерації.
        template (str): Ім'я Jinja2-шаблону.
    
    Note:
        Створює папку "disciplines" якщо вона не існує.
    """
    output_dir = create_output_directory("disciplines")
    safe_name = get_safe_filename(discipline_code)
    output_file = output_dir / f"{safe_name}.html"
    generate_discipline_page(yaml_file, discipline_code, output_file, template)


def handle_all_disciplines(yaml_file: str | Path, args) -> None:
    """
    Обробляє генерацію всіх дисциплін через CLI.
    
    Args:
        yaml_file (Path): Шлях до YAML-файлу з даними.
        args (Namespace): Об'єкт argparse з параметрами командного рядка.
            Використовується args.clean для очищення папки перед генерацією.
    
    Note:
        Якщо args.clean=True, спочатку видаляє існуючу папку з виводом.
    """
    output_dir = create_output_directory("disciplines")
    if args.clean:
        clean_output_directory(output_dir)

    generate_all_disciplines(yaml_file, output_dir)


def handle_index_generation(yaml_file: str | Path, output: str | None) -> None:
    """
    Обробляє генерацію індексної сторінки через CLI.
    
    Args:
        yaml_file (Path): Шлях до YAML-файлу з даними.
        output (str | None): Шлях до вихідного файлу або None.
            Якщо None, використовується "disciplines/index.html".
    """
    output_dir = create_output_directory("disciplines")
    output_file = Path(output) if output else output_dir / "index.html"
    generate_index_page(yaml_file, output_file)


# === WordPress Upload Functions ===

def get_parent_id(yaml_data: str | Path) -> int:
    """
    Отримує ID батьківської сторінки WordPress з YAML-даних.
    
    Args:
        yaml_data (dict): Дані з YAML-файлу.
    
    Returns:
        int: ID батьківської сторінки WordPress.
    
    Raises:
        SystemExit: Якщо ключ 'page_id' відсутній у metadata.
    
    Example:
        >>> yaml_data = {"metadata": {"page_id": 123}}
        >>> get_parent_id(yaml_data)
        123
    """
    try:
        return yaml_data['metadata']['page_id']
    except KeyError:
        print("❌ У YAML немає ключа 'page_id' у metadata")
        sys.exit(1)


def read_html_file(file_path: Path) -> str | None:
    """
    Читає HTML-файл та повертає його вміст.
    
    Args:
        file_path (Path): Шлях до HTML-файлу.
    
    Returns:
        str | None: Вміст файлу або None при помилці читання.
    
    Note:
        При помилці виводить повідомлення у консоль.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"❌ Помилка читання файлу {file_path}: {e}")
        return None


def upload_html_files(disciplines_dir: Path, yaml_data: dict, parent_id: int) -> dict:
    """
    Завантажує всі HTML-файли дисциплін на WordPress.
    
    Сканує директорію з HTML-файлами, завантажує кожен на WordPress
    та збирає посилання на створені/оновлені сторінки.
    
    Args:
        disciplines_dir (Path): Папка з HTML-файлами дисциплін.
        yaml_data (dict): Дані з YAML-файлу (для отримання назв дисциплін).
        parent_id (int): ID батьківської сторінки WordPress.
    
    Returns:
        dict: Структура для збереження в YAML:
            {
                "year": "2024",
                "degree": "Бакалавр",
                "links": {
                    "ПО 01": "https://site.com/page1",
                    "ПО 02": "https://site.com/page2"
                }
            }
    
    Note:
        - Пропускає файл index.html
        - Використовує slugify для створення URL-friendly slug
        - Виводить статус завантаження кожного файлу у консоль
    """
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


def save_wp_links_yaml(wp_data: dict, output_file: str ="wp_links.yaml") -> None:
    """
    Зберігає посилання WordPress та метадані у YAML-файл.
    
    Args:
        wp_data (dict): Структура з посиланнями та метаданими:
            {
                "year": "2024",
                "degree": "Бакалавр",
                "links": {"ПО 01": "https://..."}
            }
        output_file (str | Path, optional): Шлях до вихідного YAML-файлу.
            За замовчуванням "wp_links.yaml".
    
    Note:
        Автоматично створює батьківські директорії якщо їх не існує.
        Використовує кодування UTF-8 для підтримки кирилиці.
    """
    output_path = Path(output_file)
    
    # Проверяем и создаём родительскую папку, если её нет
    if output_path.parent and not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(wp_data, f, allow_unicode=True)
    
    print(f"📋 WP посилання збережені в {output_path}")


def handle_upload(yaml_file: str | Path, disciplines_dir: str, check_dir=True, save_yaml=True) -> None:
    """Обробка завантаження на WordPress"""

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

    # Зберігаємо YAML тільки якщо save_yaml=True
    if save_yaml:
        yaml_name = Path(yaml_file).stem
        save_wp_links_yaml(wp_data, Path("wp_links") / f"wp_links_{yaml_name}.yaml")


def get_index_slug(yaml_data: dict) -> str:
    """Формирует slug для index страницы на основе year и degree"""
    try:
        year = yaml_data['metadata']['year']
        degree = yaml_data['metadata']['degree']
    except KeyError as e:
        print(f"❌ В YAML нет ключа {e} в metadata для index slug")
        sys.exit(1)

    # латинизация и lower

    slug = slugify(f"op_{degree}-{year}")
    return slug


def upload_index_page(yaml_data: dict, index_file: str | Path) -> tuple[bool, str|None, str]:
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


def handle_upload_index(yaml_file: str | Path, output_dir: str | None = None) -> None:
    """Обработка загрузки index.html"""
    yaml_data = load_yaml_data(yaml_file)

    # По умолчанию папка вывода
    output_dir = Path(output_dir) if output_dir else Path("disciplines")
    index_file = output_dir / "index.html"

    if not index_file.exists():
        print(f"❌ Файл {index_file} не найден, сначала сгенерируйте его с --index")
        return

    upload_index_page(yaml_data, index_file)


def handle_parse_index(yaml_file: str | Path, output_dir: str | None = None) -> None:
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
        'upload': lambda: handle_upload(
            yaml_file, 
            args.output or "disciplines", 
            check_dir=True,
            save_yaml=not args.discipline  # False якщо -d вказано
        ),
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
