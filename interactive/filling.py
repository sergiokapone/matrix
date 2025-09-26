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
