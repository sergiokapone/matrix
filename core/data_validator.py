import yaml


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