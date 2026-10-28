@echo off
rem Lance le relais PC Class-Tech. Double clic suffit.
cd /d %~dp0..
if exist .venv\Scripts\python.exe (
  set RELAIS_PY=.venv\Scripts\python.exe
) else (
  set RELAIS_PY=python
)
%RELAIS_PY% -c "import fastapi" >nul 2>&1
if errorlevel 1 %RELAIS_PY% -m pip install -r backend/requirements.txt
%RELAIS_PY% relais\lancer_relais.py
pause
