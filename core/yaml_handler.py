import yaml


def load_yaml_data(yaml_file):
    """Завантажує дані з YAML файлу"""
    with open(yaml_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)