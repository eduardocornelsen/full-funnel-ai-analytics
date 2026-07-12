"""Tests for the Streamlit governed-chat backend (no Streamlit required)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "streamlit_app"))
from lib import governed_chat as gc  # noqa: E402
from lib import bootstrap as bs      # noqa: E402

pytestmark = pytest.mark.skipif(
    not gc.srv.GOLDEN_PATH.exists(),
    reason="golden_metrics.json not generated",
)


def test_tool_schemas_match_dispatch_table():
    schema_names = {t["name"] for t in gc.GOVERNED_TOOLS}
    assert schema_names == set(gc._DISPATCH), (
        "every advertised tool must be dispatchable and vice versa")


def test_dispatch_returns_envelope():
    out = gc.dispatch_tool("get_metric", {"metric": "blended_roas"})
    assert out["value"] and out["formula"] and out["scope_label"]


def test_dispatch_never_raises():
    assert "error" in gc.dispatch_tool("no_such_tool", {})
    assert "error" in gc.dispatch_tool("get_metric", {})  # missing required arg


def test_system_prompt_is_runtime_rendered():
    prompt = gc.build_system_prompt()
    meta = gc.srv.get_meta()
    assert meta["anchor_date"] in prompt, "prompt must carry the live anchor date"
    assert "windowed_90d" in prompt
    assert "scope mixing" in prompt.lower() or "scope_label" in prompt


def test_summarize_metric_call_has_provenance():
    out = gc.dispatch_tool("get_metric", {"metric": "session_conversion_rate"})
    rec = gc.summarize_tool_call("get_metric", {"metric": "session_conversion_rate"}, out)
    assert rec["provenance"]["formula"]
    assert rec["provenance"]["window"]


def test_bootstrap_noop_when_built():
    # In this environment the warehouse exists — ensure_warehouse must be a no-op.
    if bs.needs_bootstrap():
        pytest.skip("warehouse not built in this environment")
    calls = []
    assert bs.ensure_warehouse(progress=calls.append) is False
    assert calls == []
