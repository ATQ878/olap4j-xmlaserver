"""Pure-pandas indicator helpers. Input frames need columns open/high/low/close/volume."""
import numpy as np
import pandas as pd


def true_range(df: pd.DataFrame) -> pd.Series:
    prev = df["close"].shift(1)
    return pd.concat([df["high"] - df["low"],
                      (df["high"] - prev).abs(),
                      (df["low"] - prev).abs()], axis=1).max(axis=1)


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    return true_range(df).rolling(n).mean()


def bollinger_bandwidth(close: pd.Series, n: int = 20, k: float = 2.0) -> pd.Series:
    mid = close.rolling(n).mean()
    sd = close.rolling(n).std()
    return (2 * k * sd) / mid


def rolling_percentile(s: pd.Series, window: int) -> pd.Series:
    """Percentile rank (0..1) of the latest value within the trailing window."""
    return s.rolling(window).apply(lambda x: (x[:-1] < x[-1]).mean() if len(x) > 1 else np.nan, raw=True)


def zscore(s: pd.Series, n: int = 20) -> pd.Series:
    m = s.rolling(n).mean().shift(1)
    sd = s.rolling(n).std().shift(1)
    return (s - m) / sd.replace(0, np.nan)


def rsi(close: pd.Series, n: int = 14) -> pd.Series:
    d = close.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))
