"""
ui package (v3 Phase B)

Theming and reusable components extracted from the monolithic app.py.
Enables easy theming and health/observability widgets.
"""

from .themes import apply_crypto_theme
from .components import fng_gauge, health_sidebar, render_portfolio_table, render_backtest_results

__all__ = [
    "apply_crypto_theme",
    "fng_gauge",
    "health_sidebar",
    "render_portfolio_table",
    "render_backtest_results",
]
