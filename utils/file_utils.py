from pathlib import Path


def check_file_exists(yaml_file):
    """Перевірка існування YAML файлу"""
    return Path(yaml_file).exists()