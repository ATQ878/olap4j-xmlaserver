"""Scan a watchlist, return ranked results, and log alerts to CSV."""
from __future__ import annotations
import csv, datetime as dt, os
from . import data, signals


def scan(symbols, source="yahoo", **kw):
    results, errors = [], {}
    for s in symbols:
        try:
            results.append(signals.analyze(s, data.get(s, source, **kw)))
        except Exception as e:  # keep scanning other symbols
            errors[s] = str(e)
    results.sort(key=lambda r: -r.score)
    return results, errors


def log_alerts(results, path="alerts_log.csv", threshold=65.0):
    new = [r for r in results if r.score >= threshold]
    if not new:
        return new
    exists = os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(["logged_at", "symbol", "score", "bias", "close", "reasons"])
        for r in new:
            w.writerow([dt.datetime.now().isoformat(timespec="seconds"), r.symbol, r.score,
                        r.bias, f"{r.last_close:.4f}", " | ".join(r.reasons())])
    return new


def beep():
    try:
        import winsound
        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
    except Exception:
        print("\a", end="")
