"""Shared fixtures for the test suite."""

import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
GOLDEN_PATH = PROJECT_ROOT / "dashboards" / "golden_metrics.json"


@pytest.fixture(scope="session")
def golden() -> dict:
    """Load golden_metrics.json once for the whole test session."""
    if not GOLDEN_PATH.exists():
        pytest.skip("golden_metrics.json not found — run: python scripts/generate_golden_metrics.py")
    return json.loads(GOLDEN_PATH.read_text())


@pytest.fixture(scope="session")
def golden_90d(golden) -> dict:
    return golden["windowed_90d"]


@pytest.fixture(scope="session")
def golden_at(golden) -> dict:
    return golden["all_time"]
