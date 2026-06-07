"""
reports/scheduler.py - Headless scheduler for periodic reports, alerts, ETF refresh (v3 / PR5).

Entry point: `python -m reports.scheduler --type daily --output reports/`

Reuses: data.py (fetches), persistence (snapshots/logs), reports/generator (drafts + prompts),
integrations (etf + new alerts), backtest (optional snapshots).

Simple loop by default (no new mandatory deps). Supports optional apscheduler if installed.
File locking note for concurrent Streamlit use (design Open Q #3).

Run in background / cron / systemd. Graceful; uses same free-API-first + caching as dashboard.
"""

from __future__ import annotations
import os
import time
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional

# Soft reuse of core modules (graceful if not fully present)
try:
    from data import get_global_data, get_fear_and_greed, get_coins_markets, get_defillama_chains, get_defillama_protocols
    from integrations.etf import get_etf_summary
    from reports.generator import get_live_context, generate_initial_report_draft
    from persistence import save_context_snapshot
    from integrations.alerts import check_and_alert, get_recent_alerts
except Exception as e:
    print(f"[scheduler] Warning: some modules unavailable for full features: {e}")

try:
    import config as app_config
    DATA_DIR = getattr(app_config, "DATA_DIR", Path("."))
    ENABLE_SCHED = getattr(app_config, "ENABLE_ALERTS_SCHED", False) or os.getenv("ENABLE_ALERTS_SCHED", "0").lower() in ("1","true","yes")
except Exception:
    DATA_DIR = Path(".")
    ENABLE_SCHED = os.getenv("ENABLE_ALERTS_SCHED", "0").lower() in ("1","true","yes")

REPORTS_DIR = DATA_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def _lock_file() -> Path:
    return DATA_DIR / ".scheduler.lock"


def _acquire_lock() -> bool:
    """Simple file lock (design note on concurrent Streamlit + scheduler)."""
    lock = _lock_file()
    if lock.exists():
        # stale lock cleanup (crude; improve with psutil or mtime in future)
        try:
            age = time.time() - lock.stat().st_mtime
            if age > 3600:  # 1h stale
                lock.unlink(missing_ok=True)
            else:
                return False
        except Exception:
            return False
    lock.write_text(str(os.getpid()))
    return True


def _release_lock() -> None:
    _lock_file().unlink(missing_ok=True)


def run_once(output_dir: Path = REPORTS_DIR, do_alerts: bool = True, do_etf: bool = True, do_backtest_snapshot: bool = False) -> None:
    """One cycle: fetch, snapshot, draft report, check alerts, optional ETF refresh."""
    print(f"[scheduler] Starting cycle at {datetime.now().isoformat()}")

    ctx = {}
    try:
        ctx = get_live_context() if 'get_live_context' in globals() else {}
    except Exception as e:
        print(f"[scheduler] Context collection error (continuing): {e}")

    # Always save a fresh context snapshot (PR4 pattern)
    try:
        snap = save_context_snapshot(ctx, name=f"scheduler_{datetime.now().strftime('%Y%m%d_%H%M')}")
        print(f"[scheduler] Snapshot saved: {snap}")
    except Exception as e:
        print(f"[scheduler] Snapshot error: {e}")

    # Generate draft super report (reuses PR4 generator)
    try:
        if 'generate_initial_report_draft' in globals():
            draft = generate_initial_report_draft(ctx, output_dir=output_dir)
            print(f"[scheduler] Draft report: {draft}")
    except Exception as e:
        print(f"[scheduler] Report draft error: {e}")

    # Alerts (reuses new integrations/alerts + PR1/2 data)
    if do_alerts and 'check_and_alert' in globals():
        try:
            fng = ctx.get("market", {}).get("fng", {}).get("value")
            conc = ctx.get("portfolio", {}).get("concentration_top1")
            events = check_and_alert(fng_value=fng, portfolio_concentration=conc, extra_context={"source": "scheduler"})
            if events:
                print(f"[scheduler] Alerts fired: {len(events)}")
        except Exception as e:
            print(f"[scheduler] Alert error: {e}")

    # ETF refresh (extend PR2)
    if do_etf and 'get_etf_summary' in globals():
        try:
            etf = get_etf_summary()
            print(f"[scheduler] ETF proxy refresh: {list(etf.get('btc_etfs', {}).keys())[:2]}...")
        except Exception as e:
            print(f"[scheduler] ETF refresh error: {e}")

    # Optional backtest snapshot (PR3 reuse)
    if do_backtest_snapshot:
        print("[scheduler] Backtest snapshot placeholder (extend with load_runs + persist)")

    print("[scheduler] Cycle complete.")


def main():
    parser = argparse.ArgumentParser(description="Grok Crypto Super Intel Headless Scheduler (v3)")
    parser.add_argument("--type", default="periodic", choices=["daily", "periodic"], help="Run type (for cron/docs)")
    parser.add_argument("--output", default=str(REPORTS_DIR), help="Output dir for drafts/reports")
    parser.add_argument("--interval", type=int, default=3600, help="Seconds between cycles (default 1h)")
    parser.add_argument("--once", action="store_true", help="Run one cycle and exit")
    args = parser.parse_args()

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    if not ENABLE_SCHED and not args.once:
        print("[scheduler] ENABLE_ALERTS_SCHED=0 (or not set). Running in --once mode only or set the flag.")
        if not args.once:
            return

    if not _acquire_lock():
        print("[scheduler] Another instance running (lock file present). Exiting.")
        return

    try:
        if args.once:
            run_once(out)
        else:
            print(f"[scheduler] Starting periodic loop (every {args.interval}s). Ctrl-C to stop.")
            while True:
                run_once(out)
                time.sleep(args.interval)
    finally:
        _release_lock()


if __name__ == "__main__":
    main()
