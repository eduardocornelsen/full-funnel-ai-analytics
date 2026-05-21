"""
Tests for the FastAPI lead scoring endpoint.
Requires the lead scoring model file: ml/lead_scoring_model.json
"""

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
MODEL_PATH = PROJECT_ROOT / "ml" / "lead_scoring_model.json"


@pytest.fixture(scope="module")
def client():
    if not MODEL_PATH.exists():
        pytest.skip("ml/lead_scoring_model.json not found — run: python ml/src/train.py")
    from fastapi.testclient import TestClient
    import sys
    sys.path.insert(0, str(PROJECT_ROOT / "api"))
    from main import app  # noqa: PLC0415
    return TestClient(app)


def test_score_valid_payload(client):
    response = client.post("/score", json={
        "sessions": 5,
        "engaged_sessions": 3,
        "page_views": 10,
        "country": "BR",
        "channel": "paid_search",
        "is_first_visit": False,
    })
    assert response.status_code == 200
    data = response.json()
    assert "score" in data
    assert "lead_tier" in data
    assert 0.0 <= data["score"] <= 1.0
    assert data["lead_tier"] in ("A", "B", "C")


def test_score_first_visit(client):
    response = client.post("/score", json={
        "sessions": 1,
        "engaged_sessions": 0,
        "page_views": 1,
        "country": "US",
        "channel": "organic_search",
        "is_first_visit": True,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["lead_tier"] in ("A", "B", "C")


def test_score_missing_required_field(client):
    response = client.post("/score", json={
        "sessions": 5,
        # missing engaged_sessions, page_views, etc.
    })
    assert response.status_code == 422  # FastAPI validation error


def test_score_zero_sessions(client):
    response = client.post("/score", json={
        "sessions": 0,
        "engaged_sessions": 0,
        "page_views": 0,
        "country": "BR",
        "channel": "direct",
        "is_first_visit": True,
    })
    assert response.status_code == 200
    data = response.json()
    assert 0.0 <= data["score"] <= 1.0
