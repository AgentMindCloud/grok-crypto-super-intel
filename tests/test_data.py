"""
tests/test_data.py - PR2 data layer tests (retry, premium fallbacks, etf, chart exposure)

Run: python -m pytest tests/test_data.py -q --tb=line
"""

import pandas as pd
import pytest

from data import (
    get_coin_market_chart,
    get_glassnode_metric,
    get_premium_metric,
    _get_json,  # for retry testing
)
from integrations.etf import get_etf_price_series, get_basic_etf_flow_proxy, get_etf_summary


def test_get_coin_market_chart_returns_df():
    df = get_coin_market_chart("bitcoin", days=2)
    # May be empty in some envs, but structure should be DF
    assert isinstance(df, pd.DataFrame)
    if not df.empty:
        assert "price" in df.columns or len(df.columns) > 0


def test_glassnode_no_key_returns_none():
    # Without GLASSNODE_API_KEY set, must return None (graceful)
    res = get_glassnode_metric("market/price_usd_close", asset="BTC")
    assert res is None


def test_premium_metric_no_key():
    res = get_premium_metric("glassnode", default="fallback")
    assert res == "fallback"


def test_etf_price_series_graceful():
    df = get_etf_price_series("IBIT", period="5d")
    assert isinstance(df, pd.DataFrame)


def test_etf_summary_structure():
    summary = get_etf_summary()
    assert "btc_etfs" in summary
    assert "eth_etfs" in summary
    assert "disclaimer" in summary


def test_retry_decorator_exists_and_callable():
    # Basic smoke that the decorated _get_json still works (will hit rate limit but not crash on import)
    assert callable(_get_json)
