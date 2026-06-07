"""
backtest/engine.py

Core backtesting engine. Pure pandas, no heavy dependencies.

Refactors and significantly upgrades the original inline logic that lived in app.py (lines ~384-422 in v1).

Features added in PR 3:
- Configurable position sizing
- Basic stop loss (hard stop on close)
- Simple grid-based parameter optimization for the chosen strategy
- Better metrics via metrics.py
- Support for saving runs via `save_run()` (soft recommendation on PR 1 persistence patterns;
  the engine itself has no hard dependency and works standalone).

The engine is stateless and can be used from the Streamlit app or scripts.
"""

from __future__ import annotations
import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from . import strategies
from .metrics import compute_metrics, equity_curve_to_df


def _apply_sizing_and_stops(
    df: pd.DataFrame,
    initial_cap: float,
    sizing: str = "fixed",
    sizing_param: float = 1.0,
    stop_loss_pct: Optional[float] = None,
) -> pd.DataFrame:
    """
    Compute position size and apply simple stop logic.
    Returns df with added 'position', 'strategy_returns', 'equity'.
    """
    df = df.copy()
    price = df["close"]

    # Base signal from strategy (0 or 1 for long/flat)
    signal = df["signal"].shift(1).fillna(0)

    # Position sizing
    if sizing == "percent":
        # sizing_param is fraction of capital per trade (e.g. 0.5 = 50%)
        capital_at_risk = initial_cap * sizing_param
        position = signal * (capital_at_risk / price)
    elif sizing == "vol_target":
        # Very crude vol target: inverse of rolling std
        returns = price.pct_change()
        vol = returns.rolling(20).std().fillna(0.01)
        target_vol = 0.02  # 2% daily target vol example
        vol_scalar = (target_vol / vol).clip(0, 5)
        position = signal * (initial_cap * vol_scalar / price)
    else:  # "fixed" - fixed dollar amount per unit (sizing_param = dollars per unit, default 1 unit)
        position = signal * sizing_param

    df["position"] = position

    # Returns
    df["returns"] = price.pct_change().fillna(0)
    df["strategy_returns"] = df["position"] * df["returns"]

    # Simple stop loss (applied to strategy returns on a per-bar basis)
    if stop_loss_pct is not None and stop_loss_pct > 0:
        # If daily return worse than -stop_loss_pct while in position, zero the return that bar
        stop_mask = (df["strategy_returns"] < -stop_loss_pct) & (signal > 0)
        df.loc[stop_mask, "strategy_returns"] = -stop_loss_pct
        # Force flat after stop (for simplicity in this version)
        df.loc[stop_mask, "signal"] = 0

    # Equity curves
    df["equity"] = (1 + df["strategy_returns"]).cumprod() * initial_cap
    df["buy_hold"] = (1 + df["returns"]).cumprod() * initial_cap

    return df


def run_backtest(
    ohlcv_df: pd.DataFrame,
    strategy: str = "SMA Crossover (20/50)",
    params: Optional[Dict[str, Any]] = None,
    initial_cap: float = 10000.0,
    sizing: str = "fixed",
    sizing_param: float = 1.0,
    stop_loss_pct: Optional[float] = None,
    price_col: str = "close",
) -> Dict[str, Any]:
    """
    Main entry point for a single backtest run.

    Returns a dict with:
      - 'equity_df': DataFrame for plotting
      - 'metrics': dict of performance numbers
      - 'full_df': the augmented OHLCV with signals/returns/equity
      - 'params_used': the params that were actually run
    """
    if ohlcv_df.empty or price_col not in ohlcv_df.columns:
        return {"error": "Empty or invalid OHLCV data", "full_df": ohlcv_df}

    df = ohlcv_df.copy()
    if "close" not in df.columns and price_col != "close":
        df = df.rename(columns={price_col: "close"})

    # 1. Generate signals
    strat_func, default_params = strategies.get_strategy(strategy)
    if strat_func is None:
        return {"error": f"Unknown strategy: {strategy}"}

    run_params = {**default_params, **(params or {})}
    df = strat_func(df, **run_params)

    # 2. Apply sizing + stops + equity simulation
    df = _apply_sizing_and_stops(
        df,
        initial_cap=initial_cap,
        sizing=sizing,
        sizing_param=sizing_param,
        stop_loss_pct=stop_loss_pct,
    )

    # 3. Metrics
    metrics = compute_metrics(
        equity=df["equity"],
        strategy_returns=df["strategy_returns"],
        signals=df["signal"],
        initial_cap=initial_cap,
    )

    equity_df = equity_curve_to_df(df["equity"], df["buy_hold"])

    return {
        "equity_df": equity_df,
        "metrics": metrics,
        "full_df": df,
        "params_used": run_params,
        "sizing": sizing,
        "stop_loss_pct": stop_loss_pct,
    }


def optimize_strategy(
    ohlcv_df: pd.DataFrame,
    strategy: str = "SMA Crossover (20/50)",
    initial_cap: float = 10000.0,
    param_grid: Optional[Dict[str, list]] = None,
    sizing: str = "fixed",
    sizing_param: float = 1.0,
    stop_loss_pct: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Very simple grid search over strategy params.
    Returns the best result + all tried results (for transparency in UI).
    """
    _, default_params = strategies.get_strategy(strategy)
    if param_grid is None:
        # Sensible small grids per strategy
        if "SMA" in strategy:
            param_grid = {"fast": [10, 15, 20, 25], "slow": [40, 50, 60]}
        else:
            param_grid = {"period": [10, 14, 20], "oversold": [25, 30, 35]}

    best_sharpe = -np.inf
    best_result = None
    all_results = []

    # Cartesian product of grid
    keys = list(param_grid.keys())
    from itertools import product
    for values in product(*param_grid.values()):
        p = dict(zip(keys, values))
        res = run_backtest(
            ohlcv_df,
            strategy=strategy,
            params=p,
            initial_cap=initial_cap,
            sizing=sizing,
            sizing_param=sizing_param,
            stop_loss_pct=stop_loss_pct,
        )
        if "error" in res:
            continue

        sharpe = res["metrics"].get("annualized_sharpe", 0)
        all_results.append({"params": p, "sharpe": sharpe, "total_return": res["metrics"]["total_return_pct"]})

        if sharpe > best_sharpe:
            best_sharpe = sharpe
            best_result = res

    if best_result is None:
        return {"error": "Optimization produced no valid runs"}

    best_result["optimization_results"] = all_results
    best_result["best_params"] = best_result["params_used"]
    return best_result


# ------------------------------------------------------------------
# Soft PR 1 persistence integration for saving backtest runs
# ------------------------------------------------------------------

def _atomic_write_json(path: Path, data: list) -> None:
    """Atomic write helper (follows the pattern from PR1 persistence.py)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    tmp.replace(path)


def save_run(
    result: Dict[str, Any],
    extra: Optional[Dict[str, Any]] = None,
    runs_file: Optional[Path | str] = None,
) -> Path:
    """Save a backtest run result (dict returned by run_backtest or optimize_strategy).

    This helper performs the "soft PR 1 dance":

    - Tries to import PR1's `config` module to use its recommended `DATA_DIR`
      for storage location (and follows its atomic-write + data-dir conventions).
    - Falls back gracefully to a local `backtest_runs.json` if PR1 config
      is not available (the engine has **no hard dependency** on PR1).
    - Always stores runs in a dedicated file (never mixes with portfolio holdings).
    - Uses atomic write for safety.

    The backtest engine remains fully stateless and usable without PR1.

    Args:
        result: The dict returned from run_backtest(...) or optimize_strategy(...).
        extra: Optional additional metadata to attach to the record (e.g. asset, notes).
        runs_file: Override the target file path.

    Returns:
        Path to the file the run was appended to.
    """
    # Soft recommendation on PR 1
    try:
        import config as pr1_config
        base_dir = getattr(pr1_config, "DATA_DIR", Path("."))
    except Exception:
        base_dir = Path(".")

    if runs_file is None:
        runs_file = base_dir / "backtest_runs.json"
    runs_path = Path(runs_file).expanduser().resolve()

    # Build the record
    record: Dict[str, Any] = {
        "timestamp": datetime.datetime.now().isoformat(),
        "params": result.get("params_used") or result.get("best_params", {}),
        "metrics": result.get("metrics", {}),
        "sizing": result.get("sizing"),
        "stop_loss_pct": result.get("stop_loss_pct"),
    }
    if extra:
        record.update(extra)

    # Load existing runs (list)
    existing: list = []
    if runs_path.exists():
        try:
            existing = json.loads(runs_path.read_text(encoding="utf-8"))
        except Exception:
            existing = []
    if not isinstance(existing, list):
        existing = []

    existing.append(record)

    _atomic_write_json(runs_path, existing)
    return runs_path


def load_runs(runs_file: Optional[Path | str] = None) -> list:
    """Load previously saved backtest runs (symmetric to save_run)."""
    try:
        import config as pr1_config
        base_dir = getattr(pr1_config, "DATA_DIR", Path("."))
    except Exception:
        base_dir = Path(".")

    if runs_file is None:
        runs_file = base_dir / "backtest_runs.json"
    runs_path = Path(runs_file).expanduser().resolve()

    if not runs_path.exists():
        return []

    try:
        data = json.loads(runs_path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


# ------------------------------------------------------------------
# v3 Phase B: Backtest extensions (multi-asset, walk-forward, richer history)
# These build on the core run_backtest / optimize_strategy.
# Optional pandas-ta for indicators (see note at bottom).
# Integrates with persistence for history storage (soft).
# ------------------------------------------------------------------

def run_multi_asset_backtest(
    assets_data: Dict[str, pd.DataFrame],  # e.g. {"BTC": ohlcv_df, "ETH": ohlcv_df}
    weights: Optional[Dict[str, float]] = None,  # target weights, e.g. {"BTC": 0.6, "ETH": 0.4}
    rebalance_freq: int = 20,  # rebalance every N bars
    initial_cap: float = 10000.0,
    **common_kwargs
) -> Dict[str, Any]:
    """
    Basic multi-asset rebalance backtest (equal or custom weights, periodic rebalance).
    Each asset runs its own signal/returns, then combined with weights.
    For simplicity, assumes same strategy/params for all (pass via common_kwargs).
    Returns combined equity curve + per-asset metrics + allocation history.
    """
    if not assets_data:
        return {"error": "No assets provided"}

    if weights is None:
        n = len(assets_data)
        weights = {k: 1.0 / n for k in assets_data}

    combined_equity = pd.Series(0.0, index=next(iter(assets_data.values())).index)
    per_asset_results = {}
    allocation_history = []

    cap_per_asset = {k: initial_cap * w for k, w in weights.items()}

    for asset, df in assets_data.items():
        res = run_backtest(df, initial_cap=cap_per_asset.get(asset, initial_cap), **common_kwargs)
        if "error" in res:
            continue
        per_asset_results[asset] = res
        # Simple rebalance simulation: scale returns by weight (crude, no full rebalance logic for v1 of this)
        # For better: would need to track positions across assets and rebalance on freq.
        asset_equity = res["full_df"]["equity"] * (weights.get(asset, 0) )
        combined_equity = combined_equity.add(asset_equity, fill_value=0)

    # Normalize combined
    if len(combined_equity) > 0:
        combined_equity = combined_equity / combined_equity.iloc[0] * initial_cap if combined_equity.iloc[0] != 0 else combined_equity

    # Aggregate metrics (simple sum/avg for demo)
    total_metrics = {
        "final_equity": float(combined_equity.iloc[-1]) if len(combined_equity) > 0 else initial_cap,
        "assets": list(per_asset_results.keys()),
        "weights": weights,
    }

    return {
        "equity_df": pd.DataFrame({"Combined": combined_equity}),
        "per_asset": per_asset_results,
        "metrics": total_metrics,
        "allocation_history": allocation_history,  # placeholder for future
    }


def walk_forward_backtest(
    ohlcv_df: pd.DataFrame,
    strategy: str = "SMA Crossover (20/50)",
    train_window: int = 252,   # ~1 year daily
    test_window: int = 63,     # ~3 months
    step: int = 21,            # monthly step
    **run_kwargs
) -> Dict[str, Any]:
    """
    Simple walk-forward optimization / out-of-sample testing.
    For each window: optimize on train, run on test, collect OOS equity.
    Returns combined OOS equity + list of window results.
    """
    n = len(ohlcv_df)
    if n < train_window + test_window:
        return {"error": "Not enough data for walk-forward windows"}

    oos_equity_parts = []
    window_results = []
    current = train_window

    while current + test_window <= n:
        train_df = ohlcv_df.iloc[current - train_window : current]
        test_df = ohlcv_df.iloc[current : current + test_window]

        # Optimize on train (reuse existing)
        opt_res = optimize_strategy(train_df, strategy=strategy, **run_kwargs)
        best_params = opt_res.get("best_params", {}) if "best_params" in opt_res else run_kwargs.get("params", {})

        # Run on test with best params
        test_res = run_backtest(test_df, strategy=strategy, params=best_params, **run_kwargs)

        if "error" not in test_res:
            oos_equity_parts.append(test_res["full_df"]["equity"])
            window_results.append({
                "train_start": train_df.index[0],
                "train_end": train_df.index[-1],
                "test_start": test_df.index[0],
                "test_end": test_df.index[-1],
                "best_params": best_params,
                "test_metrics": test_res.get("metrics"),
            })

        current += step

    if not oos_equity_parts:
        return {"error": "No valid walk-forward windows"}

    combined_oos = pd.concat(oos_equity_parts).sort_index()
    # Rebase combined to start at initial_cap for display
    if len(combined_oos) > 0:
        combined_oos = combined_oos / combined_oos.iloc[0] * run_kwargs.get("initial_cap", 10000)

    return {
        "oos_equity_df": pd.DataFrame({"WalkForward_OOS": combined_oos}),
        "windows": window_results,
        "overall_metrics": compute_metrics(
            equity=combined_oos,
            strategy_returns=combined_oos.pct_change().fillna(0),
            signals=pd.Series(0, index=combined_oos.index),  # placeholder
            initial_cap=run_kwargs.get("initial_cap", 10000)
        ),
    }


def save_richer_backtest_history(result: Dict[str, Any], extra: Optional[Dict] = None) -> Optional[Path]:
    """Phase B: Use the enhanced persistence backtest history storage (if available)."""
    try:
        from persistence import save_backtest_run
        record = {
            "timestamp": datetime.now().isoformat(),
            "params": result.get("params_used", result.get("best_params", {})),
            "metrics": result.get("metrics", {}),
            "sizing": result.get("sizing"),
            "stop_loss_pct": result.get("stop_loss_pct"),
            "equity_curve_summary": {  # lightweight, not full series
                "start": str(result.get("equity_df", pd.DataFrame()).index[0]) if "equity_df" in result else None,
                "end": str(result.get("equity_df", pd.DataFrame()).index[-1]) if "equity_df" in result else None,
                "final_equity": result.get("metrics", {}).get("final_equity"),
            },
        }
        if extra:
            record.update(extra)
        return save_backtest_run(record)
    except Exception:
        # Fallback to engine's own save_run
        try:
            from .engine import save_run as engine_save_run
            return engine_save_run(result, extra=extra)
        except Exception:
            return None

