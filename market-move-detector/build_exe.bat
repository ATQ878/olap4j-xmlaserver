@echo off
REM Builds dist\MarketMoveDetector.exe (single file, no console)
cd /d "%~dp0"
if not exist .venv ( py -3 -m venv .venv && .venv\Scripts\pip install -r requirements.txt )
.venv\Scripts\pip install pyinstaller
.venv\Scripts\pyinstaller --onefile --noconsole --name MarketMoveDetector --collect-all yfinance launcher.py
