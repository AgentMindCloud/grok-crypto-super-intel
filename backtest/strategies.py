"""
backtest/strategies.py

Signal generation strategies. Pure pandas, vectorized where possible.

Each strategy function takes a DataFrame with at least 'close' column (and optionally 'high','low','volume')
and returns the same DF with added columns: signal (0/1), and any internal indicators used.
"""

import pandas as pd
import numpy as np


def sma_crossover(df: pd.DataFrame, fast: int = 20, slow: int = 50) -> pd.DataFrame:
    """Simple SMA crossover long-only strategy."""
    df = df.copy()
    df["sma_fast"] = df["close"].rolling(window=fast).mean()
    df["sma_slow"] = df["close"].rolling(window=slow).mean()
    df["signal"] = (df["sma_fast"] > df["sma_slow"]).astype(int)
    return df


def rsi_mean_reversion(df: pd.DataFrame, period: int = 14, oversold: int = 30, overbought: int = 70) -> pd.DataFrame:
    """RSI mean reversion: long when oversold, flat otherwise (crude long-only version)."""
    df = df.copy()
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    df["rsi"] = 100 - (100 / (1 + rs))
    # Long only when RSI < oversold (exit when crosses overbought or just stay in for simplicity)
    df["signal"] = (df["rsi"] < oversold).astype(int)
    return df


# Registry for easy lookup in engine / UI
STRATEGY_REGISTRY = {
    "SMA Crossover (20/50)": sma_crossover,
    "RSI Mean Reversion (buy <30, sell >70)": rsi_mean_reversion,
}

DEFAULT_PARAMS = {
    "SMA Crossover (20/50)": {"fast": 20, "slow": 50},
    "RSI Mean Reversion (buy <30, sell >70)": {"period": 14, "oversold": 30, "overbought": 70},
}


def get_strategy(name: str):
    """Helper to retrieve strategy function and default params."""
    func = STRATEGY_REGISTRY.get(name)
    params = DEFAULT_PARAMS.get(name, {}).copy()
    return func, params
