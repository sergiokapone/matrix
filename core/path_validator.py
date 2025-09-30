import sys

def validate_paths(yaml_path, disciplines_dir):
    """Перевірка існування файлів та папок"""
    if not yaml_path.exists():
        print(f"❌ YAML файл не знайдено: {yaml_path}")
        sys.exit(1)
        
    if not disciplines_dir.exists():
        print(f"❌ Папка disciplines не знайдена: {disciplines_dir}")
        sys.exit(1)
