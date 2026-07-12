"""Reference Connector implementations backed by the committed mock CSVs.

These prove the seam: the same protocol a real platform connector implements,
satisfied by the synthetic dataset. Useful for tests, demos, and as the
template for writing a new connector.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from .base import Connector, register

MOCK_DIR = Path(__file__).resolve().parents[3] / "data" / "mock_marketing"


class _CSVMockConnector(Connector):
    """Reads the committed mock CSV for target_table, filtered to the window."""

    def extract(self, start: date, end: date) -> pd.DataFrame:
        path = MOCK_DIR / f"{self.target_table}.csv"
        df = pd.read_csv(path)
        d = pd.to_datetime(df[self.date_column]).dt.date
        return self.validate_frame(df[(d >= start) & (d <= end)].reset_index(drop=True))


@register
class GA4MockConnector(_CSVMockConnector):
    name = "ga4-mock"
    target_table = "ga4_daily_sessions"
    schema = ["date", "channel_group", "device_category", "sessions",
              "engaged_sessions", "bounce_rate", "avg_session_duration_sec",
              "pages_per_session", "new_users", "conversions", "revenue",
              "conversion_rate"]


@register
class GoogleAdsMockConnector(_CSVMockConnector):
    name = "google-ads-mock"
    target_table = "google_ads_daily_performance"
    # Spend field is `cost` for Google Ads (CLAUDE.md §7) — encoded here, not prose.
    schema = ["date", "campaign_id", "campaign_name", "campaign_type",
              "impressions", "clicks", "cost", "conversions", "conversion_value",
              "ctr", "avg_cpc", "cost_per_conversion", "roas"]


@register
class MetaAdsMockConnector(_CSVMockConnector):
    name = "meta-ads-mock"
    target_table = "meta_ads_daily_performance"
    # Spend field is `spend` for Meta (CLAUDE.md §7); revenue is `purchase_value`.
    schema = ["date", "campaign_id", "campaign_name", "objective",
              "impressions", "reach", "spend", "link_clicks", "ctr", "cpc",
              "cpm", "purchases", "purchase_value", "cost_per_purchase", "roas"]
