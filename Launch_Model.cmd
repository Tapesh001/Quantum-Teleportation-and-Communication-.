@echo off
setlocal
cd /d "%~dp0"
python -c "import sys,sqlite3; assert sys.version_info >= (3,8)" >nul 2>nul
if not errorlevel 1 (
    python run.py
) else (
    py -3 run.py
)
if errorlevel 1 pause
