@echo off
REM Creates a venv on first run, then launches the GUI. Use: run.bat [--source demo]
cd /d "%~dp0"
if not exist .venv ( py -3 -m venv .venv && .venv\Scripts\pip install -r requirements.txt )
.venv\Scripts\python -m mmd --gui %*
