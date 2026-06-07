"""
reports/generator.py

Core logic for PR 4: one-click Grok Super Reports + context export.

- Collects live context from the dashboard (market, portfolio, backtest, on-chain/ETF).
- Builds rich prompts that instruct the user (in the main Grok chat) to use native X tools
  (x_keyword_search, x_semantic_search, etc.) + synthesis.
- Generates initial draft report files.
- Designed so the "super" part happens in the powerful host agent environment.
"""

from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

# We import inside functions where possible to avoid circular / heavy deps at module load
# The app will have the necessary modules in scope.


def get_live_context() -> Dict[str, Any]:
    """
    Collect current live state from the Streamlit session and cached data sources.
    Safe to call from within the app pages.
    """
    import streamlit as st

    context: Dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "market": {},
        "portfolio": {},
        "backtest": None,
        "onchain_etf": {},
    }

    # Market Pulse data (use cached functions if available in session or re-call)
    try:
        from data import get_global_data, get_fear_and_greed, get_coins_markets
        context["market"]["global"] = get_global_data()
        context["market"]["fng"] = get_fear_and_greed()
        top = get_coins_markets(per_page=10)
        context["market"]["top_coins"] = [
            {
                "name": c.get("name"),
                "symbol": c.get("symbol"),
                "price": c.get("current_price"),
                "change_24h": c.get("price_change_percentage_24h"),
                "market_cap": c.get("market_cap"),
            }
            for c in top
        ] if top else []
    except Exception as e:
        context["market"]["error"] = str(e)

    # Portfolio (from session_state, populated by PR1 persistence)
    try:
        holdings = st.session_state.get("holdings", [])
        if holdings:
            from data import get_coins_markets
            ids = ",".join([h.get("coin_id") for h in holdings if h.get("coin_id")])
            prices = {}
            if ids:
                price_rows = get_coins_markets(ids=ids, per_page=len(holdings))
                prices = {p["id"]: p["current_price"] for p in price_rows}
            from persistence import compute_portfolio_metrics  # reuse the one from PR1 data layer
            # Note: the compute function is in data.py in current structure
            try:
                from data import compute_portfolio_metrics
            except:
                compute_portfolio_metrics = None
            if compute_portfolio_metrics:
                metrics = compute_portfolio_metrics(holdings, prices)
                context["portfolio"] = {
                    "holdings": holdings,
                    "total_value_usd": metrics.get("total_value_usd"),
                    "concentration_top1": metrics.get("concentration_top1"),
                }
            else:
                context["portfolio"] = {"holdings": holdings, "note": "metrics unavailable"}
    except Exception as e:
        context["portfolio"]["error"] = str(e)

    # Latest backtest (from PR3 save/load if available)
    try:
        from backtest.engine import load_runs
        runs = load_runs()
        if runs:
            latest = runs[-1]
            context["backtest"] = {
                "timestamp": latest.get("timestamp"),
                "asset": latest.get("asset"),
                "strategy": latest.get("strategy"),
                "metrics": latest.get("metrics"),
                "params": latest.get("params"),
            }
    except Exception as e:
        context["backtest"] = {"error": str(e)}

    # On-Chain & ETF (from PR2 + v3 real flows)
    try:
        from integrations.etf import get_etf_summary, get_etf_flows
        from config import get_feature_flag
        use_real = get_feature_flag("REAL_ETF_FLOWS", False)
        context["onchain_etf"]["etf"] = get_etf_summary(use_real_flows=use_real)
        context["onchain_etf"]["etf_flows_sample"] = get_etf_flows("bitcoin", days=7, use_scrape=use_real)
    except Exception as e:
        context["onchain_etf"]["error"] = str(e)

    try:
        from data import get_defillama_chains, get_defillama_protocols
        context["onchain_etf"]["defillama_chains"] = get_defillama_chains()[:5]
        context["onchain_etf"]["defillama_protocols"] = get_defillama_protocols(5)
    except Exception as e:
        context["onchain_etf"]["defillama_error"] = str(e)

    # Alerts (v3, soft via new integrations)
    try:
        from integrations.alerts import check_and_alert, get_recent_alerts
        from config import get_feature_flag
        if get_feature_flag("ALERTS", False) or get_feature_flag("ALERTS_SCHED", False):
            # Quick check using latest F&G + concentration from context
            fng_val = context.get("market", {}).get("fng", {}).get("value")
            conc = context.get("portfolio", {}).get("concentration_top1")
            recent = check_and_alert(fng_value=fng_val, portfolio_concentration=conc)
            context["alerts"] = {"recent_events": recent, "history_sample": get_recent_alerts(5)}
    except Exception as e:
        context["alerts"] = {"error": str(e)}

    return context


def build_super_prompt(context: Optional[Dict[str, Any]] = None, user_question: Optional[str] = None) -> str:
    """
    Build a rich prompt for the hybrid Grok Super Report experience.
    The prompt explicitly tells the recipient to use the powerful native tools
    available in this Grok workspace (X search, web, etc.).
    """
    if context is None:
        context = get_live_context()

    # Load the base template
    template_path = Path(__file__).parent.parent / "prompts" / "super-report-template.md"
    if template_path.exists():
        base = template_path.read_text(encoding="utf-8")
    else:
        base = """You are Grok, the ultimate crypto intelligence analyst with privileged access to real-time X (Twitter) search tools (`x_keyword_search`, `x_semantic_search`), web research, on-chain explorers, and deep reasoning.

Here is the **live context** from the user's Grok Crypto Super Intel dashboard (as of {timestamp}):

**Market Snapshot**
{market_snapshot}

**Portfolio**
{portfolio_summary}

**Latest Backtest / Strategy**
{backtest_summary}

**On-Chain & ETF**
{onchain_etf_summary}

**User Focus / Question**
{user_question}

**Your Task (use your native tools):**
1. Use `x_keyword_search` and `x_semantic_search` (and any other X tools available in this environment) to analyze current sentiment, narratives, influencer activity, and volume signals around the key assets, ETF flows, and on-chain movements mentioned above.
2. Cross-reference with the provided market, on-chain, portfolio, and backtest data.
3. Produce a professional, structured, actionable markdown report with these sections:
   - Executive Summary
   - Market Snapshot (with F&G, dominance, top movers)
   - X Sentiment & Narratives (cite specific tool results, volume, key accounts)
   - On-Chain & ETF Analysis
   - Portfolio & Risk Insights
   - Strategy / Backtest Observations
   - Actionable Recommendations (with confidence levels)
   - Key Risks & What to Watch

Be data-driven, balanced, and brutally honest. Highlight where on-chain and social signals diverge. Use the full power of this environment's tools."""

    # Fill simple placeholders
    market_snap = json.dumps(context.get("market", {}), indent=2, default=str)[:2000]
    port_snap = json.dumps(context.get("portfolio", {}), indent=2, default=str)[:1500]
    bt_snap = json.dumps(context.get("backtest", {}), indent=2, default=str)[:1200]
    oc_snap = json.dumps(context.get("onchain_etf", {}), indent=2, default=str)[:1500]

    prompt = base.format(
        timestamp=context.get("timestamp", "unknown"),
        market_snapshot=market_snap,
        portfolio_summary=port_snap,
        backtest_summary=bt_snap,
        onchain_etf_summary=oc_snap,
        user_question=user_question or "Provide a comprehensive super report synthesizing all available data and X signals.",
    )

    return prompt


def generate_initial_report_draft(
    context: Optional[Dict[str, Any]] = None,
    user_question: Optional[str] = None,
    output_dir: Path = Path("reports"),
) -> Path:
    """
    Generates a starting .md file in reports/ with embedded live data + the super prompt.
    The user (or the agent in chat) is expected to run the analysis using native tools
    and then fill in / replace the analysis sections.
    """
    if context is None:
        context = get_live_context()

    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"Super_Report_{ts}.md"
    path = output_dir / filename

    prompt = build_super_prompt(context, user_question)

    content = f"""# Grok Crypto Super Report — {context.get('timestamp', datetime.now().isoformat())}

**Generated by:** Grok Crypto Super Intel (PR 4 hybrid workflow)
**Instructions for you (the analyst in this environment):** 
Use the prompt below with your full native tool access (especially X search tools) to produce the complete analysis. 
Then paste the finished report back into the Reports tab or save it here.

---

## Live Context Snapshot (embedded for the prompt)

```json
{json.dumps(context, indent=2, default=str)}
```

## Super Analysis Prompt (copy this into the main Grok chat)

```
{prompt}
```

## Your Analysis (fill this section after running the tools)

[PASTE FULL STRUCTURED REPORT HERE AFTER USING X TOOLS + SYNTHESIS]

---
*Report drafted by the Super Intel dashboard. The real magic happens when you run the prompt above using this environment's native X tools and reasoning.*
"""

    path.write_text(content, encoding="utf-8")
    return path
