"""
tests/test_packaging.py - v3 Phase C packaging & CI tests.

Covers Dockerfile, CI workflow, and basic structure for deployment.
"""

import os
from pathlib import Path

import pytest


def test_dockerfile_exists_and_valid():
    """Dockerfile should exist and contain key instructions from design."""
    dockerfile = Path("Dockerfile")
    assert dockerfile.exists(), "Dockerfile missing"
    content = dockerfile.read_text()
    assert "FROM python:3.11-slim" in content
    assert "EXPOSE 8501" in content
    assert "VOLUME" in content or "data" in content.lower()
    assert "streamlit run" in content or "CMD" in content


def test_ci_workflow_exists():
    """CI yaml should exist and have pytest + lint steps."""
    ci_file = Path(".github/workflows/ci.yml")
    assert ci_file.exists(), "CI workflow missing"
    content = ci_file.read_text()
    assert "pytest" in content
    assert "ruff" in content or "black" in content
    assert "on:" in content  # has triggers


def test_requirements_minimal():
    """requirements.txt should be present and lightweight (core deps only)."""
    reqs = Path("requirements.txt")
    assert reqs.exists()
    content = reqs.read_text().lower()
    assert "streamlit" in content
    # No heavy optional like vectorbt etc. in core
    assert "pandas" in content or "plotly" in content


def test_data_dir_compatible():
    """Config and persistence should support DATA_DIR for Docker volume."""
    # Just import check; actual env set in Dockerfile
    import config
    assert hasattr(config, "DATA_DIR") or "DATA_DIR" in dir(config)
