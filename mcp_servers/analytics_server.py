"""
analytics_server.py
────────────────────────────────────────────────────────────────────────────
The GOVERNED analytics MCP server — the primary data interface for AI agents.

Unlike the platform mocks (ga4, google-ads, …), which return raw rows the
agent must aggregate itself, this server returns governed metrics from the
golden layer with the governance metadata attached to every number:

  list_metrics()                     what exists, and which windows are available
  get_metric(metric, window)        one governed value + full metadata envelope
  explain_metric(metric)            formula, scope, and warnings from metrics.yml
  get_funnel(window)                funnel steps with SERVER-SIDE ordering validation
  compare_windows(metric, a, b)     two windows of one metric, safely labelled

  query_metrics(start, end)         escape hatch: any date range (ad-hoc, labelled)
  get_precomputed_window(window)    full raw section from golden_metrics.json
  get_meta()                        artifact freshness / schema metadata

Design principle — guardrails as tool contract, not prompt:
  every numeric response carries {value, formula, scope_label, window, source},
  so a consumer cannot obtain an unlabelled or unscoped number from this
  server. Formulas and descriptions are read from the dbt semantic layer
  (metrics.yml) — the single source of metric truth — never duplicated here.

CRM data (HubSpot contacts, Salesforce) is always all-time regardless of any
window — it is a lifetime count and is deliberately NOT a funnel step (§5).
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import fastmcp
import yaml

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from query_window import query_window  # noqa: E402

GOLDEN_PATH  = PROJECT_ROOT / "dashboards" / "golden_metrics.json"
METRICS_YML  = PROJECT_ROOT / "dbt_project" / "models" / "metrics" / "metrics.yml"

mcp = fastmcp.FastMCP("analytics")


# ── Metric registry ───────────────────────────────────────────────────────────
# Maps agent-facing metric ids to their location in a golden section and their
# governance metadata (CLAUDE.md §1/§2). `yaml_name` links to the governed
# definition in metrics.yml, from which formula/description are read.

METRIC_REGISTRY: dict[str, dict] = {
    "total_spend": {
        "extract": lambda s: s["spend"]["total"],
        "label": "Total Paid Spend", "unit": "USD",
        "scope_label": "Google Ads + Meta Ads paid spend",
        "yaml_name": "total_spend",
    },
    "google_spend": {
        "extract": lambda s: s["spend"]["google"],
        "label": "Google Ads Spend", "unit": "USD",
        "scope_label": "Google Ads only (`cost` field)",
        "yaml_name": None,
        "formula": "SUM(cost) from Google Ads daily performance",
    },
    "meta_spend": {
        "extract": lambda s: s["spend"]["meta"],
        "label": "Meta Ads Spend", "unit": "USD",
        "scope_label": "Meta Ads only (`spend` field)",
        "yaml_name": None,
        "formula": "SUM(spend) from Meta Ads daily performance",
    },
    "total_sessions": {
        "extract": lambda s: s["sessions"]["total"],
        "label": "Total Sessions", "unit": "count",
        "scope_label": "GA4 sessions, all channels",
        "yaml_name": "total_sessions",
    },
    "engaged_sessions": {
        "extract": lambda s: s["sessions"]["engaged"],
        "label": "Engaged Sessions", "unit": "count",
        "scope_label": "GA4 engaged sessions, all channels",
        "yaml_name": "total_engaged_sessions",
    },
    "engagement_rate": {
        "extract": lambda s: s["sessions"]["engagement_rate_pct"],
        "label": "Engagement Rate", "unit": "%",
        "scope_label": "engaged_sessions / sessions",
        "yaml_name": "engagement_rate",
    },
    "total_ga4_conversions": {
        "extract": lambda s: s["conversions"]["ga4_total"],
        "label": "GA4 Conversions", "unit": "count",
        "scope_label": "GA4 conversion events (Session CVR numerator)",
        "yaml_name": "total_ga4_conversions",
    },
    "ad_conversions": {
        "extract": lambda s: s["conversions"]["ad_platform"],
        "label": "Ad-Platform Conversions", "unit": "count",
        "scope_label": "Click-based platform conversions — NOT comparable to GA4 conversions",
        "yaml_name": None,
        "formula": "SUM(conversions) from Google Ads + SUM(purchases) from Meta Ads",
    },
    "session_conversion_rate": {
        "extract": lambda s: s["conversions"]["session_cvr_pct"],
        "label": "Session CVR", "unit": "%",
        "scope_label": "Session CVR — label as `CVR (session)`; never mix with Click CVR",
        "yaml_name": "session_conversion_rate",
    },
    "blended_roas": {
        "extract": lambda s: s["blended_roas"],
        "label": "Blended ROAS", "unit": "ratio",
        "scope_label": "Linear attribution — label as `Linear attribution · <window>`",
        "yaml_name": "blended_roas",
        "attribution_model": "linear (touchpoint-date windowing)",
    },
}


def _load_golden() -> dict | None:
    if not GOLDEN_PATH.exists():
        return None
    return json.loads(GOLDEN_PATH.read_text())


def _golden_missing() -> dict:
    return {"error": "golden_metrics.json not found.",
            "fix": "Run: python scripts/generate_golden_metrics.py"}


def _yaml_metrics() -> dict[str, dict]:
    """Governed metric definitions from the dbt semantic layer (metrics.yml)."""
    if not METRICS_YML.exists():
        return {}
    doc = yaml.safe_load(METRICS_YML.read_text())
    out = {}
    for m in doc.get("metrics", []):
        tp = m.get("type_params", {})
        formula = tp.get("expr") or (f"SUM({tp.get('measure')})" if tp.get("measure") else None)
        out[m["name"]] = {
            "label": m.get("label"),
            "description": (m.get("description") or "").strip(),
            "type": m.get("type"),
            "formula": formula,
        }
    return out


def _resolve_window(golden: dict, window: str) -> tuple[dict, dict] | dict:
    """Return (section, window_info) or an error dict."""
    if window not in golden or window.startswith("_"):
        available = [k for k in golden if not k.startswith("_")]
        return {"error": f"Window '{window}' not found.", "available_windows": available}
    section = golden[window]
    return section, {
        "key": window,
        "start": section["window"]["start"],
        "end": section["window"]["end"],
        "label": section.get("label", window),
    }


def _source_block(golden: dict) -> dict:
    meta = golden.get("_meta", {})
    return {
        "artifact": "golden_metrics.json",
        "schema_version": meta.get("schema_version"),
        "generated_at": meta.get("generated_at"),
        "anchor_date": meta.get("anchor_date"),
        "semantic_layer_crosscheck": meta.get("semantic_layer_crosscheck"),
    }


GOVERNANCE_NOTE = (
    "Copy this value verbatim — never recalculate it. Never combine values "
    "from different windows in one ratio (scope mixing). Display scope_label "
    "with the number."
)


def list_metrics() -> dict:
    """
    List every governed metric this server can return, with its unit, scope,
    and whether it is defined in the dbt semantic layer (metrics.yml).
    Also returns the available pre-computed windows. Start here.
    """
    golden = _load_golden()
    if golden is None:
        return _golden_missing()
    yaml_defs = _yaml_metrics()
    metrics = []
    for mid, reg in METRIC_REGISTRY.items():
        ydef = yaml_defs.get(reg["yaml_name"]) if reg.get("yaml_name") else None
        metrics.append({
            "metric_id": mid,
            "label": reg["label"],
            "unit": reg["unit"],
            "scope_label": reg["scope_label"],
            "semantic_layer_governed": ydef is not None,
            "summary": (ydef["description"].split("\n")[0] if ydef and ydef["description"]
                        else reg.get("formula", "")),
        })
    return {
        "metrics": metrics,
        "available_windows": list(golden["_meta"].get("available_windows", {}).keys()),
        "source": _source_block(golden),
        "usage": "get_metric(metric_id, window) for values; explain_metric(metric_id) for definitions.",
    }


def get_metric(metric: str, window: str = "windowed_90d") -> dict:
    """
    Return ONE governed metric value with its full governance envelope:
    value, formula, scope label, window bounds, and artifact provenance.

    Args:
        metric: A metric_id from list_metrics(), e.g. "blended_roas",
                "session_conversion_rate", "total_spend".
        window: A pre-computed window key, e.g. "windowed_90d" (default),
                "windowed_30d", "all_time", "month_2026_06".
    """
    golden = _load_golden()
    if golden is None:
        return _golden_missing()
    if metric not in METRIC_REGISTRY:
        return {"error": f"Unknown metric '{metric}'.",
                "available_metrics": list(METRIC_REGISTRY.keys())}
    resolved = _resolve_window(golden, window)
    if isinstance(resolved, dict):
        return resolved
    section, window_info = resolved

    reg = METRIC_REGISTRY[metric]
    ydef = _yaml_metrics().get(reg["yaml_name"]) if reg.get("yaml_name") else None
    return {
        "metric_id": metric,
        "label": reg["label"],
        "value": reg["extract"](section),
        "unit": reg["unit"],
        "scope_label": reg["scope_label"],
        "window": window_info,
        "formula": (ydef or {}).get("formula") or reg.get("formula"),
        "attribution_model": reg.get("attribution_model"),
        "semantic_layer_governed": ydef is not None,
        "source": _source_block(golden),
        "governance_note": GOVERNANCE_NOTE,
    }


def explain_metric(metric: str) -> dict:
    """
    Return the governed DEFINITION of a metric: formula, full description,
    scope, and warnings — read from the dbt semantic layer (metrics.yml),
    the project's single source of metric truth. No values.
    """
    if metric not in METRIC_REGISTRY:
        return {"error": f"Unknown metric '{metric}'.",
                "available_metrics": list(METRIC_REGISTRY.keys())}
    reg = METRIC_REGISTRY[metric]
    ydef = _yaml_metrics().get(reg["yaml_name"]) if reg.get("yaml_name") else None
    return {
        "metric_id": metric,
        "label": reg["label"],
        "unit": reg["unit"],
        "scope_label": reg["scope_label"],
        "formula": (ydef or {}).get("formula") or reg.get("formula"),
        "attribution_model": reg.get("attribution_model"),
        "semantic_layer_governed": ydef is not None,
        "definition": (ydef or {}).get("description")
                      or "Not in metrics.yml — presentation-level aggregate; formula above.",
        "defined_in": str(METRICS_YML.relative_to(PROJECT_ROOT)) if ydef else "analytics_server registry",
    }


def get_funnel(window: str = "windowed_90d") -> dict:
    """
    Return the marketing funnel for a window with SERVER-SIDE integrity
    validation: each step must be <= the step above it (CLAUDE.md §5).

    CRM lifetime counts (HubSpot contacts) are deliberately EXCLUDED — they
    are all-time numbers and cannot be a step below windowed GA4 conversions.
    Render them as separate KPI cards labelled 'CRM all-time'.
    """
    golden = _load_golden()
    if golden is None:
        return _golden_missing()
    resolved = _resolve_window(golden, window)
    if isinstance(resolved, dict):
        return resolved
    section, window_info = resolved

    steps = [
        {"name": "Sessions",         "value": section["sessions"]["total"]},
        {"name": "Engaged Sessions", "value": section["sessions"]["engaged"]},
        {"name": "Conversions",      "value": section["conversions"]["ga4_total"]},
    ]
    issues = []
    for above, below in zip(steps, steps[1:]):
        if below["value"] > above["value"]:
            issues.append(f"Funnel violation: {below['name']} ({below['value']}) "
                          f"> {above['name']} ({above['value']})")
    return {
        "window": window_info,
        "steps": steps,
        "valid": not issues,
        "issues": issues,
        "excluded": {
            "crm_contacts": "All-time lifetime count — never a funnel step (§5). "
                            "Use get_precomputed_window('all_time')['crm'] and label 'CRM all-time'.",
        },
        "source": _source_block(golden),
        "governance_note": GOVERNANCE_NOTE,
    }


def compare_windows(metric: str, window_a: str, window_b: str) -> dict:
    """
    Compare ONE metric across two pre-computed windows, safely labelled.
    Flags comparability problems (e.g. a month-to-date section vs a full
    month) instead of leaving them for the consumer to notice.
    """
    a = get_metric(metric, window_a)
    b = get_metric(metric, window_b)
    if "error" in a:
        return a
    if "error" in b:
        return b

    delta = round(b["value"] - a["value"], 4)
    pct = round((b["value"] - a["value"]) / a["value"] * 100, 2) if a["value"] else None
    warnings = []
    for env in (a, b):
        if "month to date" in env["window"]["label"]:
            warnings.append(
                f"{env['window']['key']} is MONTH-TO-DATE ({env['window']['start']} → "
                f"{env['window']['end']}) — do not compare 1:1 against a complete period "
                f"without noting the day counts."
            )
    return {
        "metric_id": metric,
        "label": a["label"],
        "unit": a["unit"],
        "scope_label": a["scope_label"],
        "a": {"window": a["window"], "value": a["value"]},
        "b": {"window": b["window"], "value": b["value"]},
        "delta": delta,
        "pct_change": pct,
        "comparability_warnings": warnings,
        "source": a["source"],
        "governance_note": GOVERNANCE_NOTE,
    }


def query_metrics(start_date: str, end_date: str, label: str = "") -> dict:
    """
    ESCAPE HATCH: query aggregated metrics for ANY date range (not just the
    pre-computed windows). Returns a full golden-schema section computed
    ad-hoc from source data with the same canonical formulas.

    The result is labelled ad-hoc — dashboards built from it must display:
    "⚡ Ad-hoc query · not from golden layer".
    CRM data is always all-time regardless of date range.
    """
    start = date.fromisoformat(start_date)
    end   = date.fromisoformat(end_date)
    section = query_window(start, end, label or f"{start_date} → {end_date}")
    section["_source"] = "ad-hoc query_window — not from golden layer; label dashboards accordingly"
    return section


def get_precomputed_window(window: str) -> dict:
    """
    Return a FULL pre-computed section from golden_metrics.json (all tables:
    channel performance, attribution, campaigns, CRM). Use get_metric() for
    single governed values; use this when you need the detailed breakdowns.
    Pass window="list" to see available keys and the current anchor.
    """
    golden = _load_golden()
    if golden is None:
        return _golden_missing()

    if window == "list":
        meta = golden.get("_meta", {})
        return {
            "available_windows": list(meta.get("available_windows", {}).keys()),
            "anchor_date": meta.get("anchor_date"),
            "window_start": meta.get("window_start"),
            "window_end": meta.get("window_end"),
            "generated_at": meta.get("generated_at"),
        }

    resolved = _resolve_window(golden, window)
    if isinstance(resolved, dict):
        return resolved
    section, _ = resolved
    section = dict(section)
    section["_source"] = "golden_metrics.json"
    section["_window_key"] = window
    return section


def get_meta() -> dict:
    """
    Return golden_metrics.json metadata: anchor_date, window bounds,
    generated_at, schema_version, semantic_layer_crosscheck status, and
    available_windows. Use this to check data freshness before reporting.
    """
    golden = _load_golden()
    if golden is None:
        return {"error": "golden_metrics.json not found"}
    return golden.get("_meta", {})


# Register plain functions as MCP tools (kept unwrapped at module level so the
# test suite can call them directly).
for _fn in (list_metrics, get_metric, explain_metric, get_funnel,
            compare_windows, query_metrics, get_precomputed_window, get_meta):
    mcp.tool()(_fn)


if __name__ == "__main__":
    mcp.run()
