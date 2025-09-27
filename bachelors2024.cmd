@echo off
echo Processing magister files
python discipline_page.py bachelor2024.yaml -a -c
python upload_disciplines.py bachelor2024.yaml
