# Grok Crypto Super Intel

**The ultimate AI-powered crypto intelligence platform — built to be *super*.**

Live market pulse, real portfolio tracking, powerful X sentiment (god-mode when used inside Grok workspace), production-grade backtesting, on-chain TVL intelligence (DeFiLlama), and Grok AI co-pilot + structured reports.

## What Makes It Super (v1)

- **Real data, not placeholders**: CoinGecko (global + coins + OHLC), alternative.me Fear & Greed (live gauge), DeFiLlama (chains + protocols TVL), CCXT public candles.
- **Modular & clean architecture**: `data.py` (rate-limited, cached-friendly fetchers) + rich Streamlit UI.
- **Working modules today**:
  - Market Pulse: total cap/volume, BTC/ETH dominance, Fear & Greed visual, sortable top coins table, 24h movers.
  - Portfolio Tracker: add holdings, live prices, total value, allocation pie, concentration risk.
  - X Sentiment Analyzer: designed for native Grok X tools (keyword + semantic + reasoning) + quick local heuristics.
  - Strategy Backtester: real OHLCV, SMA crossover or RSI strategies, equity curve vs buy-and-hold, rough Sharpe + returns.
  - On-Chain & ETF: live DeFiLlama TVL leaders + manual ETF flow notes (automation in v2).
  - Grok AI Co-Pilot + Reports: scaffolding + direct path to leverage full agent superpowers (X searches, web research, synthesis).
- **X-native advantage**: When run inside this Grok TUI/workspace you get *actual* deep X intelligence using the built-in X search tools — something no other open crypto dashboard has out of the box.
- **Fast to run, polite to free APIs**: sensible caching, rate limiting, pure public endpoints.

## Quick Start

```bash
git clone https://github.com/AgentMindCloud/grok-crypto-super-intel.git
cd grok-crypto-super-intel
pip install -r requirements.txt
streamlit run app.py
```

## Requirements

See [requirements.txt](requirements.txt). Core stack stays lightweight:
streamlit, pandas, plotly, requests, ccxt, yfinance.

## Vision & Roadmap

**v1 (current)**: Make every tab actually *do* useful work with live public data + excellent UX. Strong foundation + the unique "Grok + X tools" super power.

**PR 1 (Persistence Foundation)**: Portfolio holdings are now durable by default (local `portfolio_state.json`, atomic writes, versioned). One-time migration helper from in-memory v1 state + UI controls (Save / Reload / Clear / Import). Zero-config. Disable with `ENABLE_PERSISTENCE=0`. See `persistence.py`, `config.py`, and the Portfolio tab in `app.py`.

**PR 2 (Data Layer Hardening + Tiered Sources & ETF)**: 
- Configurable retries + exponential backoff (wraps all JSON fetches).
- Tiered/premium scaffolding (Glassnode etc.) with if-key-else graceful fallback to free sources.
- `get_coin_market_chart` now actively used (price history charts).
- New `integrations/etf.py`: yfinance price series for spot ETFs (IBIT etc.) + basic volume/price-change flow proxies.
- Minor UI updates in Market Pulse (BTC chart) + On-Chain & ETF (live proxy data instead of pure manual).
- See `data.py`, `config.py`, `integrations/etf.py`, and updated sections in `app.py` / README.

**PR 3 (Advanced Backtest Engine)**:
- Fully modular `backtest/` package (engine.py, strategies.py, metrics.py) extracted + significantly upgraded from the original inline pandas logic.
- New capabilities: position sizing (fixed/percent/vol-target), stop-loss handling, simple grid parameter optimization, richer metrics (max DD, win rate, profit factor, improved Sharpe).
- UI in Strategy Backtester tab expanded with new controls while preserving the original experience.
- Optional run saving (demo integration with PR1 persistence).
- See `backtest/` package, updated Strategy Backtester section in `app.py`, and `tests/test_backtest.py`.

**PR 4 (Reports, One-Click Super Reports & Hybrid Agent Integration)**:
- New `reports/` package with `generator.py` that builds rich, live-context prompts.
- `prompts/super-report-template.md` and `reports/templates/` for consistent output.
- Heavily enhanced **Grok AI Co-Pilot** and **Reports** tabs:
  - "Export Context for Grok" (1-click full live snapshot + super prompt ready for native X tools).
  - "1-Click Generate Super Report Draft" that saves a structured starting .md embedding all current data (market, portfolio, backtest, on-chain/ETF).
  - Auto-discovery and preview/download of all `reports/*.md` files.
- Soft use of persistence for context snapshots.
- Makes the "Pro move" / hybrid X-native superpower first-class and repeatable in the UI.
- See `reports/`, `prompts/`, updated Co-Pilot + Reports sections in `app.py`, and the expanded hybrid workflow description in this README.

**v3 Super Features (new awesome extensions, Phase A + B in progress)**:
- Alerts & notifications (new `integrations/alerts.py`): triggers on F&G extremes, portfolio concentration, backtest signals/DD, data degradation. In-app + Telegram/Discord/webhook (soft on PR1 config/persistence for logs). ENABLE_ALERTS / ENABLE_ALERTS_SCHED flags. Quick surface in Market Pulse + scheduler.
- Headless scheduler (`reports/scheduler.py`): periodic reports/alerts/ETF refresh/backtest snapshots. `python -m reports.scheduler --once` or loop. Reuses all prior layers. File lock for concurrent use.
- Real ETF flows (enhanced `integrations/etf.py` + wired in On-Chain tab): lightweight public Farside-style scrape (UA + sleep + graceful) + yf proxy fallback when ENABLE_REAL_ETF_FLOWS=1. Richer context in prompts/drafts.
- Backtest extensions (Phase B): `run_multi_asset_backtest`, `walk_forward_backtest`, `save_richer_backtest_history` (integrates with persistence). See backtest/ and updated backtester info.
- UI/observability (Phase B): `ui/themes.py` + `ui/components.py` (extracted fng_gauge, health_sidebar, render helpers). ENABLE_UI_THEMES / ENABLE_OBSERVABILITY. Health sidebar in app (last fetches, alerts, etc.). Feature flag guards.
- Richer hybrid + report iteration (Phase B): Enhanced context (flows + alerts), "Load for refinement" in Reports tab (loads report + generates refinement prompt for Co-Pilot / main chat with native X tools).
- Config flags extended (get_feature_flag helper) for all v3 items + future (multi-asset, themes, observability, hybrid iteration).
- Persistence extended for alert logs, richer backtest history, report_meta (atomic, reuses PR1 patterns).
- See new files (ui/, updates to backtest/, reports/, persistence/, app.py) + this README for details. Phase C (packaging/CI/Docker) next.

**v2 ideas** (see also in-app notes):
- Full backtest engine (stops, position sizing, parameter search, multi-asset portfolios)
- Real ETF flow automation + on-chain ETF wallet tracking
- Persistent portfolio (json / sqlite / exchange read-only via CCXT)
- One-click "Grok Super Report" that pulls *everything* (market + X + on-chain + your portfolio) and writes beautiful markdown/PDF
- Alerts (Telegram/Discord/email), scheduled runs, more sources (optional paid tiers via env keys)
- Theming, multipage or custom components, better mobile
- Optional FastAPI backend + nicer frontend or export to other tools

**Full v2 design + phased PR plan + v3 roadmap**: See [designs/v2-super-crypto-intel.md](designs/v2-super-crypto-intel.md) (and the plan for new awesome features). Ready to extend the hybrid superpower.

## Packaging & Deployment (v3 Phase C)

The repo now includes production-grade packaging for easy sharing and deployment while preserving the lightweight standalone experience.

### Docker
- `Dockerfile`: Based on `python:3.11-slim`, installs deps, exposes 8501, volumes `/app/data` for persistence (portfolio, reports, backtest history, alerts, etc.).
- Build & run:
  ```bash
  docker build -t grok-crypto-super-intel .
  docker run -p 8501:8501 -v $(pwd)/data:/app/data grok-crypto-super-intel
  ```
- Data persists outside the container via volume (matches `CRYPTO_INTEL_DATA_DIR=/app/data`).
- Works with ENABLE_* flags, .env (mount if needed), and all v3 features.

### Streamlit Community Cloud / Other Hosting
- `streamlit run app.py` still works everywhere.
- Note: Cloud has ephemeral FS — persistence resets on redeploy. Use for viz/demo or mount external storage. For full persistence, prefer Docker/local or self-hosted.
- Quickstart: Fork the repo, connect to Streamlit Cloud, set secrets for any API keys (optional).

### CI
- `.github/workflows/ci.yml`: Runs on push/PR:
  - pytest (tests/)
  - ruff lint
  - black format check
  - Basic import verification for app + data layers.
- Keeps code quality high for contributions.

### Tests Expansion
- Tests expanded with Phase B coverage (multi-asset backtest, walk-forward, etc.) in `tests/test_backtest.py`.
- All new modules have skeleton + functional tests.
- Run locally: `python -m pytest tests/ -v`

See the design doc for full rollout notes (feature flags, staged, rollback via git or flags).

This makes the "super crypto repo" easy to deploy, test, and share while keeping the core "pip install + streamlit run" magic.

**v2 ideas** (see also in-app notes):
- Full backtest engine (stops, position sizing, parameter search, multi-asset portfolios)
- Real ETF flow automation + on-chain ETF wallet tracking
- Persistent portfolio (json / sqlite / exchange read-only via CCXT)
- One-click "Grok Super Report" that pulls *everything* (market + X + on-chain + your portfolio) and writes beautiful markdown/PDF
- Alerts (Telegram/Discord/email), scheduled runs, more sources (optional paid tiers via env keys)
- Theming, multipage or custom components, better mobile
- Optional FastAPI backend + nicer frontend or export to other tools

**Full v2 design + phased PR plan**: See [designs/v2-super-crypto-intel.md](designs/v2-super-crypto-intel.md) (produced via the design skill write-review loop; 6 realistic incremental PRs, Key Decisions, Open Questions, grounded in the current v1 code). Ready to execute starting with PR 1 (persistence).

This repo is meant to be *the* place you (or anyone) can run to dominate crypto research and decision making.

Built live with Grok for @JanSol0s and the community. Next-level features on request — just say the word (or open an issue).

---

**Pro move**: Run the Streamlit app for the beautiful dashboard, then come back to this chat / Grok TUI any time you want *insanely deep* X narrative scans, on-chain forensics, or full synthesized reports that the dashboard can't do alone. The combination is the real super power.

## Contributing / Extending

PRs welcome. Keep data sources free/public where possible. Add new modules as `data_xxx.py` helpers + a new page in `app.py`. Update this README when you ship.

Let's make it legendary. 🚀
