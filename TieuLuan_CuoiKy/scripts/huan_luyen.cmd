@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0..\real_estate_ai"
if not exist ".venv\Scripts\python.exe" (
  echo Hay chay cai_dat.cmd truoc.
  pause
  exit /b 1
)
set DB_BACKEND=sqlite
set OPENBLAS_NUM_THREADS=1
set OMP_NUM_THREADS=2
".venv\Scripts\python.exe" -m backend.train_vietnam --clean artifacts\vietnam\listings_clean.csv.gz --import-db
set "EXIT_CODE=%errorlevel%"
pause
exit /b %EXIT_CODE%
