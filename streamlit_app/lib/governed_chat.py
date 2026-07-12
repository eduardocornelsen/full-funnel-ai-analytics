"""Governed chat backend — the Streamlit AI analyst's tool layer.

The chat's tools ARE the governed analytics server's functions (imported
in-process — same code the MCP clients use, no transport). The model cannot
run raw SQL from this surface: every number it can obtain arrives wrapped in
the governance envelope (value + formula + scope + window + provenance),
which the UI then renders as "How was this computed".

Kept free of Streamlit imports so the contract is unit-testable.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "mcp_servers"))

import analytics_server as srv  # noqa: E402

# Anthropic tool schemas mirroring the governed analytics server.
GOVERNED_TOOLS = [
    {
        "name": "list_metrics",
        "description": ("List every governed metric (id, unit, scope, whether the dbt "
                        "semantic layer defines it) and the available pre-computed "
                        "windows. Call this first if unsure what exists."),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_metric",
        "description": ("Get ONE governed metric value with its full governance envelope "
                        "(value, formula, scope_label, window, source). Copy the value "
                        "verbatim; always present it with its scope_label and window."),
        "input_schema": {
            "type": "object",
            "properties": {
                "metric": {"type": "string", "description": "metric_id from list_metrics, e.g. 'blended_roas'"},
                "window": {"type": "string", "description": "e.g. 'windowed_90d' (default), 'windowed_30d', 'all_time', 'month_2026_06'"},
            },
            "required": ["metric"],
        },
    },
    {
        "name": "explain_metric",
        "description": "Get the governed DEFINITION of a metric (formula, scope, warnings) from the dbt semantic layer. No values.",
        "input_schema": {
            "type": "object",
            "properties": {"metric": {"type": "string"}},
            "required": ["metric"],
        },
    },
    {
        "name": "get_funnel",
        "description": ("Get the marketing funnel (sessions → engaged → conversions) for a window, "
                        "validated server-side. CRM lifetime counts are excluded by design — never "
                        "add them as funnel steps."),
        "input_schema": {
            "type": "object",
            "properties": {"window": {"type": "string", "description": "default 'windowed_90d'"}},
        },
    },
    {
        "name": "compare_windows",
        "description": ("Compare ONE metric across two windows (delta + % change). Surfaces "
                        "comparability warnings (e.g. month-to-date vs full month) — repeat "
                        "any warning to the user."),
        "input_schema": {
            "type": "object",
            "properties": {
                "metric": {"type": "string"},
                "window_a": {"type": "string"},
                "window_b": {"type": "string"},
            },
            "required": ["metric", "window_a", "window_b"],
        },
    },
    {
        "name": "get_precomputed_window",
        "description": ("Get a FULL golden-layer section (channel performance, attribution by channel, "
                        "campaign tables, CRM pipeline) for one window. Use for breakdowns beyond "
                        "single metrics. Pass window='list' to discover keys."),
        "input_schema": {
            "type": "object",
            "properties": {"window": {"type": "string"}},
            "required": ["window"],
        },
    },
    {
        "name": "query_metrics",
        "description": ("ESCAPE HATCH for date ranges with no pre-computed window (e.g. last 45 days, "
                        "a quarter). Ad-hoc — you MUST tell the user the result is an ad-hoc query, "
                        "not from the golden layer. CRM data stays all-time."),
        "input_schema": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "description": "YYYY-MM-DD"},
                "end_date": {"type": "string", "description": "YYYY-MM-DD"},
            },
            "required": ["start_date", "end_date"],
        },
    },
]

_DISPATCH = {
    "list_metrics": lambda i: srv.list_metrics(),
    "get_metric": lambda i: srv.get_metric(i["metric"], i.get("window", "windowed_90d")),
    "explain_metric": lambda i: srv.explain_metric(i["metric"]),
    "get_funnel": lambda i: srv.get_funnel(i.get("window", "windowed_90d")),
    "compare_windows": lambda i: srv.compare_windows(i["metric"], i["window_a"], i["window_b"]),
    "get_precomputed_window": lambda i: srv.get_precomputed_window(i["window"]),
    "query_metrics": lambda i: srv.query_metrics(i["start_date"], i["end_date"]),
}


def dispatch_tool(name: str, tool_input: dict) -> dict:
    """Execute a governed tool call; always returns a JSON-serializable dict."""
    fn = _DISPATCH.get(name)
    if fn is None:
        return {"error": f"Unknown tool '{name}'", "available": list(_DISPATCH)}
    try:
        return fn(tool_input or {})
    except Exception as e:  # surface, never crash the chat loop
        return {"error": f"{type(e).__name__}: {e}"}


def build_system_prompt() -> str:
    """Render the analyst system prompt at RUNTIME from the golden artifact.

    No literal dates: window bounds, anchor, and freshness all come from
    _meta, so the prompt can never go stale (the previous chat hardcoded
    '2024-03-30 to 2026-03-15' and drifted for months).
    """
    meta = srv.get_meta()
    windows = ", ".join(meta.get("available_windows", {}).keys()) or "unknown"
    return f"""You are the governed AI analyst for a full-funnel marketing analytics platform.

DATA CONTRACT (non-negotiable):
- Every number you present MUST come from a tool call. Copy values verbatim — never compute, \
extrapolate, or average numbers yourself.
- Always state each metric's scope_label and window alongside its value \
(e.g. "Blended ROAS 10.7× — linear attribution · 2026-04-14 → 2026-07-12").
- Never combine values from different windows into one ratio (scope mixing).
- CRM figures are lifetime counts: label them "CRM all-time"; never place them in a funnel.
- If a tool returns comparability warnings or an ad-hoc label, repeat that caveat to the user.

DATA STATE (live from the golden artifact):
- Anchor date: {meta.get('anchor_date')} · generated {meta.get('generated_at')}
- Dataset range: {meta.get('dataset_start')} → {meta.get('dataset_end')}
- Pre-computed windows: {windows}
- Semantic-layer verification: {meta.get('semantic_layer_crosscheck')}

Default to windowed_90d when the user doesn't specify a period. Answer in 2–5 concise,
business-focused sentences after gathering the numbers you need."""


def summarize_tool_call(name: str, tool_input: dict, output: dict) -> dict:
    """Compact record of one tool call for the 'How was this computed' panel."""
    rec = {"tool": name, "input": tool_input}
    if "value" in output and "formula" in output:      # metric envelope
        rec["provenance"] = {k: output.get(k) for k in
                             ("metric_id", "value", "unit", "formula", "scope_label")}
        rec["provenance"]["window"] = output.get("window", {}).get("label")
        rec["provenance"]["verified"] = (output.get("source") or {}).get("semantic_layer_crosscheck")
    elif "steps" in output:                            # funnel
        rec["provenance"] = {"steps": output["steps"], "valid": output.get("valid"),
                             "window": output.get("window", {}).get("label")}
    elif "delta" in output:                            # comparison
        rec["provenance"] = {"a": output.get("a"), "b": output.get("b"),
                             "delta": output.get("delta"), "pct_change": output.get("pct_change"),
                             "warnings": output.get("comparability_warnings")}
    else:
        rec["provenance"] = {"summary": json.dumps(output, default=str)[:400]}
    return rec
