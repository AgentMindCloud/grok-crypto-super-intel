"""
tests/test_persistence.py - Basic tests for PR 1 PortfolioStore

Run with: python -m pytest tests/test_persistence.py -q
"""

import json
import tempfile
from pathlib import Path

import pytest

from persistence import PortfolioStore


def test_json_roundtrip(tmp_path: Path):
    store = PortfolioStore(json_path=tmp_path / "test_portfolio.json")

    holdings = [
        {"symbol": "BTC", "coin_id": "bitcoin", "amount": 0.5, "cost_basis": 65000.0},
        {"symbol": "ETH", "coin_id": "ethereum", "amount": 3.0},
    ]

    store.save(holdings)
    loaded = store.load()

    assert len(loaded) == 2
    assert loaded[0]["symbol"] == "BTC"
    assert loaded[0]["cost_basis"] == 65000.0
    assert "cost_basis" not in loaded[1]  # optional field omitted when absent


def test_clear_and_reload(tmp_path: Path):
    p = tmp_path / "p.json"
    store = PortfolioStore(json_path=p)

    store.save([{"symbol": "SOL", "coin_id": "solana", "amount": 10.0}])
    assert store.load()

    store.clear()
    assert store.load() == []


def test_seed_from_session(tmp_path: Path):
    p = tmp_path / "seed.json"
    store = PortfolioStore(json_path=p)

    session_data = [{"symbol": "BTC", "coin_id": "bitcoin", "amount": 0.1}]

    seeded = store.seed_from_session_if_present(session_data)
    assert seeded is True
    assert len(store.load()) == 1

    # second call should be no-op
    seeded2 = store.seed_from_session_if_present(session_data)
    assert seeded2 is False


def test_atomic_write(tmp_path: Path):
    p = tmp_path / "atomic.json"
    store = PortfolioStore(json_path=p)

    store.save([{"symbol": "X", "coin_id": "x", "amount": 1.0}])
    assert p.exists()

    # Simulate crash by leaving a .tmp (should be cleaned on next save)
    bad_tmp = p.with_suffix(".json.tmp")
    bad_tmp.write_text("corrupt")
    store.save([{"symbol": "Y", "coin_id": "y", "amount": 2.0}])

    loaded = store.load()
    assert loaded[0]["symbol"] == "Y"


def test_version_and_metadata(tmp_path: Path):
    p = tmp_path / "meta.json"
    store = PortfolioStore(json_path=p)
    store.save([{"symbol": "A", "coin_id": "a", "amount": 1}])

    raw = json.loads(p.read_text())
    assert raw["version"] == 1
    assert "updated_at" in raw
    assert isinstance(raw["holdings"], list)
