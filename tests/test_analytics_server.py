"""Contract tests for the governed analytics MCP server.

The server's promise is that no number leaves it without governance metadata.
These tests pin that contract: envelope completeness, funnel validation,
month-to-date comparability warnings, and formula provenance from metrics.yml.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "mcp_servers"))
import analytics_server as srv  # noqa: E402

pytestmark = pytest.mark.skipif(
    not srv.GOLDEN_PATH.exists(),
    reason="golden_metrics.json not generated — run scripts/generate_golden_metrics.py",
)

ENVELOPE_FIELDS = {"metric_id", "label", "value", "unit", "scope_label",
                   "window", "formula", "source", "governance_note"}


def test_list_metrics_inventory():
    out = srv.list_metrics()
    ids = {m["metric_id"] for m in out["metrics"]}
    assert {"blended_roas", "session_conversion_rate", "total_spend"} <= ids
    assert "windowed_90d" in out["available_windows"]
    # Every metric declares whether the semantic layer governs it
    assert all("semantic_layer_governed" in m for m in out["metrics"])


def test_get_metric_envelope_complete():
    for metric in srv.METRIC_REGISTRY:
        env = srv.get_metric(metric)
        assert ENVELOPE_FIELDS <= set(env), f"{metric} envelope missing fields"
        assert env["window"]["key"] == "windowed_90d"
        assert env["window"]["start"] and env["window"]["end"]
        assert env["source"]["artifact"] == "golden_metrics.json"


def test_get_metric_matches_golden_artifact():
    import json
    golden = json.loads(srv.GOLDEN_PATH.read_text())
    env = srv.get_metric("blended_roas", "windowed_90d")
    assert env["value"] == golden["windowed_90d"]["blended_roas"]
    assert env["attribution_model"].startswith("linear")


def test_yaml_governed_formula_comes_from_metrics_yml():
    env = srv.explain_metric("blended_roas")
    assert env["semantic_layer_governed"] is True
    assert "total_attributed_revenue" in env["formula"]
    assert "metrics.yml" in env["defined_in"]


def test_unknown_metric_and_window_are_guided():
    assert "available_metrics" in srv.get_metric("nonexistent")
    assert "available_windows" in srv.get_metric("blended_roas", "windowed_45d")


def test_funnel_is_validated_server_side():
    out = srv.get_funnel("windowed_90d")
    assert out["valid"] is True and out["issues"] == []
    values = [s["value"] for s in out["steps"]]
    assert values == sorted(values, reverse=True)
    # CRM lifetime counts must be excluded with an explanation, not silently
    assert "crm_contacts" in out["excluded"]


def test_compare_windows_flags_month_to_date():
    import json
    golden = json.loads(srv.GOLDEN_PATH.read_text())
    mtd = [k for k in golden if k.startswith("month_")
           and "month to date" in golden[k]["label"]]
    full = [k for k in golden if k.startswith("month_")
            and "(full month)" in golden[k]["label"]]
    if not (mtd and full):
        pytest.skip("no month-to-date + full-month pair in current golden")
    out = srv.compare_windows("total_spend", full[0], mtd[0])
    assert out["comparability_warnings"], "month-to-date comparison must carry a warning"
    assert out["a"]["value"] != out["b"]["value"] or out["delta"] == 0


def test_precomputed_window_marks_source():
    out = srv.get_precomputed_window("windowed_90d")
    assert out["_source"] == "golden_metrics.json"
