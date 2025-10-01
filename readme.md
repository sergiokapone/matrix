# Генератор сторінок дисциплін для WordPress

Цей проект дозволяє автоматично генерувати HTML-сторінки дисциплін із YAML-файлу та завантажувати їх на WordPress. Підтримує як окремі дисципліни, так і всі дисципліни одразу, а також індексну сторінку з усіма посиланнями.

---

## Зміст

- Встановлення
- Структура проекту
- Підготовка YAML
- Генерація сторінок
- Завантаження на WordPress
- CLI аргументи
- Приклади використання
- Ліцензія

---

## Встановлення

1. Клонувати репозиторій:

git clone https://github.com/yourusername/discipline-page-generator.git
cd discipline-page-generator

2. Створити та активувати віртуальне середовище (рекомендовано):

python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

3. Встановити залежності:

pip install -r requirements.txt

4. Створити `.env` файл для збереження параметрів WordPress (URL, логін, пароль, API ключі тощо).

---

## Структура проекту

.
├── data/
│   ├── disciplines.yaml       # Основні дані дисциплін
│   └── lecturers.yaml         # Дані про лекторів
├── templates/
│   ├── discipline_template.html
│   └── index_template.html
├── core/                      # Модулі обробки YAML, WP та валідаторів
├── index_parser/              # Модуль для парсингу index.html
├── create_discipline_page.py  # Головний скрипт CLI
└── README.md

---

## Підготовка YAML

- disciplines.yaml містить усі дисципліни та їх властивості:
  - Код дисципліни
  - Назва
  - Кредити
  - Контроль
  - Лектор (lecturer_id)
  - Піддисципліни (опціонально)
- lecturers.yaml містить дані лекторів (lecturer_id → дані про лектора).

Опціонально можна додати:
- elevative_disciplines – для додаткових дисциплін.
- mappings – відповідності компетенцій та програмних результатів.

---

## Генерація сторінок

- Окрема дисципліна:

python create_discipline_page.py data/disciplines.yaml -d "ПО 01"

- Всі дисципліни:

python create_discipline_page.py data/disciplines.yaml --all

- Індексна сторінка:

python create_discipline_page.py data/disciplines.yaml --index

---

## Завантаження на WordPress

1. Завантаження всіх сторінок дисциплін:

python create_discipline_page.py data/disciplines.yaml --upload

2. Завантаження індексної сторінки:

python create_discipline_page.py data/disciplines.yaml --upload-index

3. Підстановка посилань на сайті у index.html:

python create_discipline_page.py data/disciplines.yaml --parse-index

---

## CLI аргументи

- -d, --discipline : Код дисципліни для генерації
- -a, --all        : Генерація всіх дисциплін
- -i, --index      : Створення індексної сторінки
- -pi, --parse-index : Підстановка WP посилань в index.html
- -u, --upload     : Завантаження згенерованих сторінок на WP
- -ui, --upload-index : Завантаження index.html на WP
- -t, --template   : Вказати шаблон HTML
- -o, --output     : Вихідний файл або папка
- -c, --clean      : Очистити каталог перед генерацією

---

## Приклади використання

# Генерація однієї дисципліни
python create_discipline_page.py data.yaml -d "ПО 01"

# Генерація всіх дисциплін
python create_discipline_page.py data.yaml --all

# Генерація індексу та завантаження на WP
python create_discipline_page.py data.yaml --index --parse-index --upload-index

# Використання кастомного шаблону
python create_discipline_page.py data.yaml --all --template custom_template.html

---

## Ліцензія

MIT License © 2025
