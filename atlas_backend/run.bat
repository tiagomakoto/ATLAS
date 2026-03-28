@echo off
echo Iniciando ATLAS Backend...
python -m uvicorn main:app --reload --log-level info
pause