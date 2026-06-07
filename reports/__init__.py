"""
reports package - Super Reports and Hybrid Grok Integration (PR 4)

Provides prompt builders and report generators that embed live dashboard data
and explicitly direct the use of the host Grok environment's native tools (X search, etc.)
for the ultimate "super" analysis experience.
"""
from .generator import build_super_prompt, get_live_context, generate_initial_report_draft

__all__ = ["build_super_prompt", "get_live_context", "generate_initial_report_draft"]
