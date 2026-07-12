"""Contract tests for the Connector protocol, the CSV reference connectors,
and the GA4 API-response mapping (no network or credentials required)."""

import sys
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from fullfunnel.connectors import ConnectorConfigError, available, get_connector  # noqa: E402
from fullfunnel.connectors import ga4  # noqa: E402


def test_registry_lists_real_and_mock():
    names = available()
    assert "ga4" in names
    assert "ga4-mock" in names and "google-ads-mock" in names and "meta-ads-mock" in names


def test_unknown_connector_is_guided():
    with pytest.raises(KeyError, match="Available"):
        get_connector("hubspot")


@pytest.mark.skipif(
    not (Path(__file__).parent.parent / "data" / "mock_marketing" / "ga4_daily_sessions.csv").exists(),
    reason="mock CSVs not present")
def test_csv_mock_roundtrip_matches_schema_and_window():
    conn = get_connector("ga4-mock")
    df = conn.extract(date(2026, 3, 1), date(2026, 3, 7))
    assert list(df.columns) == conn.schema
    assert not df.empty
    import pandas as pd
    d = pd.to_datetime(df["date"]).dt.date
    assert d.min() >= date(2026, 3, 1) and d.max() <= date(2026, 3, 7)


def _fake_row(dims, mets):
    return SimpleNamespace(
        dimension_values=[SimpleNamespace(value=v) for v in dims],
        metric_values=[SimpleNamespace(value=str(v)) for v in mets],
    )


def test_ga4_mapping_produces_staging_schema():
    rows = [
        # date, channel display name, device / sessions, engaged, bounce(0-1),
        # avg dur, pages/sess, new users, key events, revenue
        _fake_row(["20260701", "Organic Search", "MOBILE"],
                  [1000, 600, 0.45, 182.4, 3.21, 700, 25, 2512.5]),
        _fake_row(["20260701", "Cross-network", "desktop"],
                  [10, 4, 0.5, 60.0, 1.0, 8, 0, 0]),
    ]
    df = ga4.report_rows_to_frame(rows)
    conn = get_connector("ga4")
    assert list(conn.validate_frame(df).columns) == conn.schema

    first = df.iloc[0]
    assert first["date"] == "2026-07-01"
    assert first["channel_group"] == "organic_search"
    assert first["device_category"] == "mobile"
    assert first["bounce_rate"] == 45.0          # fraction → percent
    assert first["conversion_rate"] == 2.5       # 25 / 1000 * 100
    assert first["revenue"] == 2512.5

    # Unknown channel groups are slugified, never dropped
    assert df.iloc[1]["channel_group"] == "cross_network"
    # Zero sessions must not divide by zero
    assert ga4.report_rows_to_frame(
        [_fake_row(["20260701", "Direct", "tablet"], [0, 0, 0, 0, 0, 0, 0, 0])]
    ).iloc[0]["conversion_rate"] == 0.0


def test_ga4_requires_configuration(monkeypatch):
    monkeypatch.delenv("GA4_PROPERTY_ID", raising=False)
    with pytest.raises(ConnectorConfigError, match="GA4_PROPERTY_ID"):
        get_connector("ga4").extract(date(2026, 1, 1), date(2026, 1, 31))
