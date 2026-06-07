"""
backtest package - Advanced Strategy Backtester (PR 3)

Modular pure-pandas implementation extracted and upgraded from the original inline logic in app.py.

Key enhancements:
- Position sizing (fixed, percent of capital, simple volatility target)
- Stop loss logic (fixed % trailing or hard)
- Parameter optimization (simple grid search)
- Improved metrics (max drawdown, win rate, profit factor, better annualized Sharpe)
- Multi-asset support scaffolding (single asset primary for v1 of this module)
- Compatible output for Streamlit UI (equity curve, metrics, signal df)

Usage:
    from backtest.engine import run_backtest, optimize_strategy, save_run, load_runs
    results = run_backtest(df, strategy='sma', initial_cap=10000, sizing='percent', stop_loss=0.05)
    save_run(results, extra={"asset": "bitcoin"})
    runs = load_runs()
"""

from .engine import (
    run_backtest, optimize_strategy, save_run, load_runs,
    run_multi_asset_backtest, walk_forward_backtest, save_richer_backtest_history
)
from . import strategies
from . import metrics

__all__ = [
    "run_backtest", "optimize_strategy", "save_run", "load_runs",
    "run_multi_asset_backtest", "walk_forward_backtest", "save_richer_backtest_history",
    "strategies", "metrics"
]
