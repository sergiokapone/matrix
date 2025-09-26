import pandas as pd
import yaml
import webbrowser
import argparse
import sys

from pathlib import Path
from datetime import datetime


def generate_matrices_from_yaml(
    yaml_file="curriculum.yaml", output_file="matrices.xlsx"
):
    """
    Генерує Excel файл з матрицями компетенцій та програмних результатів на основі YAML конфігу
    """

    # Завантажуємо YAML
    with open(yaml_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    metadata = config.get("metadata", {})
    disciplines = config["disciplines"]
    competencies = config["competencies"]
    program_results = config["program_results"]
    mappings = config["mappings"]

    # === МАТРИЦЯ КОМПЕТЕНЦІЙ ===
    comp_df = pd.DataFrame(
        "", index=list(competencies.keys()), columns=list(disciplines.keys())
    )

    # === МАТРИЦЯ ПРОГРАМНИХ РЕЗУЛЬТАТІВ ===
    prog_df = pd.DataFrame(
        "", index=list(program_results.keys()), columns=list(disciplines.keys())
    )

    # Заповнюємо матриці на основі mappings
    for discipline_code, mapping in mappings.items():
        if discipline_code in disciplines:
            # Компетенції
            for comp_code in mapping.get("competencies", []):
                if comp_code in comp_df.index:
                    comp_df.at[comp_code, discipline_code] = "+"

            # Програмні результати
            for prog_code in mapping.get("program_results", []):
                if prog_code in prog_df.index:
                    prog_df.at[prog_code, discipline_code] = "+"

    # Створюємо багаторівневі заголовки колонок
    comp_columns = pd.MultiIndex.from_tuples(
        [(disciplines[code], code) for code in comp_df.columns],
        names=["Дисципліна", "Код"],
    )

    prog_columns = pd.MultiIndex.from_tuples(
        [(disciplines[code], code) for code in prog_df.columns],
        names=["Дисципліна", "Код"],
    )

    comp_df.columns = comp_columns
    prog_df.columns = prog_columns

    # Зберігаємо в один Excel файл з трьома листами
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        comp_df.to_excel(writer, sheet_name="Компетентності")
        prog_df.to_excel(writer, sheet_name="Програмні результати")

        # === ЗВЕДЕНА ТАБЛИЦЯ ===
        summary_data = []
        for disc_code, disc_name in disciplines.items():
            mapping = mappings.get(disc_code, {})
            comps = mapping.get("competencies", [])
            progs = mapping.get("program_results", [])

            summary_data.append(
                {
                    "Код": disc_code,
                    "Дисципліна": disc_name,
                    "Компетенції": ", ".join(comps) if comps else "",
                    "Програмні результати": ", ".join(progs) if progs else "",
                    "Кількість компетенцій": len(comps),
                    "Кількість ПРН": len(progs),
                }
            )

        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name="Зведена таблиця", index=False)

        # Налаштовуємо ширину колонок для зведеної таблиці
        worksheet = writer.sheets["Зведена таблиця"]
        worksheet.column_dimensions["A"].width = 10  # Код
        worksheet.column_dimensions["B"].width = 50  # Дисципліна
        worksheet.column_dimensions["C"].width = 40  # Компетенції
        worksheet.column_dimensions["D"].width = 40  # Програмні результати
        worksheet.column_dimensions["E"].width = 15  # Кількість компетенцій
        worksheet.column_dimensions["F"].width = 15  # Кількість ПРН

    print(f"✅ Матриці згенеровано: {output_file}")
    print(f"📊 Компетенції: {len(competencies)} x {len(disciplines)}")
    print(f"📊 Програмні результати: {len(program_results)} x {len(disciplines)}")
    print(f"📋 Зведена таблиця: {len(disciplines)} дисциплін")


def interactive_fill_mappings(yaml_file="curriculum.yaml"):
    """
    Інтерактивне заповнення відповідностей між дисциплінами і компетенціями/результатами
    """
    # Завантажуємо конфігурацію
    with open(yaml_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    disciplines = config["disciplines"]
    competencies = config["competencies"]
    program_results = config["program_results"]
    mappings = config.get("mappings", {})

    # Знаходимо незаповнені дисципліни
    unfilled = [code for code in disciplines.keys() if code not in mappings]

    if not unfilled:
        print("🎉 Всі дисципліни вже заповнені!")
        return

    print(f"📝 Знайдено {len(unfilled)} незаповнених дисциплін")
    print("=" * 60)

    for i, disc_code in enumerate(unfilled):
        print(f"\n[{i + 1}/{len(unfilled)}] {disc_code}: {disciplines[disc_code]}")
        print("-" * 50)

        # Показуємо компетенції
        print("\n🎯 КОМПЕТЕНЦІЇ:")
        comp_list = list(competencies.keys())
        for j, comp_code in enumerate(comp_list):
            print(f"{j + 1:2d}. {comp_code}: {competencies[comp_code][:60]}...")

        # Вибір компетенцій
        print("\nВиберіть компетенції (номери через кому, або Enter для пропуску):")
        comp_input = input("Компетенції: ").strip()
        selected_comps = []

        if comp_input:
            try:
                indices = [int(x.strip()) - 1 for x in comp_input.split(",")]
                selected_comps = [
                    comp_list[i] for i in indices if 0 <= i < len(comp_list)
                ]
                print(f"✅ Обрано: {', '.join(selected_comps)}")
            except:
                print("❌ Некоректний ввід, пропускаю компетенції")

        # Показуємо програмні результати
        print("\n🎯 ПРОГРАМНІ РЕЗУЛЬТАТИ:")
        prog_list = list(program_results.keys())
        for j, prog_code in enumerate(prog_list):
            print(f"{j + 1:2d}. {prog_code}: {program_results[prog_code][:60]}...")

        # Вибір результатів
        print(
            "\nВиберіть програмні результати (номери через кому, або Enter для пропуску):"
        )
        prog_input = input("Результати: ").strip()
        selected_progs = []

        if prog_input:
            try:
                indices = [int(x.strip()) - 1 for x in prog_input.split(",")]
                selected_progs = [
                    prog_list[i] for i in indices if 0 <= i < len(prog_list)
                ]
                print(f"✅ Обрано: {', '.join(selected_progs)}")
            except:
                print("❌ Некоректний ввід, пропускаю результати")

        # Зберігаємо вибір
        mappings[disc_code] = {
            "competencies": selected_comps,
            "program_results": selected_progs,
        }

        # Автозбереження
        config["mappings"] = mappings
        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.dump(
                config,
                f,
                allow_unicode=True,
                default_flow_style=False,
                indent=2,
                sort_keys=False,
            )

        print(f"💾 Збережено {disc_code}")

        # Питаємо чи продовжувати
        if i < len(unfilled) - 1:
            cont = input("\nПродовжити? (Enter - так, q - вихід): ").strip().lower()
            if cont == "q":
                break

    print(f"\n🎉 Заповнення завершено! Заповнено {len(mappings)} дисциплін")


def generate_html_report(yaml_file="curriculum.yaml"):
    """
    Генерує HTML звіт з кольоровими таблицями та інтерактивними підказками
    """
    # Завантажуємо дані
    with open(yaml_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    metadata = config.get("metadata", {})
    disciplines = config["disciplines"]
    competencies = config["competencies"]
    program_results = config["program_results"]
    mappings = config.get("mappings", {})
    
    # Створюємо HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{metadata.get('title', 'Матриці компетенцій')} - Звіт</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            table {{ border-collapse: collapse; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: center; }}
            th {{ background-color: #f2f2f2; font-weight: bold; }}
            .filled {{ background-color: #d4edda; color: #155724; font-weight: bold; }}
            .empty {{ background-color: #f8f9fa; }}
            .discipline-header {{ background-color: #e9ecef; writing-mode: vertical-rl; text-orientation: mixed; }}
            .stats {{ background-color: #d1e7dd; padding: 15px; margin: 20px 0; border-radius: 5px; }}
            .metadata {{ background-color: #e7f3ff; padding: 15px; margin: 20px 0; border-radius: 5px; border-left: 4px solid #0066cc; }}
            .unfilled {{ color: #721c24; background-color: #f8d7da; padding: 10px; margin: 10px 0; }}
            
            /* Стилі для підказок */
            .tooltip-trigger {{
                position: relative;
                cursor: help;
                color: #0066cc;
                font-weight: bold;
                text-decoration: underline;
                text-decoration-style: dotted;
            }}
            
            .tooltip-trigger:hover {{
                color: #004499;
            }}
            
            .tooltip {{
                position: absolute;
                background: #333;
                color: white;
                padding: 8px 12px;
                border-radius: 6px;
                font-size: 0.85em;
                font-weight: normal;
                max-width: 300px;
                word-wrap: break-word;
                z-index: 1000;
                box-shadow: 0 4px 8px rgba(0,0,0,0.3);
                opacity: 0;
                transform: translateY(-5px);
                transition: all 0.2s ease;
                pointer-events: none;
                white-space: normal;
                line-height: 1.3;
            }}
            
            .tooltip.show {{
                opacity: 1;
                transform: translateY(0);
            }}
            
            .tooltip::after {{
                content: '';
                position: absolute;
                top: 100%;
                left: 50%;
                margin-left: -5px;
                border-width: 5px;
                border-style: solid;
                border-color: #333 transparent transparent transparent;
            }}
        </style>
    </head>
    <body>
        <h1>📊 {metadata.get('title', 'Звіт по матрицях компетенцій')}</h1>
    """
    
    # Блок метаданих
    if metadata:
        html += '<div class="metadata">'
        html += '<h3>ℹ️ Інформація про програму</h3>'
        
        if metadata.get('university'):
            html += f'<p><strong>ВНЗ:</strong> {metadata["university"]}</p>'
        if metadata.get('faculty'):
            html += f'<p><strong>Підрозділ:</strong> {metadata["faculty"]}</p>'
        if metadata.get('department'):
            html += f'<p><strong>Кафедра:</strong> {metadata["department"]}</p>'
        if metadata.get('specialty'):
            html += f'<p><strong>Спеціальність:</strong> {metadata["specialty"]}</p>'
        if metadata.get('specialization'):
            html += f'<p><strong>Спеціалізація:</strong> {metadata["specialization"]}</p>'
        if metadata.get('degree'):
            html += f'<p><strong>Освітній рівень:</strong> {metadata["degree"]}</p>'
        if metadata.get('credits_total'):
            html += f'<p><strong>Обсяг програми:</strong> {metadata["credits_total"]} кредитів ЄКТС</p>'
        if metadata.get('study_years'):
            html += f'<p><strong>Термін навчання:</strong> {metadata["study_years"]} роки</p>'
        if metadata.get('website'):
            html += f'<p><strong>Сайт:</strong> <a href="{metadata["website"]}" target="_blank">{metadata["website"]}</a></p>'
        if metadata.get('version'):
            html += f'<p><strong>Версія матриці:</strong> {metadata["version"]}</p>'
        if metadata.get('last_updated'):
            html += f'<p><strong>Останнє оновлення:</strong> {metadata["last_updated"]}</p>'
        
        contacts = metadata.get('contacts', {})
        if contacts:
            html += '<p><strong>Контакти:</strong> '
            contact_info = []
            if contacts.get('email'):
                contact_info.append(f'📧 {contacts["email"]}')
            if contacts.get('phone'):
                contact_info.append(f'📞 {contacts["phone"]}')
            html += ', '.join(contact_info) + '</p>'
        
        html += '</div>'
    
    html += f'<p><strong>Звіт згенеровано:</strong> {datetime.now().strftime("%d.%m.%Y о %H:%M")}</p>'
    
    # Статистика
    unfilled_disciplines = [code for code in disciplines.keys() if code not in mappings]
    
    html += f"""
    <div class="stats">
        <h3>📈 Статистика</h3>
        <p><strong>Всього дисциплін:</strong> {len(disciplines)}</p>
        <p><strong>Заповнено відповідностей:</strong> {len(mappings)}</p>
        <p><strong>Залишилось заповнити:</strong> {len(unfilled_disciplines)}</p>
    </div>
    """
    
    if unfilled_disciplines:
        html += '<div class="unfilled"><h4>⚠️ Незаповнені дисципліни:</h4><ul>'
        for code in unfilled_disciplines:
            html += f'<li>{code}: {disciplines[code]}</li>'
        html += '</ul></div>'
    
    # Матриця компетенцій
    html += '<h2>🎯 Матриця компетенцій</h2><table>'
    
    # Заголовок таблиці
    html += '<tr><th>Компетенція</th>'
    for disc_code in disciplines.keys():
        html += f'<th class="discipline-header" title="{disciplines[disc_code]}">{disc_code}</th>'
    html += '</tr>'
    
    # Рядки компетенцій
    for comp_code, comp_desc in competencies.items():
        html += f'<tr><td title="{comp_desc}"><strong>{comp_code}</strong></td>'
        for disc_code in disciplines.keys():
            has_mapping = (disc_code in mappings and 
                          comp_code in mappings[disc_code].get("competencies", []))
            cell_class = "filled" if has_mapping else "empty"
            cell_content = "+" if has_mapping else ""
            html += f'<td class="{cell_class}">{cell_content}</td>'
        html += '</tr>'
    
    html += '</table>'
    
    # Матриця програмних результатів
    html += '<h2>🎯 Матриця програмних результатів</h2><table>'
    
    # Заголовок таблиці
    html += '<tr><th>Програмний результат</th>'
    for disc_code in disciplines.keys():
        html += f'<th class="discipline-header" title="{disciplines[disc_code]}">{disc_code}</th>'
    html += '</tr>'
    
    # Рядки результатів
    for prog_code, prog_desc in program_results.items():
        html += f'<tr><td title="{prog_desc}"><strong>{prog_code}</strong></td>'
        for disc_code in disciplines.keys():
            has_mapping = (disc_code in mappings and 
                          prog_code in mappings[disc_code].get("program_results", []))
            cell_class = "filled" if has_mapping else "empty"
            cell_content = "+" if has_mapping else ""
            html += f'<td class="{cell_class}">{cell_content}</td>'
        html += '</tr>'
    
    html += '</table>'
    
    # Додаткова таблиця: Дисципліна → Компетенції, ПРН
    html += '<h2>📋 Зведена таблиця по дисциплінах</h2>'
    html += '<table style="width: 100%;">'
    html += '<tr><th style="width: 15%;">Код</th><th style="width: 30%;">Дисципліна</th><th style="width: 27.5%;">Компетенції</th><th style="width: 27.5%;">Програмні результати</th></tr>'
    
    for disc_code, disc_name in disciplines.items():
        mapping = mappings.get(disc_code, {})
        comps = mapping.get("competencies", [])
        progs = mapping.get("program_results", [])
        
        # Форматуємо списки з підказками
        if comps:
            comp_spans = [f'<span class="tooltip-trigger" data-tooltip="{competencies.get(comp, comp)}">{comp}</span>' for comp in comps]
            comp_text = ", ".join(comp_spans)
        else:
            comp_text = "<em>не заповнено</em>"
            
        if progs:
            prog_spans = [f'<span class="tooltip-trigger" data-tooltip="{program_results.get(prog, prog)}">{prog}</span>' for prog in progs]
            prog_text = ", ".join(prog_spans)
        else:
            prog_text = "<em>не заповнено</em>"
        
        # Визначаємо стиль рядка
        row_class = "" if (comps or progs) else 'style="background-color: #f8d7da;"'
        
        html += f'<tr {row_class}>'
        html += f'<td><strong><span class="tooltip-trigger" data-tooltip="{disc_name}">{disc_code}</span></strong></td>'
        html += f'<td style="text-align: left; padding-left: 10px;">{disc_name}</td>'
        html += f'<td style="text-align: left; font-size: 0.9em;">{comp_text}</td>'
        html += f'<td style="text-align: left; font-size: 0.9em;">{prog_text}</td>'
        html += '</tr>'
    
    html += '</table>'
    
    # Пам'ятка з розшифровкою компетенцій та програмних результатів
    html += '<h2>📖 Пам\'ятка: розшифровка компетенцій та програмних результатів</h2>'
    
    # Компетенції
    html += '<h3>🎯 Компетенції</h3>'
    html += '<table style="width: 100%; font-size: 0.9em;">'
    html += '<tr><th style="width: 10%;">Код</th><th style="width: 90%;">Опис</th></tr>'
    
    for comp_code, comp_desc in competencies.items():
        html += f'<tr><td style="text-align: center;"><strong>{comp_code}</strong></td>'
        html += f'<td style="text-align: left; padding-left: 10px;">{comp_desc}</td></tr>'
    
    html += '</table>'
    
    # Програмні результати
    html += '<h3>📋 Програмні результати навчання</h3>'
    html += '<table style="width: 100%; font-size: 0.9em;">'
    html += '<tr><th style="width: 10%;">Код</th><th style="width: 90%;">Опис</th></tr>'
    
    for prog_code, prog_desc in program_results.items():
        html += f'<tr><td style="text-align: center;"><strong>{prog_code}</strong></td>'
        html += f'<td style="text-align: left; padding-left: 10px;">{prog_desc}</td></tr>'
    
    html += '</table>'

    # Додаємо JavaScript для підказок
    html += """
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        const triggers = document.querySelectorAll('.tooltip-trigger');
        let currentTooltip = null;
        
        triggers.forEach(trigger => {
            trigger.addEventListener('mouseenter', function(e) {
                // Видаляємо попередню підказку
                if (currentTooltip) {
                    currentTooltip.remove();
                    currentTooltip = null;
                }
                
                const tooltipText = this.getAttribute('data-tooltip');
                if (!tooltipText) return;
                
                // Створюємо нову підказку
                const tooltip = document.createElement('div');
                tooltip.className = 'tooltip show';
                tooltip.textContent = tooltipText;
                
                // Додаємо до body
                document.body.appendChild(tooltip);
                currentTooltip = tooltip;
                
                // Позиціонуємо підказку відносно курсора
                const rect = this.getBoundingClientRect();
                const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
                const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;
                
                // Позиція зверху від елементу
                let left = rect.left + scrollLeft + (rect.width / 2) - (tooltip.offsetWidth / 2);
                let top = rect.top + scrollTop - tooltip.offsetHeight - 10;
                
                // Якщо виходить за верхню межу, показуємо знизу
                if (top < scrollTop + 10) {
                    top = rect.bottom + scrollTop + 10;
                    // Змінюємо стрілочку
                    tooltip.style.setProperty('--arrow-direction', 'up');
                }
                
                // Якщо виходить за ліву межу
                if (left < scrollLeft + 10) {
                    left = scrollLeft + 10;
                }
                
                // Якщо виходить за праву межу
                if (left + tooltip.offsetWidth > scrollLeft + window.innerWidth - 10) {
                    left = scrollLeft + window.innerWidth - tooltip.offsetWidth - 10;
                }
                
                tooltip.style.left = left + 'px';
                tooltip.style.top = top + 'px';
            });
            
            trigger.addEventListener('mouseleave', function() {
                if (currentTooltip) {
                    currentTooltip.classList.remove('show');
                    setTimeout(() => {
                        if (currentTooltip) {
                            currentTooltip.remove();
                            currentTooltip = null;
                        }
                    }, 200);
                }
            });
        });
        
        // Видаляємо підказку при прокрутці або кліку
        window.addEventListener('scroll', function() {
            if (currentTooltip) {
                currentTooltip.remove();
                currentTooltip = null;
            }
        });
        
        document.addEventListener('click', function() {
            if (currentTooltip) {
                currentTooltip.remove();
                currentTooltip = null;
            }
        });
        
        console.log('Tooltip script loaded. Found triggers:', triggers.length);
    });
    </script>
    </body></html>"""
    
    # Зберігаємо та відкриваємо
    temp_file = Path(yaml_file).with_suffix('.html')
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    webbrowser.open(f'file://{temp_file.absolute()}')
    print(f"📊 HTML звіт відкрито в браузері: {temp_file}")


def show_statistics(yaml_file="curriculum.yaml"):
    """
    Показує детальну статистику в консолі
    """
    with open(yaml_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    disciplines = config["disciplines"]
    competencies = config["competencies"]
    program_results = config["program_results"]
    mappings = config.get("mappings", {})

    print("📊 СТАТИСТИКА МАТРИЦЬ")
    print("=" * 50)

    # Загальна інформація
    print(f"📚 Всього дисциплін: {len(disciplines)}")
    print(f"🎯 Всього компетенцій: {len(competencies)}")
    print(f"📋 Всього програмних результатів: {len(program_results)}")
    print(f"✅ Заповнено відповідностей: {len(mappings)}")
    print(f"❌ Незаповнено: {len(disciplines) - len(mappings)}")

    if len(mappings) == 0:
        print("\n⚠️  Відповідності ще не заповнені!")
        return

    # Статистика по компетенціям
    comp_usage = {}
    for mapping in mappings.values():
        for comp in mapping.get("competencies", []):
            comp_usage[comp] = comp_usage.get(comp, 0) + 1

    print(f"\n🎯 ВИКОРИСТАННЯ КОМПЕТЕНЦІЙ:")
    print("-" * 30)
    for comp_code in sorted(competencies.keys()):
        count = comp_usage.get(comp_code, 0)
        print(f"{comp_code}: {count:2d} дисциплін")

    # Статистика по програмним результатам
    prog_usage = {}
    for mapping in mappings.values():
        for prog in mapping.get("program_results", []):
            prog_usage[prog] = prog_usage.get(prog, 0) + 1

    print(f"\n📋 ВИКОРИСТАННЯ ПРОГРАМНИХ РЕЗУЛЬТАТІВ:")
    print("-" * 30)
    for prog_code in sorted(program_results.keys()):
        count = prog_usage.get(prog_code, 0)
        print(f"{prog_code}: {count:2d} дисциплін")

    # Незаповнені дисципліни
    unfilled = [code for code in disciplines.keys() if code not in mappings]
    if unfilled:
        print(f"\n❌ НЕЗАПОВНЕНІ ДИСЦИПЛІНИ ({len(unfilled)}):")
        print("-" * 30)
        for code in unfilled:
            print(f"{code}: {disciplines[code]}")


def validate_data(yaml_file="curriculum.yaml"):
    """
    Перевіряє коректність даних у YAML файлі
    """
    try:
        with open(yaml_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Помилка читання YAML: {e}")
        return False

    print("🔍 ВАЛІДАЦІЯ ДАНИХ")
    print("=" * 30)

    errors = []
    warnings = []

    disciplines = config.get("disciplines", {})
    competencies = config.get("competencies", {})
    program_results = config.get("program_results", {})
    mappings = config.get("mappings", {})

    # Перевіряємо структуру
    if not disciplines:
        errors.append("Відсутня секція 'disciplines'")
    if not competencies:
        errors.append("Відсутня секція 'competencies'")
    if not program_results:
        errors.append("Відсутня секція 'program_results'")

    # Перевіряємо відповідності
    for disc_code, mapping in mappings.items():
        if disc_code not in disciplines:
            errors.append(f"Невідома дисципліна в mappings: {disc_code}")

        for comp in mapping.get("competencies", []):
            if comp not in competencies:
                errors.append(f"Невідома компетенція: {comp} (у {disc_code})")

        for prog in mapping.get("program_results", []):
            if prog not in program_results:
                errors.append(f"Невідомий програмний результат: {prog} (у {disc_code})")

    # Попередження про незаповнені дисципліни
    unfilled_count = len(disciplines) - len(mappings)
    if unfilled_count > 0:
        warnings.append(f"Незаповнено {unfilled_count} дисциплін")

    # Виводимо результати
    if errors:
        print("❌ ПОМИЛКИ:")
        for error in errors:
            print(f"  • {error}")

    if warnings:
        print("\n⚠️  ПОПЕРЕДЖЕННЯ:")
        for warning in warnings:
            print(f"  • {warning}")

    if not errors and not warnings:
        print("✅ Всі дані коректні!")
    elif not errors:
        print("✅ Критичних помилок не знайдено")

    return len(errors) == 0


def create_yaml_template(filename="curriculum.yaml"):
    """
    Створює YAML шаблон для редагування
    """

    template = {
        # Дисципліни: код -> повна назва
        "disciplines": {
            "ЗО 01": "Математичний аналіз",
            "ЗО 02": "Алгебра та геометрія",
            "ЗО 03": "Механіка",
            "ЗО 04": "Термодинаміка та молекулярна фізика",
            "ЗО 05": "Диференціальні рівняння",
            "ЗО 06": "Електрика та магнетизм",
            "ЗО 07": "Оптика",
            "ЗО 08": "Атомна фізика",
            "ЗО 09": "Українська мова за професійним спрямуванням",
            "ЗО 10": "Історія науки і техніки",
            "ЗО 11": "Основи здорового способу життя",
            "ЗО 12": "Практичний курс іноземної мови",
            "ЗО 13": "Екологія",
            "ЗО 14": "Філософські основи наукового пізнання",
            "ЗО 15": "Основи економіки",
            "ЗО 16": "Практичний курс іноземної мови професійного спрямування",
            "ЗО 17": "Безпека життєдіяльності та цивільній захист",
            "ЗО 18": "Права і свободи людини",
            "ЗО 19": "Хімія",
            "ЗО 20": "Теорія ймовірності та математична статистика",
            "ПО 01": "Програмування",
            "ПО 02": "Комп'ютерна графіка",
            "ПО 03": "Введення в спеціальність",
            "ПО 04": "Тензорний аналіз",
            "ПО 05": "Програмування С++",
            "ПО 06": "Класична механіка",
            "ПО 07": "Комп'ютерні пакети для представлення наукових результатів (Origin, LaTeX, Gnuplot)",
            "ПО 08": "Рівняння математичної фізики",
            "ПО 09": "Обчислювальні методи",
            "ПО 10": "Математичне моделювання та відкриті пакети прикладних програм",
            "ПО 11": "Теорія поля",
            "ПО 12": "Електродинаміка суцільних середовищ",
            "ПО 13": "Коливання та хвилі",
            "ПО 14": "Квантова механіка",
            "ПО 15": "Статистична фізика та основи фізики твердого тіла",
            "ПО 16": "Статистична радіофізика та оптика",
            "ПО 17": "Лабораторно-дослідницький практикум",
            "ПО 18": "Міждисциплінарна курсова робота",
            "ПО 19": "Основи наукових досліджень",
            "ПО 20": "Переддипломна практика",
            "ПО 21": "Дипломне проєктування",
        },
        # Компетенції: код -> опис
        "competencies": {
            "ЗК 1": "Здатність застосовувати знання у практичних ситуаціях",
            "ЗК 2": "Знання та розуміння предметної області",
            "ЗК 3": "Здатність спілкуватися державною мовою",
            "ЗК 4": "Здатність спілкуватися іноземною мовою",
            "ЗК 5": "Здатність використання ІКТ",
            "ЗК 6": "Здатність проведення досліджень",
            "ЗК 7": "Здатність до пошуку та аналізу інформації",
            "ЗК 8": "Здатність до міжособистісної взаємодії",
            "ЗК 9": "Здатність працювати автономно",
            "ЗК 10": "Здатність здійснювати безпечну діяльність",
            "ЗК 11": "Здатність реалізувати права і обов'язки",
            "ЗК 12": "Здатність зберігати культурні цінності",
            "ЗК 13": "Здатність критично оцінювати результати",
            "ЗК 14": "Здатність до самостійного навчання",
            "ЗК 15": "Військова підготовка",
            "ФК 1": "Участь у наукових проектах",
            "ФК 2": "Участь у експериментах та дослідженнях",
            "ФК 3": "Виготовлення експериментальних зразків",
            "ФК 4": "Впровадження результатів досліджень",
            "ФК 5": "Розвиток компетентностей у прикладній фізиці",
            "ФК 6": "Використання сучасних теоретичних уявлень",
            "ФК 7": "Методи теоретичного дослідження",
            "ФК 8": "Робота в колективі",
            "ФК 9": "Проведення наукових досліджень",
            "ФК 10": "Застосування математичного апарату",
            "ФК 11": "Використання професійно-орієнтованих знань",
        },
        # Програмні результати навчання
        "program_results": {
            "ПРН 1": "Знати сучасну фізику на достатньому рівні",
            "ПРН 2": "Застосовувати математичні методи",
            "ПРН 3": "Застосовувати технології експериментального дослідження",
            "ПРН 4": "Застосовувати моделі для дослідження явищ",
            "ПРН 5": "Вибирати ефективні методи досліджень",
            "ПРН 6": "Відшуковувати науково-технічну інформацію",
            "ПРН 7": "Аналізувати науково-технічну інформацію",
            "ПРН 8": "Спілкуватися професійно державною та англійською мовами",
            "ПРН 9": "Презентувати результати досліджень",
            "ПРН 10": "Планувати професійну діяльність",
            "ПРН 11": "Знати цілі сталого розвитку",
            "ПРН 12": "Розуміти закономірності розвитку прикладної фізики",
            "ПРН 13": "Оцінювати витрати та наслідки проектів",
            "ПРН 14": "Використовувати методи дослідження матеріалів",
            "ПРН 15": "Знання методології наукових досліджень",
            "ПРН 16": "Знання математичних та комп'ютерних методів",
            "ПРН 17": "Знання професійно-орієнтованих дисциплін",
        },
        # ГОЛОВНЕ! Відповідності: дисципліна -> які компетенції/результати вона забезпечує
        "mappings": {
            # Приклади заповнення - решту додавайте через інтерактивний режим!
            "ЗО 01": {  # Математичний аналіз
                "competencies": ["ЗК 1", "ЗК 2", "ЗК 14", "ФК 6", "ФК 7"],
                "program_results": ["ПРН 1", "ПРН 2", "ПРН 16"],
            },
            "ПО 01": {  # Програмування
                "competencies": ["ЗК 1", "ЗК 5", "ЗК 9", "ФК 5", "ФК 10"],
                "program_results": ["ПРН 2", "ПРН 4", "ПРН 16"],
            },
        },
    }

    # Зберігаємо YAML файл
    with open(filename, "w", encoding="utf-8") as f:
        yaml.dump(
            template,
            f,
            allow_unicode=True,
            default_flow_style=False,
            indent=2,
            sort_keys=False,
        )

    print(f"📝 YAML шаблон створено: {filename}")
    print("🎯 Використовуй інтерактивний режим для заповнення решти!")


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
    yaml_file = args.yaml_file

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
