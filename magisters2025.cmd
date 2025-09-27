@echo off
echo Processing magister files
python discipline_page.py magister2025.yaml -a -c
python upload_disciplines.py magister2025.yaml
