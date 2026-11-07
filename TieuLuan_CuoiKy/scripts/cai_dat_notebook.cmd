@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0..\real_estate_ai"
if not exist ".venv\Scripts\python.exe" (
  py -3.12 -m venv .venv
  if errorlevel 1 goto failed
)
".venv\Scripts\python.exe" -m pip install -r requirements\notebook.txt
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m ipykernel install --user --name tieuluan-cuoiky --display-name "Python (TieuLuan_CuoiKy)"
if errorlevel 1 goto failed
echo.
echo Cai dat notebook thanh cong.
echo Trong VS Code: Select Kernel - Python Environments - real_estate_ai\.venv\Scripts\python.exe.
echo Kernel cua du an: Python (TieuLuan_CuoiKy).
echo Chon Restart Kernel and Run All de chay lai tu dau.
pause
exit /b 0
:failed
echo Cai dat notebook chua thanh cong. Xem loi ben tren.
pause
exit /b 1
