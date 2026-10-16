"""Walk-forward backtest: does a high score precede a larger-than-normal move?

At each bar t we score using only data up to t, then look at the next `horizon` bars.
A "big move" is |forward return| > 1.5x the typical horizon move (trailing 60-bar daily
stdev * sqrt(horizon)). Direction hit rate is measured only when bias is UP/DOWN.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from . import signals

BUCKETS = [(0, 30), (30, 45), (45, 65), (65, 101)]


def walk(symbol: str, df: pd.DataFrame, horizon: int = 5, warmup: int = 130, window: int = 200) -> pd.DataFrame:
    rows = []
    close = df["close"]
    daily = close.pct_change().rolling(60).std()
    for t in range(warmup, len(df) - horizon):
        r = signals.analyze(symbol, df.iloc[max(0, t - window + 1): t + 1])
        fwd = close.iloc[t + horizon] / close.iloc[t] - 1
        norm = daily.iloc[t] * np.sqrt(horizon)
        rows.append((symbol, df.index[t], r.score, r.bias, fwd, abs(fwd) / norm if norm else np.nan))
    return pd.DataFrame(rows, columns=["symbol", "date", "score", "bias", "fwd", "move_x"])


def summarize(trades: pd.DataFrame) -> pd.DataFrame:
    out = []
    for lo, hi in BUCKETS:
        s = trades[(trades.score >= lo) & (trades.score < hi)]
        d = s[s.bias != "NEUTRAL"]
        hit = ((np.sign(d.fwd) == np.where(d.bias == "UP", 1, -1)).mean()) if len(d) else np.nan
        out.append({"score": f"{lo}-{min(hi, 100)}", "n": len(s),
                    "avg_move_x": s.move_x.mean(), "pct_big_move": (s.move_x > 1.5).mean() if len(s) else np.nan,
                    "dir_hit_rate": hit})
    return pd.DataFrame(out)


def run(symbols, source="yahoo", horizon=5, **kw) -> pd.DataFrame:
    from . import data
    frames = []
    for s in symbols:
        try:
            frames.append(walk(s, data.get(s, source, **kw), horizon))
        except Exception as e:
            print(f"{s}: skipped ({e})")
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
