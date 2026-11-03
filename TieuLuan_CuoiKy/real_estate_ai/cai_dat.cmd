@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  py -3.12 -m venv .venv
  if errorlevel 1 goto failed
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
if not exist ".env" (
  copy ".env.example" ".env" >nul
  echo Hay mo .env va dien mat khau PostgreSQL truoc khi chay demo.
)
echo Cai dat xong. Chay chay_demo.cmd de thu mot lan.
pause
exit /b 0
:failed
echo Cai dat chua thanh cong. Xem thong bao loi ben tren.
pause
exit /b 1
