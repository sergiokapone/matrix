@echo off
echo Processing magister files
python ../create_discipline_page.py ../data/bachelor2024.yaml -a
python ../create_discipline_page.py ../data/bachelor2024.yaml -i
python ../create_discipline_page.py ../data/bachelor2024.yaml -pi
python ../create_discipline_page.py ../data/bachelor2024.yaml -ui


