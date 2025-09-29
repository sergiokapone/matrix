@echo off
chcp 65001 > nul
echo Processing magister files
python create_discipline_page.py magister2025.yaml -d "ПО 01"
python upload_disciplines.py magister2025.yaml
