import yaml


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

    print("\n🎯 ВИКОРИСТАННЯ КОМПЕТЕНЦІЙ:")
    print("-" * 30)
    for comp_code in sorted(competencies.keys()):
        count = comp_usage.get(comp_code, 0)
        print(f"{comp_code}: {count:2d} дисциплін")

    # Статистика по програмним результатам
    prog_usage = {}
    for mapping in mappings.values():
        for prog in mapping.get("program_results", []):
            prog_usage[prog] = prog_usage.get(prog, 0) + 1

    print("\n📋 ВИКОРИСТАННЯ ПРОГРАМНИХ РЕЗУЛЬТАТІВ:")
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