@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Hay chay cai_dat.cmd truoc.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" retrain_model.py
set "EXIT_CODE=%errorlevel%"
pause
exit /b %EXIT_CODE%
