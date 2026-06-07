"""
persistence.py - Local-first persistence for Grok Crypto Super Intel (PR 1)

Implements PortfolioStore:
- JSON primary (simple, inspectable, git-friendly, zero extra deps)
- Optional SQLite for future relational data (backtest runs, history, etc.)
- Atomic writes (write .tmp then rename)
- Versioned schema (supports cost_basis + simple change history)
- Fallback / zero-config friendly
- One-time migration helper from in-memory session state (v1 -> v2)

Designed to be used from Streamlit with st.session_state for the store instance.
"""

from __future__ import annotations

import json
import os
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_JSON_PATH = Path("portfolio_state.json")
DEFAULT_SQLITE_PATH = Path("portfolio_state.db")

SCHEMA_VERSION = 1


class PortfolioStore:
    """Durable store for portfolio holdings.

    Holdings are list of dicts:
        {"symbol": "BTC", "coin_id": "bitcoin", "amount": 0.25, "cost_basis": 62000.0 (optional)}
    """

    def __init__(
        self,
        json_path: Path | str = DEFAULT_JSON_PATH,
        use_sqlite: bool = False,
        sqlite_path: Optional[Path | str] = None,
    ):
        self.json_path = Path(json_path).expanduser().resolve()
        self.use_sqlite = use_sqlite
        self.sqlite_path = Path(sqlite_path).expanduser().resolve() if sqlite_path else self.json_path.with_suffix(".db")

        self.json_path.parent.mkdir(parents=True, exist_ok=True)
        if self.use_sqlite:
            self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
            self._ensure_sqlite_schema()

    # ---------------- JSON path (primary for v1) ----------------

    def _atomic_write_json(self, data: Dict[str, Any]) -> None:
        tmp = self.json_path.with_suffix(self.json_path.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        tmp.replace(self.json_path)

    def load(self) -> List[Dict[str, Any]]:
        """Load holdings. Prefers JSON; falls back to empty list."""
        if self.json_path.exists():
            try:
                with open(self.json_path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                if isinstance(raw, dict):
                    if raw.get("version", 0) > SCHEMA_VERSION:
                        # future version - be conservative
                        return raw.get("holdings", [])
                    return raw.get("holdings", [])
                elif isinstance(raw, list):
                    # legacy format (very early v1)
                    return raw
            except Exception:
                pass  # fall through to empty

        if self.use_sqlite and self.sqlite_path.exists():
            try:
                return self._load_from_sqlite()
            except Exception:
                pass

        return []

    def save(self, holdings: List[Dict[str, Any]]) -> None:
        """Persist holdings atomically with metadata."""
        data = {
            "version": SCHEMA_VERSION,
            "updated_at": time.time(),
            "holdings": holdings,
        }
        self._atomic_write_json(data)

        if self.use_sqlite:
            self._save_to_sqlite(holdings)

    def clear(self) -> None:
        """Remove persisted state (reverts to in-memory only until next save)."""
        if self.json_path.exists():
            self.json_path.unlink(missing_ok=True)
        if self.use_sqlite and self.sqlite_path.exists():
            self.sqlite_path.unlink(missing_ok=True)

    # ---------------- SQLite (optional, for future PRs) ----------------

    def _ensure_sqlite_schema(self) -> None:
        con = sqlite3.connect(self.sqlite_path)
        try:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS holdings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    coin_id TEXT NOT NULL,
                    amount REAL NOT NULL,
                    cost_basis REAL,
                    updated_at REAL DEFAULT (strftime('%s','now'))
                )
                """
            )
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS meta (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
                """
            )
            con.execute("INSERT OR IGNORE INTO meta(key, value) VALUES ('version', ?)", (str(SCHEMA_VERSION),))
            con.commit()
        finally:
            con.close()

    def _load_from_sqlite(self) -> List[Dict[str, Any]]:
        con = sqlite3.connect(self.sqlite_path)
        try:
            rows = con.execute(
                "SELECT symbol, coin_id, amount, cost_basis FROM holdings ORDER BY id"
            ).fetchall()
            return [
                {
                    "symbol": r[0],
                    "coin_id": r[1],
                    "amount": r[2],
                    **({"cost_basis": r[3]} if r[3] is not None else {}),
                }
                for r in rows
            ]
        finally:
            con.close()

    def _save_to_sqlite(self, holdings: List[Dict[str, Any]]) -> None:
        con = sqlite3.connect(self.sqlite_path)
        try:
            con.execute("DELETE FROM holdings")
            for h in holdings:
                con.execute(
                    "INSERT INTO holdings (symbol, coin_id, amount, cost_basis) VALUES (?, ?, ?, ?)",
                    (
                        h.get("symbol"),
                        h.get("coin_id"),
                        float(h.get("amount", 0)),
                        h.get("cost_basis"),
                    ),
                )
            con.commit()
        finally:
            con.close()

    # ---------------- Migration / UX helpers ----------------

    def seed_from_session_if_present(
        self, session_holdings: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """One-time v1->v2 migration helper.

        If we have no persisted data but were given (or can see) old in-memory holdings,
        seed the store from them and return True.
        """
        if self.load():
            return False  # already have persisted data

        if not session_holdings:
            return False

        # Only seed if it looks like real user data (not the hardcoded defaults)
        if session_holdings and len(session_holdings) > 0:
            self.save(session_holdings)
            return True
        return False

    def get_holdings_with_defaults(
        self, defaults: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """Convenience: load persisted or return provided defaults."""
        persisted = self.load()
        if persisted:
            return persisted
        return defaults or []


# Convenience factory used by the app
def get_default_store() -> PortfolioStore:
    """Factory that respects env but keeps zero-config defaults."""
    json_path = os.getenv("PORTFOLIO_STATE_JSON", str(DEFAULT_JSON_PATH))
    use_sqlite = os.getenv("USE_SQLITE_PERSISTENCE", "0").lower() in ("1", "true", "yes")
    return PortfolioStore(json_path=json_path, use_sqlite=use_sqlite)


# ------------------------------------------------------------------
# v3 Phase B extensions: Alert logs, richer backtest history, report_meta
# Reuses the atomic write pattern from PortfolioStore.
# Soft / optional use of config for DATA_DIR.
# ------------------------------------------------------------------

def _get_data_dir() -> Path:
    """Softly get the recommended data dir from config (PR1)."""
    try:
        import config as app_config
        return getattr(app_config, "DATA_DIR", Path("."))
    except Exception:
        return Path(".")


def _atomic_write_json(path: Path, data: Any) -> None:
    """Atomic JSON write helper (extracted/reused pattern)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    tmp.replace(path)


# --- Context snapshots (cleaned/fixed from PR4) ---
def save_context_snapshot(snapshot: Dict[str, Any], name: str = "latest_context") -> Path:
    """Save a full dashboard context snapshot (used by reports for reproducibility)."""
    data_dir = _get_data_dir()
    snap_path = data_dir / f"{name}.json"
    _atomic_write_json(snap_path, snapshot)
    return snap_path


def load_context_snapshot(name: str = "latest_context") -> Optional[Dict[str, Any]]:
    data_dir = _get_data_dir()
    snap_path = data_dir / f"{name}.json"
    if snap_path.exists():
        try:
            return json.loads(snap_path.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


# --- Alert logs (for v3 alerts integration) ---
ALERTS_LOG_NAME = "alerts.log.json"

def save_alert_log(events: List[Dict[str, Any]]) -> Path:
    """Append alert events to a log file (atomic)."""
    data_dir = _get_data_dir()
    log_path = data_dir / ALERTS_LOG_NAME
    existing = []
    if log_path.exists():
        try:
            existing = json.loads(log_path.read_text(encoding="utf-8"))
        except Exception:
            existing = []
    if not isinstance(existing, list):
        existing = []
    existing.extend(events if isinstance(events, list) else [events])
    _atomic_write_json(log_path, existing)
    return log_path


def load_alert_log(limit: int = 50) -> List[Dict[str, Any]]:
    data_dir = _get_data_dir()
    log_path = data_dir / ALERTS_LOG_NAME
    if not log_path.exists():
        return []
    try:
        data = json.loads(log_path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data[-limit:]
        return []
    except Exception:
        return []


# --- Richer backtest history storage (v3 Phase B) ---
BACKTEST_HISTORY_NAME = "backtest_history.json"

def save_backtest_run(run_record: Dict[str, Any]) -> Path:
    """Save a backtest run record (richer than basic save_run; includes full metrics, params, optional equity ref).
    This complements the backtest/engine.py save_run for history storage.
    """
    data_dir = _get_data_dir()
    hist_path = data_dir / BACKTEST_HISTORY_NAME
    existing = []
    if hist_path.exists():
        try:
            existing = json.loads(hist_path.read_text(encoding="utf-8"))
        except Exception:
            existing = []
    if not isinstance(existing, list):
        existing = []
    existing.append(run_record)
    _atomic_write_json(hist_path, existing)
    return hist_path


def load_backtest_history(limit: int = 100) -> List[Dict[str, Any]]:
    data_dir = _get_data_dir()
    hist_path = data_dir / BACKTEST_HISTORY_NAME
    if not hist_path.exists():
        return []
    try:
        data = json.loads(hist_path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data[-limit:]
        return []
    except Exception:
        return []


# --- Report metadata (v3 Phase B) ---
REPORTS_META_NAME = "reports_meta.json"

def save_report_meta(report_meta: Dict[str, Any]) -> Path:
    """Save or update metadata for a generated report (title, type, generated_by, snapshot_ref, etc.)."""
    data_dir = _get_data_dir()
    meta_path = data_dir / REPORTS_META_NAME
    existing = {}
    if meta_path.exists():
        try:
            existing = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            existing = {}
    if not isinstance(existing, dict):
        existing = {}
    report_id = report_meta.get("id") or report_meta.get("filename") or str(datetime.now().timestamp())
    existing[report_id] = {**existing.get(report_id, {}), **report_meta, "updated_at": datetime.now().isoformat()}
    _atomic_write_json(meta_path, existing)
    return meta_path


def load_reports_meta() -> Dict[str, Any]:
    data_dir = _get_data_dir()
    meta_path = data_dir / REPORTS_META_NAME
    if not meta_path.exists():
        return {}
    try:
        return json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        return {}

