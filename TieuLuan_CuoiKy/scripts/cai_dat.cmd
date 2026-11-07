@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0..\real_estate_ai"
if not exist ".venv\Scripts\python.exe" (
  py -3.12 -m venv .venv
  if errorlevel 1 goto failed
)
".venv\Scripts\python.exe" -m pip install -r requirements\base.txt
if errorlevel 1 goto failed
if not exist ".env" (
  copy ".env.example" ".env" >nul
  echo UI chinh dung SQLite. Chi can dien PostgreSQL khi chon backend PostgreSQL.
)
if not exist "artifacts\kingcounty\model.joblib" (
  set OPENBLAS_NUM_THREADS=1
  set OMP_NUM_THREADS=2
  set DB_BACKEND=sqlite
  ".venv\Scripts\python.exe" -m backend.train_kingcounty --import-db
  if errorlevel 1 goto failed
)
if not exist "artifacts\vietnam\model.joblib" (
  set OPENBLAS_NUM_THREADS=1
  set OMP_NUM_THREADS=2
  ".venv\Scripts\python.exe" -m backend.train_vietnam --clean artifacts\vietnam\listings_clean.csv.gz
  if errorlevel 1 goto failed
)
echo Cai dat xong. Chay TieuLuan_CuoiKy\chay_ui.cmd de mo giao dien web voi SQLite.
echo Chay scripts\chay_demo.cmd de thu pipeline mot lan theo cau hinh .env.
pause
exit /b 0
:failed
echo Cai dat chua thanh cong. Xem thong bao loi ben tren.
pause
exit /b 1
