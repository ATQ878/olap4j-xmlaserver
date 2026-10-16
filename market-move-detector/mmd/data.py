"""Data providers: Yahoo Finance (yfinance), CSV files, and a synthetic demo generator."""
from __future__ import annotations
import numpy as np
import pandas as pd

COLS = ["open", "high", "low", "close", "volume"]


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.rename(columns=str.lower)
    if "adj close" in df.columns and "close" not in df.columns:
        df["close"] = df["adj close"]
    return df[COLS].dropna(subset=["close"])


def fetch_yahoo(symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    import yfinance as yf  # imported lazily so the engine works without it
    df = yf.download(symbol, period=period, interval=interval, auto_adjust=True, progress=False)
    if df is None or df.empty:
        raise ValueError(f"No data returned for {symbol}")
    return _normalize(df)


def load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    return _normalize(df)


def synthetic(symbol: str = "DEMO", bars: int = 300, seed: int | None = None, setup: bool = True) -> pd.DataFrame:
    """Random walk; with setup=True the tail has a squeeze then a volume-backed breakout."""
    rng = np.random.default_rng(seed if seed is not None else abs(hash(symbol)) % 2**32)
    vol = np.full(bars, 0.012)
    if setup:
        vol[-40:-3] = 0.003   # compression
        vol[-3:] = 0.02       # expansion
    ret = rng.normal(0.0003, vol)
    if setup:
        ret[-3:] += 0.012
    close = 100 * np.exp(np.cumsum(ret))
    spread = np.abs(rng.normal(0, vol)) * close
    openp = np.r_[close[0], close[:-1]]
    v = rng.lognormal(13, 0.25, bars)
    if setup:
        v[-3:] *= 3.5
    idx = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=bars)
    return pd.DataFrame({"open": openp, "high": np.maximum(openp, close) + spread,
                         "low": np.minimum(openp, close) - spread, "close": close, "volume": v}, index=idx)


def get(symbol: str, source: str = "yahoo", **kw) -> pd.DataFrame:
    if source == "demo":
        return synthetic(symbol, setup=symbol.upper().endswith(("1", "3", "5", "7", "9")) or symbol.upper() == "DEMO")
    if source == "csv":
        return load_csv(symbol)
    return fetch_yahoo(symbol, **kw)
