"""Early-warning signal engine.

Each detector returns a Signal with strength in [0,1] and direction in {-1,0,+1}.
The composite score (0-100) is a weighted blend; bias is the weighted direction.
"""
from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np
import pandas as pd
from . import indicators as ind

WEIGHTS = {"squeeze": 0.25, "volume": 0.25, "momentum": 0.20, "range": 0.15, "breakout": 0.15}


@dataclass
class Signal:
    name: str
    strength: float
    direction: int
    detail: str


@dataclass
class Result:
    symbol: str
    score: float
    bias: str
    signals: list = field(default_factory=list)
    last_close: float = float("nan")
    asof: object = None

    @property
    def level(self) -> str:
        return "HIGH" if self.score >= 65 else "WATCH" if self.score >= 45 else "QUIET"

    def reasons(self) -> list:
        return [f"{s.name}: {s.detail}" for s in sorted(self.signals, key=lambda s: -s.strength) if s.strength >= 0.4]


def _clip01(x: float) -> float:
    return float(min(1.0, max(0.0, x))) if np.isfinite(x) else 0.0


def _sign(x: float, dead: float = 0.0) -> int:
    return 0 if not np.isfinite(x) or abs(x) <= dead else (1 if x > 0 else -1)


def squeeze(df: pd.DataFrame, lookback: int = 120) -> Signal:
    """Volatility compression: bandwidth near the bottom of its range precedes expansion."""
    bw = ind.bollinger_bandwidth(df["close"])
    pct = ind.rolling_percentile(bw.dropna(), lookback).iloc[-1] if bw.notna().sum() > 30 else np.nan
    strength = _clip01((0.25 - pct) / 0.25) if np.isfinite(pct) else 0.0
    return Signal("squeeze", strength, 0, f"bandwidth at {pct:.0%} percentile" if np.isfinite(pct) else "n/a")


def volume(df: pd.DataFrame) -> Signal:
    """Abnormal volume with a price direction (accumulation / distribution)."""
    z = ind.zscore(df["volume"].astype(float)).iloc[-1]
    ret = df["close"].pct_change().iloc[-1]
    return Signal("volume", _clip01((z - 1.0) / 3.0), _sign(ret), f"volume z={z:.1f}, day {ret:+.2%}")


def momentum(df: pd.DataFrame) -> Signal:
    """Acceleration: short-term rate of change outpacing the medium-term pace."""
    c = df["close"]
    fast = c.pct_change(5).iloc[-1]
    slow = c.pct_change(20).iloc[-1] / 4  # per-5-day equivalent
    accel = fast - slow
    vol = c.pct_change().rolling(60).std().iloc[-1] * np.sqrt(5)
    k = accel / vol if vol and np.isfinite(vol) else np.nan
    return Signal("momentum", _clip01(abs(k) / 2.5), _sign(accel), f"5d {fast:+.2%} vs pace {slow:+.2%}")


def range_expansion(df: pd.DataFrame) -> Signal:
    tr = ind.true_range(df)
    ratio = tr.iloc[-1] / ind.atr(df, 20).shift(1).iloc[-1]
    ret = df["close"].pct_change().iloc[-1]
    return Signal("range", _clip01((ratio - 1.0) / 1.5), _sign(ret), f"true range {ratio:.1f}x ATR")


def breakout(df: pd.DataFrame, n: int = 20) -> Signal:
    """Proximity to / violation of the prior n-day high or low."""
    hi = df["high"].rolling(n).max().shift(1).iloc[-1]
    lo = df["low"].rolling(n).min().shift(1).iloc[-1]
    c = df["close"].iloc[-1]
    atr = ind.atr(df, 14).iloc[-1]
    if not all(np.isfinite([hi, lo, atr])) or atr == 0:
        return Signal("breakout", 0.0, 0, "n/a")
    d_hi, d_lo = (hi - c) / atr, (c - lo) / atr  # distance in ATRs (<=0 means broken)
    if d_hi <= d_lo:
        return Signal("breakout", _clip01(1 - d_hi / 1.5), 1, f"{d_hi:+.1f} ATR from {n}d high")
    return Signal("breakout", _clip01(1 - d_lo / 1.5), -1, f"{d_lo:+.1f} ATR from {n}d low")


DETECTORS = {"squeeze": squeeze, "volume": volume, "momentum": momentum,
             "range": range_expansion, "breakout": breakout}


def analyze(symbol: str, df: pd.DataFrame, weights: dict | None = None) -> Result:
    w = weights or WEIGHTS
    df = df.dropna(subset=["close"]).copy()
    if len(df) < 60:
        raise ValueError(f"{symbol}: need >= 60 bars, got {len(df)}")
    sigs = [fn(df) for fn in DETECTORS.values()]
    total = sum(w[s.name] for s in sigs)
    score = 100 * sum(w[s.name] * s.strength for s in sigs) / total
    dsum = sum(w[s.name] * s.strength * s.direction for s in sigs)
    # Squeeze is directionless but amplifies the pending move's conviction.
    bias = "UP" if dsum > 0.03 else "DOWN" if dsum < -0.03 else "NEUTRAL"
    return Result(symbol, round(score, 1), bias, sigs, float(df["close"].iloc[-1]), df.index[-1])
