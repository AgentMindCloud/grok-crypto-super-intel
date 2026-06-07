"""
ui/components.py - Reusable widgets (v3 Phase B)

Extracted/refactored common UI pieces from app.py for cleanliness and theming.
Includes the original fng_gauge + new health/observability sidebar.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Any, Dict, List, Optional


def fng_gauge(value: int, classification: str):
    """Fear & Greed gauge (extracted from original app.py)."""
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


def health_sidebar(
    last_fetches: Optional[Dict[str, str]] = None,
    call_counts: Optional[Dict[str, int]] = None,
    rate_headroom: Optional[str] = None,
    alerts_count: int = 0,
):
    """Simple observability / health panel for sidebar or expander (Phase B)."""
    with st.sidebar.expander("📡 Health & Observability (v3)", expanded=False):
        if last_fetches:
            st.markdown("**Last successful fetches**")
            for source, ts in last_fetches.items():
                st.caption(f"{source}: {ts}")
        else:
            st.caption("Last fetches: (enable ENABLE_OBSERVABILITY for live data)")

        if call_counts:
            st.markdown("**Call counts (this session)**")
            for source, cnt in call_counts.items():
                st.caption(f"{source}: {cnt}")

        if rate_headroom:
            st.caption(f"Rate headroom: {rate_headroom}")

        if alerts_count > 0:
            st.warning(f"Active alerts: {alerts_count} (see Market Pulse or Reports)")

        st.caption("Data is cached. New features behind ENABLE_OBSERVABILITY flag.")


def render_portfolio_table(holdings_df: pd.DataFrame):
    """Reusable portfolio table renderer."""
    if holdings_df.empty:
        st.info("No holdings.")
        return
    st.dataframe(holdings_df, use_container_width=True, hide_index=True)


def render_backtest_results(result: Dict[str, Any]):
    """Reusable backtest results renderer (metrics + curve + table)."""
    if "error" in result:
        st.error(result["error"])
        return

    m = result.get("metrics", {})
    cols = st.columns(4)
    cols[0].metric("Final Equity", f"${m.get('final_equity', 0):,.0f}")
    cols[1].metric("Total Return", f"{m.get('total_return_pct', 0):+.1f}%")
    cols[2].metric("Sharpe (ann.)", f"{m.get('annualized_sharpe', 0):.2f}")
    cols[3].metric("Max DD", f"{m.get('max_drawdown_pct', 0):.1f}%")

    if "equity_df" in result:
        import plotly.express as px
        fig = px.line(result["equity_df"], title="Equity Curve")
        st.plotly_chart(fig, use_container_width=True)

    if "full_df" in result:
        st.dataframe(
            result["full_df"][["close", "signal", "strategy_returns", "equity"]].tail(10).round(2),
            use_container_width=True,
        )
