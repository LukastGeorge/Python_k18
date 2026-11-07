@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0..\real_estate_ai"
if not exist ".venv\Scripts\python.exe" (
  echo Chua co moi truong Python. Hay chay cai_dat.cmd truoc.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m backend.run_hourly --once
set "EXIT_CODE=%errorlevel%"
pause
exit /b %EXIT_CODE%
