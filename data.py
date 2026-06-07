"""
Super Crypto Intel - Data Layer (PR2 hardened)
Pure data fetching + light processing. Designed for Streamlit caching + easy extension.
All public / free where possible. Tiered/premium sources with graceful fallback.
Configurable retries + rate limits.
"""

from __future__ import annotations
import os
import time
from typing import Any, Callable, Dict, List, Optional

import requests
import pandas as pd

# Local imports for PR2 config (no circularity)
import config as app_config

# ---------- Config (now driven from central config where possible) ----------
COINGECKO_BASE = "https://api.coingecko.com/api/v3"
ALT_FNG_BASE = "https://api.alternative.me/fng/"
DEFILLAMA_BASE = "https://api.llama.fi"

# Rate limit now configurable via env (PR2)
_last_cg_call = 0.0
_CG_MIN_INTERVAL = getattr(app_config, "CG_RATE_LIMIT_INTERVAL", 1.2)


def _rate_limit_coingecko():
    global _last_cg_call
    now = time.time()
    wait = _CG_MIN_INTERVAL - (now - _last_cg_call)
    if wait > 0:
        time.sleep(wait)
    _last_cg_call = time.time()


def with_retry(max_attempts: Optional[int] = None, base_delay: Optional[float] = None):
    """Decorator for exponential backoff retry on transient errors (PR2)."""
    max_attempts = max_attempts or getattr(app_config, "RETRY_MAX_ATTEMPTS", 3)
    base_delay = base_delay or getattr(app_config, "RETRY_BASE_DELAY", 1.0)

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            delay = base_delay
            last_exc = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except (requests.exceptions.RequestException, ConnectionError, TimeoutError) as e:
                    last_exc = e
                    if attempt == max_attempts - 1:
                        break
                    time.sleep(delay)
                    delay *= 2  # exponential
            # final fallback: re-raise or return safe empty
            raise last_exc if last_exc else RuntimeError("Retry failed with no exception")
        return wrapper
    return decorator


@with_retry()
def _get_json(url: str, params: Optional[Dict[str, Any]] = None, timeout: int = 15) -> Any:
    # PR2: rate limit still applies before the call
    _rate_limit_coingecko()
    resp = requests.get(url, params=params or {}, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


# ---------- Core Market Data (CoinGecko - no key required) ----------

def get_global_data() -> Dict[str, Any]:
    """Global crypto market stats: total cap, volume, BTC/ETH dominance, etc."""
    _rate_limit_coingecko()
    data = _get_json(f"{COINGECKO_BASE}/global")
    g = data.get("data", {})
    return {
        "total_market_cap_usd": g.get("total_market_cap", {}).get("usd"),
        "total_volume_24h_usd": g.get("total_volume", {}).get("usd"),
        "market_cap_change_24h": g.get("market_cap_change_percentage_24h_usd"),
        "btc_dominance": g.get("market_cap_percentage", {}).get("btc"),
        "eth_dominance": g.get("market_cap_percentage", {}).get("eth"),
        "active_cryptocurrencies": g.get("active_cryptocurrencies"),
        "markets": g.get("markets"),
    }


def get_coins_markets(
    vs_currency: str = "usd",
    per_page: int = 50,
    page: int = 1,
    price_change_percentage: str = "24h,7d",
    ids: Optional[str] = None,  # comma separated e.g. "bitcoin,ethereum"
) -> List[Dict[str, Any]]:
    """Top coins with price, market cap, volume, % changes. Perfect for tables + rankings."""
    _rate_limit_coingecko()
    params = {
        "vs_currency": vs_currency,
        "order": "market_cap_desc",
        "per_page": per_page,
        "page": page,
        "price_change_percentage": price_change_percentage,
        "sparkline": "false",
    }
    if ids:
        params["ids"] = ids
    return _get_json(f"{COINGECKO_BASE}/coins/markets", params=params)


def get_coin_ohlc(coin_id: str, vs_currency: str = "usd", days: int = 30) -> pd.DataFrame:
    """OHLC data as DataFrame. Good for charts and simple backtesting."""
    _rate_limit_coingecko()
    url = f"{COINGECKO_BASE}/coins/{coin_id}/ohlc"
    params = {"vs_currency": vs_currency, "days": days}
    raw = _get_json(url, params=params)
    # CoinGecko returns [[timestamp, open, high, low, close], ...]
    if not raw:
        return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close"])
    df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df = df.set_index("timestamp")
    return df


def get_coin_market_chart(coin_id: str, vs_currency: str = "usd", days: int = 30) -> pd.DataFrame:
    """Price + market cap + volume time series. Useful for advanced plots."""
    _rate_limit_coingecko()
    url = f"{COINGECKO_BASE}/coins/{coin_id}/market_chart"
    params = {"vs_currency": vs_currency, "days": days, "interval": "daily"}
    data = _get_json(url, params=params)
    prices = data.get("prices", [])
    if not prices:
        return pd.DataFrame()
    df = pd.DataFrame(prices, columns=["timestamp", "price"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df = df.set_index("timestamp")
    return df


# ---------- Sentiment ----------
def get_fear_and_greed(limit: int = 1) -> Dict[str, Any]:
    """alternative.me Fear & Greed Index. Returns latest + classification."""
    try:
        data = _get_json(f"{ALT_FNG_BASE}", params={"limit": limit})
        if data and data.get("data"):
            item = data["data"][0]
            return {
                "value": int(item.get("value", 50)),
                "classification": item.get("value_classification", "Neutral"),
                "timestamp": item.get("timestamp"),
                "time_until_update": item.get("time_until_update"),
            }
    except Exception:
        pass
    return {"value": 50, "classification": "Neutral (fallback)", "timestamp": None, "time_until_update": None}


# ---------- On-Chain / DeFi (DeFiLlama - excellent free tier) ----------
def get_defillama_chains() -> List[Dict[str, Any]]:
    """TVL by chain. Great overview of on-chain activity."""
    try:
        return _get_json(f"{DEFILLAMA_BASE}/v2/chains")
    except Exception:
        return []


def get_defillama_protocols(limit: int = 20) -> List[Dict[str, Any]]:
    """Top protocols by TVL + 1d/7d changes."""
    try:
        prots = _get_json(f"{DEFILLAMA_BASE}/protocols")
        # Sort by TVL desc and take top N
        prots = sorted(prots, key=lambda x: x.get("tvl", 0) or 0, reverse=True)[:limit]
        return prots
    except Exception:
        return []


def get_defillama_protocol_tvl(slug: str) -> Dict[str, Any]:
    """Detailed TVL history + breakdown for one protocol."""
    try:
        return _get_json(f"{DEFILLAMA_BASE}/protocol/{slug}")
    except Exception:
        return {}


# ---------- Exchange / CCXT helpers (public, no key for spot candles) ----------
def get_ccxt_ohlcv(
    exchange_id: str = "binance",
    symbol: str = "BTC/USDT",
    timeframe: str = "1h",
    limit: int = 100,
) -> pd.DataFrame:
    """Fetch OHLCV via ccxt (public). Great for backtesting real exchange data."""
    try:
        import ccxt  # local import so the module is optional until needed
        ex_class = getattr(ccxt, exchange_id)
        exchange = ex_class({"enableRateLimit": True})
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df = df.set_index("timestamp")
        return df
    except Exception as e:
        # Return empty frame on failure (ccxt not installed or rate limited or pair not supported)
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])


# ---------- Tiered / Premium Sources (PR2 - always graceful fallback to free) ----------

def get_glassnode_metric(metric_path: str, asset: str = "BTC", **params) -> Optional[Dict[str, Any]]:
    """Scaffolding for Glassnode on-chain metrics.

    Returns data dict or None (no key or error). Graceful degradation is mandatory.
    Example metric_path: 'market/price_usd_close' or 'transactions/count'
    """
    api_key = getattr(app_config, "GLASSNODE_API_KEY", None)
    if not api_key:
        return None
    url = f"https://api.glassnode.com/v1/metrics/{metric_path}"
    qparams = {**params, "a": asset, "api_key": api_key}
    try:
        return _get_json(url, params=qparams)
    except Exception:
        return None


def get_premium_metric(source: str, **kwargs) -> Any:
    """Generic entrypoint for future premium sources (Arkham, LunarCrush, etc.).

    Always returns None or safe default when key is missing.
    """
    key = getattr(app_config, f"{source.upper()}_API_KEY", None)
    if not key:
        return kwargs.get("default", None)
    # Real implementation would construct authenticated request here.
    # For now: scaffolding only.
    return kwargs.get("default", None)


# ---------- Portfolio helpers (pure) ----------
def compute_portfolio_metrics(
    holdings: List[Dict[str, Any]],  # [{"symbol": "BTC", "amount": 0.5, "coin_id": "bitcoin"}, ...]
    prices: Dict[str, float],        # {"bitcoin": 62000, ...} keyed by coin_id or symbol upper
) -> Dict[str, Any]:
    """Calculate value, weights, simple P&L proxy (assumes cost_basis optional)."""
    total = 0.0
    rows = []
    for h in holdings:
        cid = h.get("coin_id") or h.get("symbol", "").lower()
        amt = float(h.get("amount", 0))
        price = prices.get(cid) or prices.get(h.get("symbol", "").upper(), 0.0)
        value = amt * price
        total += value
        rows.append({
            "symbol": h.get("symbol"),
            "amount": amt,
            "price": price,
            "value_usd": value,
        })

    for r in rows:
        r["weight_pct"] = (r["value_usd"] / total * 100) if total > 0 else 0

    return {
        "total_value_usd": round(total, 2),
        "holdings": rows,
        "concentration_top1": max((r["weight_pct"] for r in rows), default=0),
    }


# ---------- Small utilities ----------
def safe_number(n: Any, default: float = 0.0, ndigits: int = 2) -> float:
    try:
        return round(float(n), ndigits)
    except Exception:
        return default
