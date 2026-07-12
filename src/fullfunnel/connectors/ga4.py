"""Real GA4 connector — Google Analytics Data API v1 → ga4_daily_sessions schema.

The first genuine platform connector: proves the seam carries real data.

Setup (free tier is sufficient):
  1. pip install -e ".[ga4]"
  2. GCP service account with the Analytics Data API enabled; grant it Viewer
     on the GA4 property; download the key JSON.
  3. export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
     export GA4_PROPERTY_ID=123456789
  4. fullfunnel ingest --connector ga4 --last-days 90 --dry-run

Design notes:
- The API response → staging-schema mapping is a PURE function
  (`report_rows_to_frame`) so it is unit-tested against fake responses —
  no credentials or network needed in CI.
- GA4 channel groups arrive as display names ("Organic Search"); the project's
  staging schema uses snake_case keys. The mapping is explicit and total:
  unknown groups are slugified rather than dropped, so no traffic silently
  disappears.
- `conversions` uses GA4 key events (the post-UA name for conversions).
"""

from __future__ import annotations

import os
import re
from datetime import date

import pandas as pd

from .base import Connector, ConnectorConfigError, register

# GA4 display name → project channel_group key (matches stg_ga4_sessions values)
CHANNEL_MAP = {
    "Organic Search": "organic_search",
    "Paid Search":    "paid_search",
    "Paid Social":    "paid_social",
    "Organic Social": "organic_social",
    "Direct":         "direct",
    "Email":          "email",
    "Referral":       "referral",
}

# (GA4 metric api_name, staging column) — order defines the request
METRICS = [
    ("sessions",                 "sessions"),
    ("engagedSessions",          "engaged_sessions"),
    ("bounceRate",               "bounce_rate"),
    ("averageSessionDuration",   "avg_session_duration_sec"),
    ("screenPageViewsPerSession", "pages_per_session"),
    ("newUsers",                 "new_users"),
    ("keyEvents",                "conversions"),
    ("totalRevenue",             "revenue"),
]

DIMENSIONS = ["date", "sessionDefaultChannelGroup", "deviceCategory"]


def normalise_channel(display_name: str) -> str:
    if display_name in CHANNEL_MAP:
        return CHANNEL_MAP[display_name]
    return re.sub(r"[^a-z0-9]+", "_", display_name.strip().lower()).strip("_") or "unassigned"


def report_rows_to_frame(rows) -> pd.DataFrame:
    """Map GA4 RunReport rows to the ga4_daily_sessions staging schema.

    `rows` is any iterable of objects with .dimension_values / .metric_values
    (each having .value) — the real API rows, or fakes in tests.
    """
    records = []
    for row in rows:
        dims = [dv.value for dv in row.dimension_values]
        mets = [mv.value for mv in row.metric_values]
        raw_date, channel, device = dims
        vals = {col: float(v or 0) for (_, col), v in zip(METRICS, mets)}
        sessions = vals["sessions"]
        records.append({
            "date":                     f"{raw_date[0:4]}-{raw_date[4:6]}-{raw_date[6:8]}",
            "channel_group":            normalise_channel(channel),
            "device_category":          device.lower(),
            "sessions":                 int(sessions),
            "engaged_sessions":         int(vals["engaged_sessions"]),
            # GA4 returns bounceRate as a 0-1 fraction; staging stores percent.
            "bounce_rate":              round(vals["bounce_rate"] * 100, 1),
            "avg_session_duration_sec": round(vals["avg_session_duration_sec"], 0),
            "pages_per_session":        round(vals["pages_per_session"], 1),
            "new_users":                int(vals["new_users"]),
            "conversions":              int(vals["conversions"]),
            "revenue":                  round(vals["revenue"], 2),
            "conversion_rate":          round(vals["conversions"] / sessions * 100, 2) if sessions else 0.0,
        })
    return pd.DataFrame.from_records(records)


@register
class GA4Connector(Connector):
    name = "ga4"
    target_table = "ga4_daily_sessions"
    schema = ["date", "channel_group", "device_category", "sessions",
              "engaged_sessions", "bounce_rate", "avg_session_duration_sec",
              "pages_per_session", "new_users", "conversions", "revenue",
              "conversion_rate"]

    def extract(self, start: date, end: date) -> pd.DataFrame:
        property_id = os.environ.get("GA4_PROPERTY_ID", "")
        if not property_id:
            raise ConnectorConfigError(
                "GA4_PROPERTY_ID is not set. Export your GA4 property id "
                "(Admin → Property settings) and GOOGLE_APPLICATION_CREDENTIALS "
                "pointing at a service-account key with Analytics Data API access."
            )
        try:
            from google.analytics.data_v1beta import BetaAnalyticsDataClient
            from google.analytics.data_v1beta.types import (
                DateRange, Dimension, Metric, RunReportRequest)
        except ImportError as e:
            raise ConnectorConfigError(
                "google-analytics-data is not installed. Run: pip install -e '.[ga4]'"
            ) from e

        client = BetaAnalyticsDataClient()
        request = RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=[Dimension(name=d) for d in DIMENSIONS],
            metrics=[Metric(name=api_name) for api_name, _ in METRICS],
            date_ranges=[DateRange(start_date=start.isoformat(), end_date=end.isoformat())],
            limit=250000,
        )
        response = client.run_report(request)
        df = report_rows_to_frame(response.rows)
        if df.empty:
            # A real but empty property is valid; return an empty frame WITH schema
            df = pd.DataFrame(columns=self.schema)
        return self.validate_frame(df.sort_values(["date", "channel_group", "device_category"])
                                     .reset_index(drop=True) if not df.empty else df)
