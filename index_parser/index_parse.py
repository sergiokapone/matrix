import yaml
from pathlib import Path
import re

def parse_index_links(index_file_path="disciplines/index.html", data_yaml=None):
    """
    Заменяет локальные ссылки на дисциплины в HTML-файле на ссылки из WordPress.
    
    Функция выполняет следующие действия:
    1. Загружает соответствия кодов дисциплин и WP-ссылок из YAML-файла
    2. Проверяет совпадение метаданных (год, степень) между основным YAML и WP-ссылками
    3. Находит все ссылки формата 'ЗО_01.html', 'ПО_02.html' и т.д.
    4. Заменяет их на соответствующие WordPress URL
    
    Args:
        index_file_path (str): Путь к HTML-файлу с дисциплинами. 
            По умолчанию "disciplines/index.html"
        data_yaml (str, optional): Путь к основному YAML-файлу с метаданными.
            Используется для проверки соответствия года и степени.
            Если None, проверка метаданных пропускается.
    
    Returns:
        None
    
    Side Effects:
        - Перезаписывает файл index_file_path с обновленными ссылками
        - Выводит статус операции в консоль
    
    Формат YAML с WP-ссылками (wp_links/wp_links_*.yaml):
        year: "2024"
        degree: "bachelor"
        links:
          ЗО 01: "https://example.com/zo-01"
          ПО 02: "https://example.com/po-02"
    
    Поддерживаемые коды дисциплин:
        - ЗО (Загальноосвітні)
        - ПО (Професійні обов'язкові)
        - ПВ (Професійні вибіркові)
        - НК (Нормативні курси)
        - ВК (Вибіркові курси)
    
    Examples:
        >>> parse_index_links("disciplines/index.html", "data/bachelor_2024.yaml")
        ✅ href в disciplines/index.html заменены на WP ссылки для ЗО_XX / ПО_XX
        
        >>> parse_index_links(data_yaml="data/master_2023.yaml")
        ❌ Метаданные не совпадают: WP (2024/bachelor) vs YAML (2023/master)
    
    Notes:
        - Ссылки вида 'ЗО_01.html' и 'ЗО 01.html' обрабатываются одинаково
        - Если код дисциплины не найден в YAML, подставляется "#"
        - Название YAML-файла с WP-ссылками формируется автоматически 
          из имени основного YAML (wp_links_<stem>.yaml)
    """
    # Проверяем существование HTML-файла с индексом дисциплин
    index_file = Path(index_file_path)
    if not index_file.exists():
        print(f"❌ Файл {index_file} не найден")
        return
    
    # Формируем путь к YAML-файлу с WordPress ссылками
    # Используем stem (имя без расширения) основного YAML для поиска соответствующего файла
    data_yaml_stem = Path(data_yaml).stem
    wp_links_yaml = Path("wp_links") / f"wp_links_{data_yaml_stem}.yaml"

    # Загружаем данные о WordPress ссылках из YAML
    with open(wp_links_yaml, encoding="utf-8") as f:
        wp_data = yaml.safe_load(f)
    
    # Извлекаем словарь соответствий "код дисциплины" -> "WP URL"
    wp_links = wp_data.get("links", {})
    # Извлекаем метаданные для проверки совпадения
    wp_year = wp_data.get("year", "")
    wp_degree = wp_data.get("degree", "")

    # Проверяем соответствие метаданных с основным YAML (если указан)
    if data_yaml:
        with open(data_yaml, encoding="utf-8") as f:
            meta_data = yaml.safe_load(f)
        
        # Получаем год и степень из основного YAML
        year = meta_data.get("metadata", {}).get("year", "")
        degree = meta_data.get("metadata", {}).get("degree", "")
        
        # Если метаданные не совпадают, прерываем выполнение
        if wp_year != year or wp_degree != degree:
            print(f"❌ Метаданные не совпадают: WP ({wp_year}/{wp_degree}) vs YAML ({year}/{degree}). Парсинг отменен.")
            return

    # Читаем содержимое HTML-файла
    html = index_file.read_text(encoding="utf-8")
    
    # Регулярное выражение для поиска ссылок на дисциплины:
    # - Ищет href="XX_NN.html" или href="XX NN.html"
    # - XX - двухбуквенный код типа дисциплины (ЗО, ПО, ПВ, НК, ВК)
    # - NN - двузначный номер (с опциональной дробной частью вида .1, .2)
    # Примеры: "ЗО_01.html", "ПО 02.html", "ПВ_03.1.html"
    pattern = re.compile(r'href="((ЗО|ПО|ПВ|НК|ВК)[ _]\d{2}(?:\.\d+)?)\.html"')

    def replace_href(match):
        """
        Callback-функция для замены найденного href на WordPress URL.
        
        Args:
            match (re.Match): Объект совпадения регулярного выражения
        
        Returns:
            str: Новый атрибут href с WordPress URL или "#" если код не найден
        
        Notes:
            - Нормализует код дисциплины: заменяет '_' на пробел и убирает лишние пробелы
            - Использует замыкание для доступа к wp_links из внешней функции
        """
        # Извлекаем полный код дисциплины (например, "ЗО_01" или "ПО 02")
        # group(1) содержит весь код без .html
        code = match.group(1).replace('_', ' ').strip()
        
        # Ищем соответствующий WordPress URL в словаре
        # Если код не найден, используем заглушку "#"
        wp_url = wp_links.get(code, "#")
        
        # Возвращаем новый атрибут href
        return f'href="{wp_url}"'

    # Выполняем замену всех найденных ссылок
    html_new = pattern.sub(replace_href, html)
    
    # Сохраняем обновленный HTML обратно в файл
    index_file.write_text(html_new, encoding="utf-8")
    
    # Выводим сообщение об успешном выполнении
    print(f"✅ href в {index_file} заменены на WP ссылки для ЗО_XX / ПО_XX")