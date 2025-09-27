import yaml
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, Template

def generate_discipline_page(yaml_file, discipline_code, output_file=None, template_dir="templates", template_name="discipline_template.html"):
    """Генерує HTML сторінку для конкретної дисципліни"""
    
    # Налаштовуємо Jinja2 environment
    jinja_env = setup_jinja_environment(template_dir)
    
    # Завантажуємо дані
    data = load_yaml_data(yaml_file)
    
    # Перевіряємо наявність дисципліни
    if discipline_code not in data['disciplines']:
        print(f"❌ Дисципліна {discipline_code} не знайдена!")
        return False
    
    try:
        # Завантажуємо шаблон з папки templates
        template = jinja_env.get_template(template_name)
    except Exception as e:
        print(f"❌ Помилка завантаження шаблону {template_name}: {e}")
        return False
    
    # Отримуємо дані дисципліни
    discipline = data['disciplines'][discipline_code]
    metadata = data.get('metadata', {})
    
    # Отримуємо відповідні компетенції та результати
    general_comps, professional_comps = get_mapped_competencies(
        discipline_code, data.get('mappings', {}), data.get('competencies', {}))
    
    program_results = get_mapped_program_results(
        discipline_code, data.get('mappings', {}), data.get('program_results', {}))
    
    # Підготовуємо контекст для шаблону
    context = {
        'discipline_code': discipline_code,
        'discipline': discipline,
        'metadata': metadata,
        'general_competencies': general_comps,
        'professional_competencies': professional_comps,
        'mapped_program_results': program_results
    }
    
    # Рендеримо шаблон
    html_content = template.render(context)
    
    # Зберігаємо файл
    if not output_file:
        safe_name = discipline_code.replace(' ', '_').replace('/', '_')
        output_file = f"discipline_{safe_name}.html"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Сторінка дисципліни створена: {output_file}")
    return True

def generate_all_disciplines(yaml_file, output_dir="disciplines", template_dir="templates", template_name="discipline_template.html"):
    """Генерує сторінки для всіх дисциплін"""
    
    # Налаштовуємо Jinja2 environment
    jinja_env = setup_jinja_environment(template_dir)
    
    data = load_yaml_data(yaml_file)
    
    # Створюємо директорію для виводу
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    disciplines = data.get('disciplines', {})
    
    print(f"🚀 Генерація сторінок для {len(disciplines)} дисциплін...")
    print(f"📄 Шаблон: {template_dir}/{template_name}")
    
    success_count = 0
    for discipline_code in disciplines.keys():
        safe_name = discipline_code.replace(' ', '_').replace('/', '_')
        output_file = output_path / f"{safe_name}.html"
        
        if generate_discipline_page(yaml_file, discipline_code, output_file, template_dir, template_name):
            success_count += 1
    
    print(f"✅ Успішно створено {success_count} сторінок у папці {output_dir}")

def generate_index_page(yaml_file, output_file="index.html", template_dir="templates", template_name="index_template.html"):
    """Генерує індексну сторінку зі списком всіх дисциплін"""
    
    # Налаштовуємо Jinja2 environment
    jinja_env = setup_jinja_environment(template_dir)
    
    data = load_yaml_data(yaml_file)
    metadata = data.get('metadata', {})
    disciplines = data.get('disciplines', {})
    
    try:
        # Завантажуємо шаблон індексу з папки templates
        template = jinja_env.get_template(template_name)
    except Exception as e:
        print(f"❌ Помилка завантаження шаблону {template_name}: {e}")
        return False
    
    # Рендеримо шаблон
    html_content = template.render(metadata=metadata, disciplines=disciplines)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"📋 Індексна сторінка створена: {output_file}")
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, Template

def setup_jinja_environment(template_dir="templates"):
    """Налаштовує Jinja2 Environment для роботи з папкою шаблонів"""
    template_path = Path(template_dir)
        
    return Environment(loader=FileSystemLoader(template_dir))


def load_template(template_file="discipline_template.html"):
    """Завантажує шаблон з файлу (deprecated - використовуйте setup_jinja_environment)"""
    template_path = Path(template_file)
        
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()

def load_yaml_data(yaml_file):
    """Завантажує дані з YAML файлу"""
    with open(yaml_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def get_mapped_competencies(discipline_code, mappings, all_competencies):
    """Отримує компетенції для конкретної дисципліни розділені на загальні та фахові"""
    if discipline_code not in mappings:
        return [], []
    
    mapped_comps = mappings[discipline_code].get('competencies', [])
    
    general_competencies = []
    professional_competencies = []
    
    for comp_code in mapped_comps:
        if comp_code in all_competencies:
            comp_desc = all_competencies[comp_code]
            if comp_code.startswith('ЗК'):
                general_competencies.append((comp_code, comp_desc))
            elif comp_code.startswith('ФК'):
                professional_competencies.append((comp_code, comp_desc))
    
    return general_competencies, professional_competencies

def get_mapped_program_results(discipline_code, mappings, all_program_results):
    """Отримує програмні результати для конкретної дисципліни"""
    if discipline_code not in mappings:
        return []
    
    mapped_results = mappings[discipline_code].get('program_results', [])
    
    program_results = []
    for prn_code in mapped_results:
        if prn_code in all_program_results:
            program_results.append((prn_code, all_program_results[prn_code]))
    
    return program_results

from jinja2 import Environment, FileSystemLoader
import os

def generate_discipline_page(yaml_file, discipline_code, output_file=None, template_file="discipline_template.html"):
    """Генерує HTML сторінку для конкретної дисципліни через Jinja2 шаблон"""
    
    # Завантажуємо дані
    data = load_yaml_data(yaml_file)
    
    # Перевіряємо наявність дисципліни
    if discipline_code not in data['disciplines']:
        print(f"❌ Дисципліна {discipline_code} не знайдена!")
        return False
    
    discipline = data['disciplines'][discipline_code]
    metadata = data.get('metadata', {})

    # Відповідні компетенції та результати
    general_comps, professional_comps = get_mapped_competencies(
        discipline_code, data.get('mappings', {}), data.get('competencies', {}))
    program_results = get_mapped_program_results(
        discipline_code, data.get('mappings', {}), data.get('program_results', {}))

    # Підготовка контексту
    context = {
        'discipline_code': discipline_code,
        'discipline': discipline,
        'metadata': metadata,
        'general_competencies': general_comps,
        'professional_competencies': professional_comps,
        'mapped_program_results': program_results
    }

    # Папка з шаблонами
    templates_dir = os.path.join(os.path.dirname(__file__), "templates")
    env = Environment(loader=FileSystemLoader(templates_dir), autoescape=True)
    
    # Завантажуємо шаблон
    template = env.get_template(template_file)
    
    # Рендеримо HTML
    html_content = template.render(context)
    
    # Зберігаємо файл
    if not output_file:
        safe_name = discipline_code.replace(' ', '_').replace('/', '_')
        output_file = f"discipline_{safe_name}.html"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Сторінка дисципліни створена: {output_file}")
    return True


def generate_all_disciplines(yaml_file, output_dir="disciplines", template_file="discipline_template.html"):
    """Генерує сторінки для всіх дисциплін"""
    
    data = load_yaml_data(yaml_file)
    
    # Створюємо директорію для виводу
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    disciplines = data.get('disciplines', {})
    
    print(f"🚀 Генерація сторінок для {len(disciplines)} дисциплін...")
    print(f"📄 Шаблон: {template_file}")
    
    success_count = 0
    for discipline_code in disciplines.keys():
        safe_name = discipline_code.replace(' ', '_').replace('/', '_')
        output_file = output_path / f"{safe_name}.html"
        
        if generate_discipline_page(yaml_file, discipline_code, output_file, template_file):
            success_count += 1
    
    print(f"✅ Успішно створено {success_count} сторінок у папці {output_dir}")

def generate_index_page(yaml_file, output_file="index.html"):
    """Генерує індексну сторінку зі списком всіх дисциплін через Jinja2 шаблон"""
    
    data = load_yaml_data(yaml_file)
    metadata = data.get('metadata', {})
    disciplines = data.get('disciplines', {})

    # Подготовка суммарных кредитов и контроля для поддисциплин
    for code, discipline in disciplines.items():
        if 'subdisciplines' in discipline and discipline['subdisciplines']:
            # Суммируем кредиты поддисциплин
            total_credits = sum(sub.get('credits', 0) for sub in discipline['subdisciplines'].values())
            # Собираем уникальные формы контроля
            controls = list({sub.get('control') for sub in discipline['subdisciplines'].values() if sub.get('control')})
            discipline['total_credits'] = total_credits
            discipline['all_controls'] = ', '.join(controls)
        else:
            discipline['total_credits'] = discipline.get('credits', 0)
            discipline['all_controls'] = discipline.get('control', '')

    # Вказуємо Jinja2 на папку з шаблонами
    templates_dir = os.path.join(os.path.dirname(__file__), "templates")
    env = Environment(loader=FileSystemLoader(templates_dir), autoescape=True)
    
    # Завантажуємо шаблон
    template = env.get_template("index_template.html")
    
    # Рендеримо HTML
    html_content = template.render(metadata=metadata, disciplines=disciplines)
    
    # Записуємо у файл
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"📋 Індексна сторінка створена: {output_file}")


def main():
    """Головна функція з CLI інтерфейсом"""
    import argparse

    parser = argparse.ArgumentParser(description='Генератор сторінок дисциплін для WordPress')
    parser.add_argument('yaml_file', help='Шлях до YAML файлу з даними')
    parser.add_argument('--discipline', '-d', help='Код конкретної дисципліни для генерації')
    parser.add_argument('--template', '-t', default="discipline_template.html",
                    help='Файл шаблону в папці templates/')
    parser.add_argument('--all', '-a', action='store_true', help='Генерувати сторінки для всіх дисциплін')
    parser.add_argument('--index', '-i', action='store_true', help='Створити індексну сторінку')
    parser.add_argument('--output', '-o', help='Вихідний файл або папка')

    args = parser.parse_args()

    yaml_file = Path("data") / args.yaml_file

    if not Path(yaml_file).exists():
        print(f"❌ YAML файл не знайдено: {yaml_file}")
        return

    if args.discipline:
        # Генеруємо одну дисципліну

        # Создаём папку disciplines, если её нет
        output_dir = Path("disciplines")
        output_dir.mkdir(exist_ok=True)

        # Формируем безопасное имя файла
        safe_name = args.discipline.replace(' ', '_').replace('/', '_')
        output_file = output_dir / f"{safe_name}.html"

        # Генерируем страницу для одной дисциплины
        generate_discipline_page(yaml_file, args.discipline, output_file, args.template)

    elif args.all:
        # Генеруємо всі дисципліни
        output_dir = args.output if args.output else "disciplines"
        generate_all_disciplines(yaml_file, output_dir)

    elif args.index:
        # Створюємо папку disciplines, якщо її немає
        output_dir = Path("disciplines")
        output_dir.mkdir(exist_ok=True)
        
        # Вихідний файл або index.html у папці disciplines
        output_file = Path(args.output) if args.output else output_dir / "index.html"
        
        generate_index_page(yaml_file, output_file)

    else:
        print("❌ Оберіть одну з опцій: --discipline, --all, або --index")
        print("💡 Приклади:")
        print("  python script.py data.yaml -d 'ПО 01'")
        print("  python script.py data.yaml --all")
        print("  python script.py data.yaml --index")
        print("  python script.py data.yaml --all --template custom_template.html")

if __name__ == "__main__":
    main()
