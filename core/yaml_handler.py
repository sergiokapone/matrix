import yaml
import sys


def load_yaml_data(yaml_path):
    """Завантаження YAML файлу"""
    try:
        with open(yaml_path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Помилка читання YAML файлу: {e}")
        sys.exit(1)