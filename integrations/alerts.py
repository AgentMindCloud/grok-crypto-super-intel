"""
integrations/alerts.py - Alerts & Notifications (v3 / PR5-like)

Triggers on key events (F&G extremes, portfolio concentration, backtest signals/DD, data degradation).
Delivery: in-app (return dicts for UI), + optional webhook/Telegram/Discord/email (via requests or stdlib).

Soft on PR1 (uses config + persistence for logs if available).
Graceful everywhere (like etf.py / data.py tiered scaffolding): no keys = no external delivery, still returns events.
Config via ENABLE_ALERTS + specific keys (TELEGRAM_BOT_TOKEN etc.).

Reuse patterns: atomic writes from persistence, graceful excepts, config flags.
"""

from __future__ import annotations
import os
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests  # already in requirements

# Soft imports for PR1 patterns (config + persistence for logs/history)
try:
    import config as app_config
    ENABLE_ALERTS = getattr(app_config, "ENABLE_ALERTS", False) or getattr(app_config, "ENABLE_ALERTS_SCHED", False)
    DATA_DIR = getattr(app_config, "DATA_DIR", Path("."))
except Exception:
    ENABLE_ALERTS = os.getenv("ENABLE_ALERTS", "0").lower() in ("1", "true", "yes") or os.getenv("ENABLE_ALERTS_SCHED", "0").lower() in ("1", "true", "yes")
    DATA_DIR = Path(".")

ALERT_LOG = DATA_DIR / "alerts.log.json"  # simple append log (protected by .gitignore)

def _log_alert(event: Dict[str, Any]) -> None:
    """Append alert to local log (atomic, following PR1 persistence pattern)."""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        existing: List[Dict] = []
        if ALERT_LOG.exists():
            try:
                existing = json.loads(ALERT_LOG.read_text(encoding="utf-8"))
            except Exception:
                existing = []
        if not isinstance(existing, list):
            existing = []
        existing.append({**event, "logged_at": datetime.now().isoformat()})
        tmp = ALERT_LOG.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(existing, indent=2, default=str), encoding="utf-8")
        tmp.replace(ALERT_LOG)
    except Exception:
        pass  # never break main flow


def _send_webhook(url: str, payload: Dict[str, Any]) -> bool:
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.ok
    except Exception:
        return False


def _send_telegram(token: str, chat_id: str, text: str) -> bool:
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        r = requests.post(url, data={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}, timeout=10)
        return r.ok
    except Exception:
        return False


# (Discord/email similar via webhooks or smtplib; stubs for now to keep deps minimal)


def check_and_alert(
    fng_value: Optional[int] = None,
    portfolio_concentration: Optional[float] = None,
    backtest_signal_flip: Optional[bool] = None,
    backtest_dd: Optional[float] = None,
    data_fetch_failed: Optional[bool] = None,
    extra_context: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Core checker. Returns list of triggered events (always, for in-app use).
    If ENABLE_ALERTS and keys present, also delivers externally.

    Triggers (per design Goals/PR5/Observability):
    - F&G < 20 (extreme fear) or > 80 (extreme greed)
    - Portfolio concentration > 40% top-1
    - Backtest signal flip or DD > 15%
    - Data fetch degradation (e.g. repeated failures)

    Reuses graceful patterns: returns events even on delivery fail.
    """
    events: List[Dict[str, Any]] = []
    now = datetime.now().isoformat()

    # F&G extreme
    if fng_value is not None:
        if fng_value <= 20:
            events.append({
                "type": "fng_extreme_fear",
                "value": fng_value,
                "message": f"Extreme Fear (F&G={fng_value}) — potential buying opportunity per historical patterns.",
                "timestamp": now,
            })
        elif fng_value >= 80:
            events.append({
                "type": "fng_extreme_greed",
                "value": fng_value,
                "message": f"Extreme Greed (F&G={fng_value}) — caution, potential reversal risk.",
                "timestamp": now,
            })

    # Portfolio concentration
    if portfolio_concentration is not None and portfolio_concentration > 40:
        events.append({
            "type": "portfolio_concentration",
            "value": portfolio_concentration,
            "message": f"High concentration: top holding {portfolio_concentration:.1f}% of portfolio.",
            "timestamp": now,
        })

    # Backtest signals
    if backtest_signal_flip:
        events.append({
            "type": "backtest_signal_flip",
            "message": "Backtest strategy signal flipped (new long/short opportunity).",
            "timestamp": now,
        })
    if backtest_dd is not None and backtest_dd < -15:  # negative = drawdown
        events.append({
            "type": "backtest_drawdown",
            "value": backtest_dd,
            "message": f"Backtest drawdown exceeded threshold: {backtest_dd:.1f}%.",
            "timestamp": now,
        })

    # Data fetch issues
    if data_fetch_failed:
        events.append({
            "type": "data_fetch_degraded",
            "message": "One or more data sources failed to refresh (using cached/last good values).",
            "timestamp": now,
        })

    if not events:
        return []

    # Log locally always (for history / in-app)
    for ev in events:
        _log_alert(ev)

    # External delivery (only if enabled + keys)
    if ENABLE_ALERTS:
        telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        telegram_chat = os.getenv("TELEGRAM_CHAT_ID")
        webhook_url = os.getenv("ALERT_WEBHOOK_URL")
        discord_webhook = os.getenv("DISCORD_WEBHOOK_URL")

        payload = {
            "title": "Grok Crypto Super Intel Alert",
            "events": events,
            "context": extra_context or {},
            "timestamp": now,
        }

        if telegram_token and telegram_chat:
            text = f"**{payload['title']}**\n" + "\n".join(f"- {e['message']}" for e in events)
            _send_telegram(telegram_token, telegram_chat, text)

        if webhook_url:
            _send_webhook(webhook_url, payload)

        if discord_webhook:
            _send_webhook(discord_webhook, {"content": f"**{payload['title']}**", "embeds": [{"description": "\n".join(e['message'] for e in events)}]})

        # Email stub (stdlib smtplib) left as future opt-in for minimal deps.

    return events


def get_recent_alerts(limit: int = 20) -> List[Dict[str, Any]]:
    """Read recent alerts from local log (for in-app history panel)."""
    if not ALERT_LOG.exists():
        return []
    try:
        data = json.loads(ALERT_LOG.read_text(encoding="utf-8"))
        return data[-limit:] if isinstance(data, list) else []
    except Exception:
        return []
