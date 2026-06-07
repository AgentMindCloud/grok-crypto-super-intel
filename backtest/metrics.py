"""
backtest/metrics.py

Performance metrics computation. Works on the results of a backtest run.

All functions are pure and expect pandas Series/DataFrames.
"""

import pandas as pd
import numpy as np


def compute_metrics(equity: pd.Series, strategy_returns: pd.Series, signals: pd.Series, initial_cap: float = 10000.0) -> dict:
    """
    Compute a rich set of metrics.
    Returns dict with keys suitable for UI display and saving.
    """
    if len(equity) == 0:
        return {"error": "No data"}

    final_equity = float(equity.iloc[-1])
    total_return = (final_equity / initial_cap - 1) * 100

    # Annualized Sharpe (assuming daily bars, 252 trading days)
    if strategy_returns.std() > 0:
        sharpe = (strategy_returns.mean() / strategy_returns.std()) * np.sqrt(252)
    else:
        sharpe = 0.0

    # Max Drawdown
    roll_max = equity.cummax()
    drawdown = (equity - roll_max) / roll_max
    max_dd = float(drawdown.min() * 100)

    # Simple win rate (on periods with position)
    in_position = signals.shift(1).fillna(0) > 0
    pos_returns = strategy_returns[in_position]
    if len(pos_returns) > 0:
        wins = (pos_returns > 0).sum()
        win_rate = (wins / len(pos_returns)) * 100
    else:
        win_rate = 0.0

    # Rough profit factor
    gross_profit = pos_returns[pos_returns > 0].sum()
    gross_loss = abs(pos_returns[pos_returns < 0].sum())
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

    return {
        "final_equity": round(final_equity, 2),
        "total_return_pct": round(total_return, 2),
        "annualized_sharpe": round(sharpe, 2),
        "max_drawdown_pct": round(max_dd, 2),
        "win_rate_pct": round(win_rate, 1),
        "profit_factor": round(profit_factor, 2) if profit_factor != float("inf") else "inf",
        "num_periods": len(equity),
    }


def equity_curve_to_df(equity: pd.Series, buy_hold: pd.Series) -> pd.DataFrame:
    """Helper to prepare clean equity curve for plotting."""
    df = pd.DataFrame({"Strategy": equity, "Buy & Hold": buy_hold}).dropna()
    return df
