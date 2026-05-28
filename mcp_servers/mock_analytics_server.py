"""
mock_analytics_server.py
────────────────────────────────────────────────────────────────────────────
Analytics MCP server — golden layer with arbitrary date windows.

Exposes three tools to Claude:

  query_metrics(start_date, end_date)
      Query any date range. Uses query_window.py (same logic as the golden
      layer) and returns the full aggregated metric schema.

  get_precomputed_window(window)
      Fast path for pre-computed windows. Reads directly from
      golden_metrics.json without re-querying the CSV files.
      Pass window="list" to see available keys.

  get_meta()
      Return golden_metrics.json _meta (anchor date, generated_at, schema).

Rationale:
    The raw MCP servers (ga4, google_ads, meta_ads, hubspot, salesforce)
    return platform-level rows — Claude must aggregate and join them.
    This server returns pre-aggregated metrics with the same validated
    formulas as the dbt golden layer, for any date range, via a single call.

    CRM data (HubSpot contacts, Salesforce) is always all-time regardless
    of the date range passed — it is a lifetime count.
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import fastmcp

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from query_window import query_window  # noqa: E402

GOLDEN_PATH = PROJECT_ROOT / "dashboards" / "golden_metrics.json"

mcp = fastmcp.FastMCP("analytics")


@mcp.tool()
def query_metrics(start_date: str, end_date: str, label: str = "") -> dict:
    """
    Query aggregated marketing analytics for any date range.

    Returns the same schema as a golden_metrics.json section:
    sessions, spend, conversions, blended_roas, channel_performance,
    attribution_by_channel, ga4_by_channel, campaigns, crm.

    CRM data is always all-time regardless of date range.

    Args:
        start_date: Window start in YYYY-MM-DD format.
        end_date:   Window end in YYYY-MM-DD format.
        label:      Optional display label (shown in the window metadata).
    """
    start = date.fromisoformat(start_date)
    end   = date.fromisoformat(end_date)
    return query_window(start, end, label or f"{start_date} → {end_date}")


@mcp.tool()
def get_precomputed_window(window: str) -> dict:
    """
    Return a pre-computed metric section from golden_metrics.json.

    Fast path for common windows — no re-query needed. The golden is
    regenerated daily so values always reflect the latest appended data.

    Args:
        window: One of the available window keys, e.g.:
                "windowed_90d", "windowed_30d", "windowed_7d",
                "windowed_60d", "windowed_180d", "all_time",
                or a monthly key like "month_2026_03".
                Pass "list" to see all available keys and the current anchor.
    """
    if not GOLDEN_PATH.exists():
        return {
            "error": "golden_metrics.json not found.",
            "fix": "Run: python scripts/generate_golden_metrics.py",
        }

    golden = json.loads(GOLDEN_PATH.read_text())

    if window == "list":
        meta = golden.get("_meta", {})
        return {
            "available_windows": list(meta.get("available_windows", {}).keys()),
            "anchor_date": meta.get("anchor_date"),
            "window_start": meta.get("window_start"),
            "window_end": meta.get("window_end"),
            "generated_at": meta.get("generated_at"),
        }

    if window not in golden:
        available = [k for k in golden if not k.startswith("_")]
        return {"error": f"Window '{window}' not found. Available: {available}"}

    section = dict(golden[window])
    section["_source"] = "golden_metrics.json"
    section["_window_key"] = window
    return section


@mcp.tool()
def get_meta() -> dict:
    """
    Return golden_metrics.json metadata.

    Includes: anchor_date, window_start, window_end, generated_at,
    schema_version, available_windows, and dataset_start/end.
    Use this to check data freshness before building a dashboard.
    """
    if not GOLDEN_PATH.exists():
        return {"error": "golden_metrics.json not found"}
    return json.loads(GOLDEN_PATH.read_text()).get("_meta", {})


if __name__ == "__main__":
    mcp.run()
