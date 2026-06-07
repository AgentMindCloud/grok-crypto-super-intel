"""
Grok Crypto Super Intel
The ultimate AI-powered crypto command center.
Modular, data-rich, and built to dominate research & trading insights.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from pathlib import Path
from datetime import datetime

from data import (
    get_global_data,
    get_coins_markets,
    get_fear_and_greed,
    get_defillama_chains,
    get_defillama_protocols,
    compute_portfolio_metrics,
    safe_number,
    get_coin_market_chart,  # PR2: now used in Market Pulse
)

# PR 1: Persistence (local-first, zero-config by default)
from config import ENABLE_PERSISTENCE, PORTFOLIO_STATE_JSON
from persistence import PortfolioStore, get_default_store

# PR 2: Data layer + ETF integration (minor usage in Market Pulse + On-Chain/ETF)
from integrations.etf import get_etf_summary, get_basic_etf_flow_proxy
from integrations.alerts import check_and_alert, get_recent_alerts  # v3 alerts
# get_coin_market_chart is already available via data import (used below)

# PR 3: Advanced modular backtester
from backtest.engine import run_backtest, optimize_strategy, save_run, load_runs
from backtest import strategies as bt_strategies

# PR 4: Super Reports + Hybrid Grok Integration
from reports.generator import build_super_prompt, get_live_context, generate_initial_report_draft
from persistence import save_context_snapshot, load_context_snapshot  # soft use for snapshots
from integrations.alerts import check_and_alert, get_recent_alerts  # v3
import json
from pathlib import Path
import glob

# v3 Phase B: UI theming + components (feature flagged)
from ui.themes import apply_crypto_theme
from ui.components import health_sidebar, render_backtest_results
from ui import components as ui_components

# -------------------------- Page Setup --------------------------
st.set_page_config(
    page_title="Grok Crypto Super Intel",
    layout="wide",
    page_icon="🚀",
    initial_sidebar_state="expanded",
)

# v3 Phase B: Apply crypto theme if enabled (non-breaking)
try:
    from config import get_feature_flag
    if get_feature_flag("UI_THEMES", False):
        apply_crypto_theme()
except Exception:
    pass

st.title("🚀 Grok Crypto Super Intel")
st.caption("Ultimate Grok-powered crypto intelligence platform • Live data • X-native sentiment • Real backtesting • On-chain flows")

# -------------------------- Sidebar Navigation --------------------------
PAGES = [
    "Market Pulse",
    "Portfolio Tracker",
    "X Sentiment Analyzer",
    "Strategy Backtester",
    "On-Chain & ETF",
    "Grok AI Co-Pilot",
    "Reports",
]

page = st.sidebar.selectbox("📍 Module", PAGES, index=0)
st.sidebar.markdown("---")
st.sidebar.caption("Data: CoinGecko (free) • alternative.me • DeFiLlama • CCXT (public)\nX analysis powered by Grok + native tools in this workspace")

# v3 Phase B: Health / Observability sidebar (when ENABLE_OBSERVABILITY)
try:
    from config import get_feature_flag
    if get_feature_flag("OBSERVABILITY", False):
        # Placeholder data; in full impl would track last fetches from data layer
        health_sidebar(
            last_fetches={"CoinGecko": "just now", "DeFiLlama": "2m ago"},
            call_counts={"global": 12, "markets": 8, "backtest": 3},
            rate_headroom="< 10 calls/min typical",
            alerts_count=len(get_recent_alerts(10)) if 'get_recent_alerts' in dir() else 0,
        )
except Exception:
    pass

# -------------------------- Helpers --------------------------
@st.cache_data(ttl=45)
def cached_global():
    return get_global_data()

@st.cache_data(ttl=60)
def cached_markets(limit=50):
    return get_coins_markets(per_page=limit)

@st.cache_data(ttl=120)
def cached_fng():
    return get_fear_and_greed(limit=1)

@st.cache_data(ttl=180)
def cached_defi_chains():
    return get_defillama_chains()

@st.cache_data(ttl=180)
def cached_defi_protocols(limit=15):
    return get_defillama_protocols(limit=limit)


def fng_gauge(value: int, classification: str):
    """Simple visual for Fear & Greed."""
    color = "#22c55e" if value >= 75 else ("#eab308" if value >= 55 else ("#f97316" if value >= 35 else "#ef4444"))
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={"text": f"Fear & Greed • {classification}"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": color},
            "steps": [
                {"range": [0, 25], "color": "#450a0a"},
                {"range": [25, 45], "color": "#431407"},
                {"range": [45, 55], "color": "#422006"},
                {"range": [55, 75], "color": "#14532d"},
                {"range": [75, 100], "color": "#052e16"},
            ],
            "threshold": {"line": {"color": "white", "width": 2}, "thickness": 0.8, "value": value},
        },
    ))
    fig.update_layout(height=220, margin=dict(l=10, r=10, t=30, b=10))
    return fig


# -------------------------- MARKET PULSE (Real & Super) --------------------------
if page == "Market Pulse":
    st.header("📊 Live Market Pulse")
    st.markdown("Real-time overview powered by CoinGecko + alternative.me Fear & Greed. Auto-refreshes via cache.")

    col1, col2, col3 = st.columns([1.1, 1.1, 1])

    with st.spinner("Fetching live market data..."):
        try:
            g = cached_global()
            markets = cached_markets(limit=30)
            fng = cached_fng()
        except Exception as e:
            st.error(f"Data fetch issue: {e}")
            g, markets, fng = {}, [], {"value": 50, "classification": "Neutral (error)"}

    # Top metrics row
    with col1:
        st.metric(
            "Total Market Cap",
            f"${safe_number(g.get('total_market_cap_usd', 0)/1e12, 2)}T",
            delta=f"{safe_number(g.get('market_cap_change_24h', 0), 2)}% 24h",
        )
        st.metric("24h Volume", f"${safe_number(g.get('total_volume_24h_usd', 0)/1e9, 1)}B")

    with col2:
        st.metric("BTC Dominance", f"{safe_number(g.get('btc_dominance', 0), 1)}%")
        st.metric("ETH Dominance", f"{safe_number(g.get('eth_dominance', 0), 1)}%")

    with col3:
        fng_val = fng.get("value", 50)
        fng_cls = fng.get("classification", "Neutral")
        st.plotly_chart(fng_gauge(fng_val, fng_cls), use_container_width=True)

    st.markdown("---")

    # Coins table + movers
    st.subheader("Top Coins by Market Cap")

    if markets:
        df = pd.DataFrame(markets)
        # Nice columns
        display = df[[
            "name", "symbol", "current_price", "market_cap", "total_volume",
            "price_change_percentage_24h", "price_change_percentage_7d_in_currency"
        ]].copy()
        display.columns = ["Name", "Symbol", "Price (USD)", "Market Cap", "24h Vol", "24h %", "7d %"]
        display["Symbol"] = display["Symbol"].str.upper()
        display = display.sort_values("Market Cap", ascending=False)

        # Format
        display["Price (USD)"] = display["Price (USD)"].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "-")
        display["Market Cap"] = display["Market Cap"].apply(lambda x: f"${x/1e9:,.1f}B" if pd.notna(x) else "-")
        display["24h Vol"] = display["24h Vol"].apply(lambda x: f"${x/1e9:,.1f}B" if pd.notna(x) else "-")
        display["24h %"] = display["24h %"].apply(lambda x: f"{x:+.1f}%" if pd.notna(x) else "-")
        display["7d %"] = display["7d %"].apply(lambda x: f"{x:+.1f}%" if pd.notna(x) else "-")

        st.dataframe(
            display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "24h %": st.column_config.TextColumn("24h %", help="Price change last 24h"),
                "7d %": st.column_config.TextColumn("7d %", help="Price change last 7 days"),
            },
        )

        # Quick movers
        st.subheader("🔥 Biggest 24h Movers (Top 30)")
        movers = df.nlargest(8, "price_change_percentage_24h")[["name", "symbol", "price_change_percentage_24h", "current_price"]]
        movers["symbol"] = movers["symbol"].str.upper()
        movers["price_change_percentage_24h"] = movers["price_change_percentage_24h"].round(1)
        st.dataframe(movers, use_container_width=True, hide_index=True)

        # PR2: Light use of get_coin_market_chart (was defined but unused in v1)
        try:
            btc_chart = get_coin_market_chart("bitcoin", days=14)
            if not btc_chart.empty:
                st.subheader("BTC Price (last 14d, via CoinGecko market_chart)")
                st.line_chart(btc_chart["price"])
        except Exception:
            pass  # graceful
    else:
        st.warning("No market data returned. Check connection or try refresh.")

    st.info("💡 Pro tip: Switch to the Grok AI Co-Pilot or Reports tab for narrative synthesis on this data. In this workspace we have god-tier X + research tools.")

    # v3 quick alerts/observability surface (when enabled; Phase A)
    try:
        from config import get_feature_flag
        if get_feature_flag("ALERTS", False) or get_feature_flag("ALERTS_SCHED", False):
            fng_val = fng.get("value") if isinstance(fng, dict) else None
            conc = None  # would pull from portfolio context in full health panel
            events = check_and_alert(fng_value=fng_val, portfolio_concentration=conc)
            if events:
                st.warning(f"⚠️ {len(events)} active alert(s) — see Co-Pilot/Reports or scheduler for details.")
            recent = get_recent_alerts(3)
            if recent:
                with st.expander("Recent alerts (v3)"):
                    for ev in recent:
                        st.caption(f"{ev.get('timestamp','')}: {ev.get('message','')}")
    except Exception:
        pass  # graceful, no breakage


# -------------------------- PORTFOLIO TRACKER (Functional + PR1 Persistence) --------------------------
elif page == "Portfolio Tracker":
    st.header("💼 Portfolio Tracker")
    st.caption("Track holdings with durable local persistence (PR 1). Prices update live from CoinGecko.")

    # --- PR 1: Initialize persistence store (zero-config by default) ---
    if ENABLE_PERSISTENCE:
        if "portfolio_store" not in st.session_state:
            st.session_state.portfolio_store = get_default_store()

        store: PortfolioStore = st.session_state.portfolio_store

        # One-time v1 -> v2 migration: if we have old in-memory data and nothing persisted yet
        if "holdings" not in st.session_state:
            old = st.session_state.get("_old_holdings_for_migration")
            seeded = store.seed_from_session_if_present(old)
            persisted = store.load()

            if persisted:
                st.session_state.holdings = persisted
            else:
                st.session_state.holdings = [
                    {"symbol": "BTC", "coin_id": "bitcoin", "amount": 0.25},
                    {"symbol": "ETH", "coin_id": "ethereum", "amount": 2.0},
                ]
                # Auto-save the defaults on first run so user has a starting point
                store.save(st.session_state.holdings)

            if seeded:
                st.success("Seeded holdings from previous in-memory session (one-time v1→v2 migration).")
    else:
        # Pure session fallback (original v1 behavior)
        if "holdings" not in st.session_state:
            st.session_state.holdings = [
                {"symbol": "BTC", "coin_id": "bitcoin", "amount": 0.25},
                {"symbol": "ETH", "coin_id": "ethereum", "amount": 2.0},
            ]
        store = None  # type: ignore

    # --- Add / Edit form (unchanged UX) ---
    with st.expander("➕ Add / Edit Holding", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            sym = st.text_input("Symbol", value="SOL").upper().strip()
        with c2:
            cid = st.text_input("CoinGecko ID (e.g. solana)", value="solana").lower().strip()
        with c3:
            amt = st.number_input("Amount", min_value=0.0, value=10.0, step=0.1)

        if st.button("Add / Update Holding"):
            existing = [h for h in st.session_state.holdings if h["symbol"] != sym]
            st.session_state.holdings = existing + [{"symbol": sym, "coin_id": cid, "amount": amt}]
            if ENABLE_PERSISTENCE and store is not None:
                store.save(st.session_state.holdings)
            st.success(f"Updated {sym}")

        if st.button("Clear All Holdings"):
            st.session_state.holdings = []
            if ENABLE_PERSISTENCE and store is not None:
                store.save(st.session_state.holdings)
            st.rerun()

    # --- Persistence controls (new in PR 1) ---
    if ENABLE_PERSISTENCE and store is not None:
        with st.expander("💾 Persistence Controls", expanded=False):
            col_p1, col_p2, col_p3, col_p4 = st.columns(4)

            with col_p1:
                if st.button("Save now"):
                    store.save(st.session_state.holdings)
                    st.toast("Portfolio saved to disk")

            with col_p2:
                if st.button("Reload from disk"):
                    st.session_state.holdings = store.load() or st.session_state.holdings
                    st.rerun()

            with col_p3:
                if st.button("Clear persisted file"):
                    store.clear()
                    st.warning("Persisted file removed. Current session holdings remain until cleared or app restart.")
                    st.rerun()

            with col_p4:
                if st.button("Import from current session (if any)"):
                    if store.seed_from_session_if_present(st.session_state.get("holdings")):
                        st.session_state.holdings = store.load()
                        st.success("Imported and persisted.")
                    else:
                        st.info("Nothing new to import or already persisted.")
                    st.rerun()

            st.caption(f"State file: {PORTFOLIO_STATE_JSON}  •  Persistence: {'ON' if ENABLE_PERSISTENCE else 'OFF'}")

    # --- Live prices + display (largely unchanged) ---
    holdings = st.session_state.holdings
    if holdings:
        ids = ",".join([h["coin_id"] for h in holdings])
        try:
            price_rows = get_coins_markets(ids=ids, per_page=len(holdings))
            prices = {p["id"]: p["current_price"] for p in price_rows}
        except Exception:
            prices = {}

        metrics = compute_portfolio_metrics(holdings, prices)

        st.metric("Total Portfolio Value (USD)", f"${metrics['total_value_usd']:,.2f}")
        st.caption(f"Top holding concentration: {metrics['concentration_top1']:.1f}%")

        # Table
        port_df = pd.DataFrame(metrics["holdings"])
        port_df["value_usd"] = port_df["value_usd"].round(2)
        port_df["weight_pct"] = port_df["weight_pct"].round(1)
        st.dataframe(port_df, use_container_width=True, hide_index=True)

        # Allocation pie
        if metrics["total_value_usd"] > 0:
            pie_df = pd.DataFrame(metrics["holdings"])
            fig = px.pie(pie_df, values="value_usd", names="symbol", title="Allocation")
            fig.update_layout(height=320)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No holdings yet. Add some above.")

    st.markdown("---")
    st.caption(
        "PR 1: Holdings are now persisted locally (json by default). "
        "Future: Connect exchange read-only keys (CCXT) or import CSV. P&L vs cost_basis in later PRs."
    )


# -------------------------- X SENTIMENT ANALYZER (Super via Grok env) --------------------------
elif page == "X Sentiment Analyzer":
    st.header("🐦 X (Twitter) Sentiment Analyzer")
    st.caption("This module is intentionally super-powered when used inside the Grok workspace (native X search + semantic + Grok reasoning).")

    st.markdown("""
    **How to get god-tier crypto X intel right now:**
    1. In the chat (this TUI), ask me things like:
       - "Analyze recent X sentiment on $SOL using keyword + semantic search"
       - "Find whale narratives and influencer takes on Bitcoin ETF flows this week"
       - "Run a narrative scan across top 20 coins"
    2. I will use the full X tool suite (`x_keyword_search`, `x_semantic_search`, etc.) + synthesis.
    3. Paste key findings back here or ask me to generate a report for the Reports tab.

    Standalone mode (no keys):
    """)

    query = st.text_input("Cashtag or keywords (e.g. $BTC OR bitcoin ETF)", value="$BTC")
    hours = st.slider("Lookback hours (for manual paste analysis)", 1, 48, 6)

    if st.button("Prepare Analysis Frame"):
        st.info(f"Analysis frame ready for: {query} (last ~{hours}h). Now switch to the main chat and say: 'Deep X sentiment scan on {query} last {hours} hours using all tools, summarize narratives, volume, and conviction.'")
        st.code(f"Example prompt:\nDeep X sentiment + narrative scan for {query}. Use keyword search + semantic search. Include volume signals, top accounts, and whether retail vs smart money is leaning bullish/bearish.")

    st.markdown("---")
    st.subheader("Quick Manual Sentiment (paste tweets)")
    pasted = st.text_area("Paste 5-20 tweets or posts (one per line)", height=150)
    if st.button("Run Basic Sentiment on Paste") and pasted.strip():
        lines = [l.strip() for l in pasted.splitlines() if l.strip()]
        bullish = sum(1 for l in lines if any(w in l.lower() for w in ["bull", "moon", "buy", "up", "ath", "breakout"]))
        bearish = sum(1 for l in lines if any(w in l.lower() for w in ["bear", "dump", "crash", "down", "sell", "rug"]))
        st.write(f"**Rough signals** — Bullish-ish keywords: {bullish} | Bearish-ish: {bearish} | Total: {len(lines)}")
        st.caption("This is a toy heuristic. Real power = use the Grok X tools in the main session.")


# -------------------------- STRATEGY BACKTESTER (PR 3 - Advanced Modular Engine) --------------------------
elif page == "Strategy Backtester":
    st.header("📈 Strategy Backtester")
    st.caption("Modular pure-pandas engine (PR 3). Real OHLCV from CoinGecko/CCXT + sizing, stops, and simple optimization.")

    colA, colB, colC = st.columns(3)
    with colA:
        asset = st.selectbox("Asset (CoinGecko id)", ["bitcoin", "ethereum", "solana", "ripple"], index=0)
        days = st.slider("History (days)", 30, 365, 90, 30)
        source = st.radio("Data source", ["CoinGecko (easy)", "CCXT (exchange candles)"], horizontal=True)

    with colB:
        strat = st.selectbox("Strategy", list(bt_strategies.STRATEGY_REGISTRY.keys()))
        initial_cap = st.number_input("Initial Capital (USD)", 1000, 1000000, 10000, 1000)

    with colC:
        sizing = st.selectbox("Position Sizing", ["fixed", "percent", "vol_target"])
        sizing_param = st.slider("Sizing Param (units / % / vol target)", 0.1, 5.0, 1.0, 0.1)
        stop_loss_pct = st.slider("Stop Loss % (per bar, 0=off)", 0.0, 0.20, 0.0, 0.01)
        run_opt = st.checkbox("Run parameter optimization (small grid)", value=False)

    if st.button("Run Backtest"):
        with st.spinner("Fetching OHLCV and running enhanced backtest..."):
            if "CoinGecko" in source:
                ohlcv = get_coin_ohlc(asset, days=days)
            else:
                ohlcv = get_ccxt_ohlcv("binance", f"{asset.upper()}/USDT", "1d", limit=min(200, days))

            if ohlcv.empty:
                st.error("No OHLCV data returned.")
            else:
                if run_opt:
                    result = optimize_strategy(
                        ohlcv,
                        strategy=strat,
                        initial_cap=initial_cap,
                        sizing=sizing,
                        sizing_param=sizing_param,
                        stop_loss_pct=stop_loss_pct if stop_loss_pct > 0 else None,
                    )
                    if "error" in result:
                        st.error(result["error"])
                    else:
                        st.success(f"Best params: {result.get('best_params', result.get('params_used'))}")
                        res = result  # best result
                        # Show a small table of tried params
                        opt_df = pd.DataFrame(result.get("optimization_results", []))
                        if not opt_df.empty:
                            st.dataframe(opt_df, use_container_width=True)
                else:
                    res = run_backtest(
                        ohlcv,
                        strategy=strat,
                        initial_cap=initial_cap,
                        sizing=sizing,
                        sizing_param=sizing_param,
                        stop_loss_pct=stop_loss_pct if stop_loss_pct > 0 else None,
                    )

                if "error" in res:
                    st.error(res["error"])
                else:
                    m = res["metrics"]
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Final Equity", f"${m['final_equity']:,.0f}")
                    m2.metric("Total Return", f"{m['total_return_pct']:+.1f}%")
                    m3.metric("Sharpe (ann.)", f"{m['annualized_sharpe']:.2f}")
                    m4.metric("Max DD", f"{m['max_drawdown_pct']:.1f}%")

                    st.caption(
                        f"Win Rate: {m.get('win_rate_pct', 'n/a')}% | "
                        f"Profit Factor: {m.get('profit_factor', 'n/a')} | "
                        f"Buy&Hold: {res.get('bh_return', 'n/a')}%"
                    )

                    # Equity curve
                    fig = px.line(res["equity_df"], title="Equity Curve: Strategy vs Buy & Hold")
                    st.plotly_chart(fig, use_container_width=True)

                    # Show recent signals / equity
                    st.dataframe(res["full_df"][["close", "signal", "strategy_returns", "equity"]].tail(10).round(2), use_container_width=True)

                    # Save run - delegated to the engine (which does the soft PR 1 dance internally)
                    if st.button("Save this backtest run (soft PR1 persistence recommended)"):
                        try:
                            saved_path = save_run(
                                res,
                                extra={"asset": asset, "strategy": strat},
                            )
                            st.success(f"Run saved to {saved_path} (soft PR1 storage recommendation followed).")
                        except Exception as e:
                            st.warning(f"Could not save run: {e}")

                    # Optional quick viewer (also uses engine helper)
                    if st.checkbox("Show previously saved runs"):
                        try:
                            runs = load_runs()
                            if runs:
                                st.dataframe(pd.DataFrame(runs).tail(10), use_container_width=True)
                            else:
                                st.info("No saved runs yet.")
                        except Exception as e:
                            st.caption(f"Could not load runs: {e}")

    st.info("PR 3 + v3 Phase B: position sizing, stops, grid opt, multi-asset rebalance (run_multi_asset_backtest), walk-forward (walk_forward_backtest), richer history via persistence. Use the engine directly for advanced experiments.")


# -------------------------- ON-CHAIN & ETF --------------------------
elif page == "On-Chain & ETF":
    st.header("🔗 On-Chain & ETF Flows")
    st.caption("DeFiLlama (free) + PR2 ETF price proxies via yfinance. Full automation & on-chain wallet tracking in future PRs.")

    st.subheader("DeFiLlama — Top Chains by TVL")
    try:
        chains = cached_defi_chains()[:12]
        if chains:
            ch_df = pd.DataFrame(chains)[["name", "tvl", "tokenSymbol"]].head(12)
            ch_df["tvl"] = (ch_df["tvl"] / 1e9).round(2)
            ch_df.columns = ["Chain", "TVL (B)", "Token"]
            st.dataframe(ch_df, use_container_width=True, hide_index=True)
    except Exception as e:
        st.warning(f"Could not load chains: {e}")

    st.subheader("DeFiLlama — Top Protocols (TVL)")
    try:
        prots = cached_defi_protocols(12)
        if prots:
            p_df = pd.DataFrame(prots)[["name", "tvl", "change_1d", "change_7d", "category"]].copy()
            p_df["tvl"] = (p_df["tvl"] / 1e9).round(2)
            p_df["change_1d"] = p_df["change_1d"].round(1)
            p_df["change_7d"] = p_df["change_7d"].round(1)
            st.dataframe(p_df, use_container_width=True, hide_index=True)
    except Exception as e:
        st.warning(f"Protocols load issue: {e}")

    st.markdown("---")
    st.subheader("ETF Flows (v3 - yfinance proxy + real flows scaffolding)")
    try:
        from config import get_feature_flag
        use_real = get_feature_flag("REAL_ETF_FLOWS", False)
        etf_data = get_etf_summary(use_real_flows=use_real)
        st.json(etf_data)
        st.caption(
            "v3: yfinance price/volume proxy + real flows (lightweight public Farside-style scrape with UA/sleep when ENABLE_REAL_ETF_FLOWS=1). "
            "Graceful fallback + manual text area. See integrations/etf.py (per design Open Q #2)."
        )
    except Exception as e:
        st.warning(f"ETF module issue: {e}")
        # Fallback to old manual
        st.text_area("Paste daily ETF inflow/outflow numbers (BTC/ETH spot ETFs)", "Example:\n2026-06-06 | BTC Spot | +$187M | ETH Spot | -$42M")


# -------------------------- GROK AI CO-PILOT (PR 4 Hybrid Enhanced) --------------------------
elif page == "Grok AI Co-Pilot":
    st.header("🧠 Grok AI Co-Pilot")
    st.caption("The ultimate hybrid experience. Build rich context here, then use the main Grok chat's native X tools + full reasoning to generate super reports.")

    user_prompt = st.text_area(
        "Your question or thesis",
        "Is the current extreme fear setup + ETF outflow pattern historically bullish for BTC over the next 30 days? What are the key X narratives right now?",
        height=100,
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📤 Export Context for Grok (1-click)"):
            ctx = get_live_context()
            prompt = build_super_prompt(ctx, user_prompt)

            # Save snapshot for reproducibility (PR4)
            try:
                snap_path = save_context_snapshot(ctx, name=f"context_{datetime.now().strftime('%Y%m%d_%H%M')}")
                st.success(f"Context snapshot saved to {snap_path}")
            except Exception:
                pass

            st.subheader("Copy this full prompt into the main Grok chat:")
            st.code(prompt, language="markdown")

            # Also offer a context json download
            ctx_json = json.dumps(ctx, indent=2, default=str)
            st.download_button(
                "Download live_context.json",
                data=ctx_json,
                file_name=f"live_context_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json"
            )

    with col2:
        if st.button("🚀 Generate & Save Super Report Draft"):
            ctx = get_live_context()
            draft_path = generate_initial_report_draft(ctx, user_prompt)
            st.success(f"Initial draft saved to {draft_path}")
            st.info("Open the Reports tab to view it, or paste the prompt from the left button into the main chat for the full X-tool-powered analysis.")

    st.markdown("---")
    st.subheader("Saved Analyses (this session)")
    if "analyses" not in st.session_state:
        st.session_state.analyses = []
    if st.session_state.analyses:
        for i, a in enumerate(st.session_state.analyses[-5:]):
            st.markdown(f"**{i+1}.** {a[:180]}...")
    else:
        st.caption("Run analyses in the main chat (using the exported prompt + native X tools) → ask me to format them → paste here or save via the Reports tab.")


# -------------------------- REPORTS (PR 4 - Hybrid Super Reports) --------------------------
elif page == "Reports":
    st.header("📄 Automated Reports & Hybrid Super Intel")
    st.caption("1-click context export + prompt generation that leverages this environment's native X tools for god-tier reports. Auto-discovers saved .md files.")

    # 1-click Super Report (wired to generator)
    if st.button("🚀 1-Click Generate Super Report Draft + Prompt"):
        ctx = get_live_context()
        draft_path = generate_initial_report_draft(ctx)
        prompt = build_super_prompt(ctx)

        st.success(f"Draft saved: {draft_path}")
        st.subheader("Super Prompt (copy to main Grok chat and run with native X tools):")
        st.code(prompt, language="markdown")

        st.download_button(
            "Download the prompt as .txt",
            data=prompt,
            file_name=f"super_prompt_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
        )

    st.markdown("---")

    # Saved Reports browser (auto-discover)
    st.subheader("Saved Reports (auto-discovered from reports/*.md)")
    report_files = sorted(glob.glob("reports/*.md"), reverse=True)

    if report_files:
        for rf in report_files[:10]:  # limit display
            name = Path(rf).name
            with st.expander(f"📄 {name}", expanded=False):
                try:
                    content = Path(rf).read_text(encoding="utf-8")
                    st.markdown(content[:8000] + ("\n\n...(truncated for preview)" if len(content) > 8000 else ""))
                    with open(rf, "rb") as f:
                        st.download_button(
                            f"Download {name}",
                            data=f,
                            file_name=name,
                            mime="text/markdown",
                            key=f"dl_{name}"
                        )
                except Exception as e:
                    st.error(f"Could not read {name}: {e}")
    else:
        st.info("No saved reports yet. Use the 1-Click button above (or the Co-Pilot tab) to generate drafts.")

    # v3 Phase B: Report iteration / refinement (richer hybrid)
    if report_files:
        selected = st.selectbox("Load a report for refinement (Phase B)", [""] + [Path(f).name for f in report_files[:5]])
        if selected:
            try:
                content = Path(f"reports/{selected}").read_text(encoding="utf-8")
                st.caption("Loaded report preview (first 1500 chars):")
                st.text(content[:1500] + "...")
                refine_prompt = f"Refine and improve this crypto report using latest X tools and current market data. Original:\n\n{content[:2000]}"
                if st.button(f"Send refinement prompt for {selected} to Co-Pilot / main chat"):
                    st.code(refine_prompt)
                    st.info("Copy the above into the main Grok chat (with native X tools) or the Co-Pilot tab for iterative improvement. Then save the result back to reports/.")
            except Exception as e:
                st.warning(f"Could not load {selected} for refinement: {e}")

    st.markdown("---")

    # Legacy / manual template generator (kept for convenience)
    with st.expander("Legacy: Simple Template Generator"):
        report_type = st.selectbox("Report type", ["Daily Market Brief", "X Narrative Deep Dive", "Portfolio Risk Review", "Backtest Post-Mortem"])
        if st.button("Generate Basic Template"):
            template = f"""# {report_type} — {pd.Timestamp.now().date()}

## Market Snapshot
- Total Cap: ...
- F&G: ...
- BTC Dom: ...

## Key Narratives (X + Research)
...

## Actionable Insights
...

## Risks
...
"""
            st.code(template, language="markdown")
            st.download_button("Download .md", template, file_name=f"{report_type.lower().replace(' ', '_')}.md")


# -------------------------- Footer / Status --------------------------
st.markdown("---")
st.caption("Built to be super. Data cached for speed & politeness to free APIs. Add your own keys in future versions for higher rate limits / premium sources.")
st.caption("Run with: `pip install -r requirements.txt && streamlit run app.py`")
