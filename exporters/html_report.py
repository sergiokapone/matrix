import webbrowser

from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from datetime import datetime

from core.yaml_handler import load_yaml_data

def generate_html_report(yaml_file="curriculum.yaml"):
    config = load_yaml_data(yaml_file)

    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("report_template.html")

    disciplines = config["disciplines"]
    competencies = config["competencies"]
    program_results = config["program_results"]
    mappings = config.get("mappings", {})
    metadata = config.get("metadata", {})
    unfilled_disciplines = [code for code in disciplines if code not in mappings]

    html_content = template.render(
        metadata=metadata,
        disciplines=disciplines,
        competencies=competencies,
        program_results=program_results,
        mappings=mappings,
        unfilled_disciplines=unfilled_disciplines,
        generated_at=datetime.now().strftime("%d.%m.%Y о %H:%M")
    )

    # Папка, де лежить main.py
    base_dir = Path.cwd()

    gh_pages_dir = base_dir / "docs"


    temp_file = gh_pages_dir / Path(yaml_file).with_suffix(".html").name

    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    webbrowser.open(f"file://{temp_file.absolute()}")
    print(f"📊 HTML звіт відкрито в браузері: {temp_file}")
