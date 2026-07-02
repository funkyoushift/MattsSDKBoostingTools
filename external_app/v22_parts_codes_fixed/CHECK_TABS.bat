@echo off
cd /d "%~dp0"
py -B -c "import json; d=json.load(open('resources/ui_layout.json',encoding='utf-8')); print([t.get('label') for t in d.get('tabs',[])])"
pause
