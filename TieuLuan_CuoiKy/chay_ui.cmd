@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0real_estate_ai"
if not exist ".venv\Scripts\python.exe" goto missing
".venv\Scripts\python.exe" -c "import flask" >nul 2>&1
if errorlevel 1 goto missing
echo Dang mo UI voi SQLite tai http://127.0.0.1:8000
echo Du lieu luu trong storage\real_estate.db. Giu cua so nay mo, Ctrl+C de dung.
".venv\Scripts\python.exe" -m backend.web_app --backend sqlite --open-browser
set "EXIT_CODE=%errorlevel%"
pause
exit /b %EXIT_CODE%
:missing
echo Hay chay scripts\cai_dat.cmd trong TieuLuan_CuoiKy de cai moi truong va Flask.
pause
exit /b 1
