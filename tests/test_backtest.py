"""
tests/test_backtest.py - Skeleton tests for PR 3 backtest engine, strategies, and metrics.
"""

import pandas as pd
import numpy as np
import pytest

from backtest.strategies import sma_crossover, rsi_mean_reversion, STRATEGY_REGISTRY
from backtest.metrics import compute_metrics
from backtest.engine import run_backtest, optimize_strategy, run_multi_asset_backtest, walk_forward_backtest


def _make_synthetic_ohlcv(n: int = 120, start_price: float = 100.0) -> pd.DataFrame:
    """Generate a simple trending + noisy price series for testing."""
    idx = pd.date_range("2024-01-01", periods=n, freq="D")
    np.random.seed(42)
    rets = np.random.normal(0.001, 0.02, n)
    close = start_price * (1 + rets).cumprod()
    df = pd.DataFrame({
        "timestamp": idx,
        "open": close * (1 + np.random.uniform(-0.005, 0.005, n)),
        "high": close * (1 + np.random.uniform(0.0, 0.01, n)),
        "low": close * (1 + np.random.uniform(-0.01, 0.0, n)),
        "close": close,
        "volume": np.random.randint(1000, 10000, n),
    })
    df = df.set_index("timestamp")
    return df


def test_strategies_return_signal():
    df = _make_synthetic_ohlcv(80)
    for name, func in STRATEGY_REGISTRY.items():
        out = func(df)
        assert "signal" in out.columns
        assert out["signal"].isin([0, 1]).all()


def test_run_backtest_basic():
    df = _make_synthetic_ohlcv(100)
    res = run_backtest(df, strategy="SMA Crossover (20/50)", initial_cap=10000)
    assert "metrics" in res
    assert "equity_df" in res
    assert "full_df" in res
    assert res["metrics"]["final_equity"] > 0


def test_run_backtest_with_sizing_and_stop():
    df = _make_synthetic_ohlcv(80)
    res = run_backtest(
        df,
        strategy="RSI Mean Reversion (buy <30, sell >70)",
        initial_cap=5000,
        sizing="percent",
        sizing_param=0.5,
        stop_loss_pct=0.05,
    )
    assert "metrics" in res
    m = res["metrics"]
    assert "max_drawdown_pct" in m
    assert "win_rate_pct" in m


def test_optimize_strategy_returns_results():
    df = _make_synthetic_ohlcv(60)
    res = optimize_strategy(df, strategy="SMA Crossover (20/50)", initial_cap=10000)
    if "error" not in res:
        assert "best_params" in res or "params_used" in res
        assert "optimization_results" in res


def test_multi_asset_and_walk_forward():
    df = _make_synthetic_ohlcv(300)
    # Multi-asset (reuse same df for demo)
    ma = run_multi_asset_backtest({"BTC": df, "ETH": df}, initial_cap=10000)
    assert "metrics" in ma or "error" in ma

    # Walk forward
    wf = walk_forward_backtest(df, strategy="SMA Crossover (20/50)", initial_cap=10000)
    assert "oos_equity_df" in wf or "error" in wf


def test_metrics_computation():
    equity = pd.Series([10000, 10100, 9900, 10200])
    rets = pd.Series([0.01, -0.02, 0.03])
    sigs = pd.Series([1, 1, 0])
    m = compute_metrics(equity, rets, sigs, initial_cap=10000)
    assert "total_return_pct" in m
    assert "max_drawdown_pct" in m
    assert "annualized_sharpe" in m
