"""
config.py - Central configuration for Grok Crypto Super Intel (PR 1+)

Lightweight, env-driven, zero external deps.
Used by persistence, future data tiers, alerts, etc.
"""

import os
from pathlib import Path
from typing import Optional

# Persistence
ENABLE_PERSISTENCE: bool = os.getenv("ENABLE_PERSISTENCE", "1").lower() in ("1", "true", "yes", "on")

# Where to store local state (respects .gitignore entries already present)
DATA_DIR: Path = Path(os.getenv("CRYPTO_INTEL_DATA_DIR", ".")).expanduser().resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)

PORTFOLIO_STATE_JSON: Path = DATA_DIR / os.getenv("PORTFOLIO_STATE_JSON_NAME", "portfolio_state.json")
PORTFOLIO_STATE_SQLITE: Path = DATA_DIR / os.getenv("PORTFOLIO_STATE_SQLITE_NAME", "portfolio_state.db")

# Future: feature flags (used by later PRs and v3 extensions)
ENABLE_TIERED_DATA: bool = os.getenv("ENABLE_TIERED_DATA", "1").lower() in ("1", "true", "yes")
ENABLE_REPORTS: bool = os.getenv("ENABLE_REPORTS", "1").lower() in ("1", "true", "yes")
ENABLE_ALERTS: bool = os.getenv("ENABLE_ALERTS", "0").lower() in ("1", "true", "yes")
ENABLE_ALERTS_SCHED: bool = os.getenv("ENABLE_ALERTS_SCHED", "0").lower() in ("1", "true", "yes")
ENABLE_REAL_ETF_FLOWS: bool = os.getenv("ENABLE_REAL_ETF_FLOWS", "0").lower() in ("1", "true", "yes")
ENABLE_OBSERVABILITY: bool = os.getenv("ENABLE_OBSERVABILITY", "1").lower() in ("1", "true", "yes")
ENABLE_MULTI_ASSET_BACKTEST: bool = os.getenv("ENABLE_MULTI_ASSET_BACKTEST", "0").lower() in ("1", "true", "yes")
ENABLE_UI_THEMES: bool = os.getenv("ENABLE_UI_THEMES", "0").lower() in ("1", "true", "yes")
ENABLE_HYBRID_ITERATION: bool = os.getenv("ENABLE_HYBRID_ITERATION", "1").lower() in ("1", "true", "yes")  # report refinement loops

def get_feature_flag(name: str, default: bool = False) -> bool:
    """Central helper for feature flags (reuse/extend for v3). Case-insensitive env lookup."""
    env_name = name.upper() if not name.startswith("ENABLE_") else name
    if not env_name.startswith("ENABLE_"):
        env_name = f"ENABLE_{env_name}"
    val = os.getenv(env_name)
    if val is None:
        return default
    return val.lower() in ("1", "true", "yes", "on")

# Tiered / Premium API keys (PR2+)
# All optional; code must always graceful-degrade to free sources
GLASSNODE_API_KEY: Optional[str] = os.getenv("GLASSNODE_API_KEY")
ARKHAM_API_KEY: Optional[str] = os.getenv("ARKHAM_API_KEY")
LUNARCRUSH_API_KEY: Optional[str] = os.getenv("LUNARCRUSH_API_KEY")
COINGECKO_API_KEY: Optional[str] = os.getenv("COINGECKO_API_KEY")  # for pro if available

# Retry & rate limit config (PR2)
RETRY_MAX_ATTEMPTS: int = int(os.getenv("RETRY_MAX_ATTEMPTS", "3"))
RETRY_BASE_DELAY: float = float(os.getenv("RETRY_BASE_DELAY", "1.0"))
CG_RATE_LIMIT_INTERVAL: float = float(os.getenv("CG_RATE_LIMIT_INTERVAL", "1.2"))  # seconds

# Basic metadata
APP_NAME = "Grok Crypto Super Intel"
APP_VERSION = "0.4.0"  # bumped for PR4 hybrid super reports + reports package
