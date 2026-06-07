"""
tests/test_reports.py - Skeleton for PR 4 reports / hybrid generator.
"""

import pytest
from pathlib import Path
import tempfile

from reports.generator import get_live_context, build_super_prompt, generate_initial_report_draft


def test_get_live_context_returns_dict():
    ctx = get_live_context()
    assert isinstance(ctx, dict)
    assert "timestamp" in ctx
    assert "market" in ctx or "error" in ctx  # graceful


def test_build_super_prompt_contains_instructions():
    ctx = {"timestamp": "test", "market": {}, "portfolio": {}, "backtest": None, "onchain_etf": {}}
    prompt = build_super_prompt(ctx, "Test thesis")
    assert "Use your native X tools" in prompt or "x_keyword_search" in prompt
    assert "Grok" in prompt
    assert "Test thesis" in prompt


def test_generate_initial_report_draft_creates_file(tmp_path):
    # Use a temp reports dir
    old_cwd = Path.cwd()
    try:
        import os
        os.chdir(tmp_path)
        (tmp_path / "reports").mkdir()
        ctx = {"timestamp": "test", "market": {}, "portfolio": {}, "backtest": None, "onchain_etf": {}}
        path = generate_initial_report_draft(ctx, output_dir=tmp_path / "reports")
        assert path.exists()
        content = path.read_text()
        assert "Super Report" in content
        assert "Live Context Snapshot" in content
    finally:
        os.chdir(old_cwd)
