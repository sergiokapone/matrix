from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from datetime import datetime
import yaml
import webbrowser

def generate_html_report(yaml_file="curriculum.yaml"):
    with open(yaml_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

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

    temp_file = Path(yaml_file).with_suffix(".html")
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    webbrowser.open(f"file://{temp_file.absolute()}")
    print(f"📊 HTML звіт відкрито в браузері: {temp_file}")
