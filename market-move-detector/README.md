# Market Move Detector (Windows)

Desktop app + CLI that scans a watchlist and flags early signs of a large price move.

## Signals (each 0-1 strength, blended into a 0-100 score)
| Signal | Weight | Meaning |
|---|---|---|
| squeeze | 25% | Bollinger bandwidth near its 120-bar low (volatility compression precedes expansion) |
| volume | 25% | Volume z-score vs 20 bars, directional by the day's return |
| momentum | 20% | 5-day rate of change accelerating past the 20-day pace |
| range | 15% | True range vs prior ATR(20) |
| breakout | 15% | Distance (in ATRs) to / through the 20-day high or low |

Levels: `HIGH` >= 65, `WATCH` >= 45. Bias (UP/DOWN/NEUTRAL) is the strength-weighted direction. Alerts at/above the threshold are appended to `alerts_log.csv` and trigger a Windows beep.

## Run on Windows
1. Install Python 3.10+ from python.org (includes Tkinter).
2. Double-click `run.bat` (creates a venv, installs deps, opens the GUI). Add `--source demo` for offline synthetic data.
3. Double-click a row to chart it. Set "Auto (min)" to rescan on a timer.
4. `build_exe.bat` produces a single `dist\MarketMoveDetector.exe`.

CLI: `python -m mmd --symbols SPY QQQ NVDA --watch 300`

Data: Yahoo Finance via `yfinance` (daily bars, delayed, free). Swap providers in `mmd/data.py`.
Tests: `pytest tests`.

**Not financial advice.** These are heuristics, not predictions; backtest before relying on them.
