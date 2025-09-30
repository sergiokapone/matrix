@echo off
echo Processing magister files
python create_discipline_page.py bachelor2024.yaml -d "ЗО 06"
python upload_disciplines.py bachelor2024.yaml
