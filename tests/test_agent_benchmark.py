"""Unit tests for the SQRA agent-benchmark harness — no API key, no network.

A scripted fake client proves the loop end-to-end: tool dispatch, token
accounting, ANSWER parsing, and precision scoring against golden-derived
ground truth.
"""

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "tests" / "benchmark"))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import agent_benchmark as ab  # noqa: E402

pytestmark = pytest.mark.skipif(
    not (Path(__file__).parent.parent / "dashboards" / "golden_metrics.json").exists(),
    reason="golden_metrics.json not generated",
)


def _text_block(text):
    return SimpleNamespace(type="text", text=text)


def _tool_block(name, tool_input, block_id="t1"):
    return SimpleNamespace(type="tool_use", name=name, input=tool_input, id=block_id)


class FakeClient:
    """Turn 1: calls get_metric; turn 2: answers with the value it got back."""

    def __init__(self):
        self.messages = self
        self._turn = 0

    def create(self, **kwargs):
        self._turn += 1
        usage = SimpleNamespace(input_tokens=100, output_tokens=20)
        if self._turn == 1:
            return SimpleNamespace(
                stop_reason="tool_use", usage=usage,
                content=[_tool_block("get_metric", {"metric": "total_sessions"})])
        # Echo the canonical value back — read from the last tool_result
        import json as _json
        tool_result = kwargs["messages"][-1]["content"][0]["content"]
        value = _json.loads(tool_result)["value"]
        return SimpleNamespace(
            stop_reason="end_turn", usage=usage,
            content=[_text_block(f"The total is {value}.\nANSWER: {value}")])


def test_questions_have_golden_ground_truth():
    qs = ab.load_questions()
    assert len(qs) >= 10
    assert all(isinstance(q["expected"], float) for q in qs)


def test_agent_loop_end_to_end_with_fake_client():
    report = ab.run_agents(limit=1, architectures=["golden-tools"],
                           client_factory=FakeClient)
    arch = report["architectures"]["golden-tools"]
    assert arch["cases"][0]["tool_calls"] == 1
    assert arch["cases"][0]["tokens"] == 240  # 2 turns × (100 + 20)
    # The fake echoes the governed tool's own value → precision may still be
    # <1 if the question's canonical window differs from the tool default;
    # what we assert is the plumbing: an answer was parsed and scored.
    assert arch["cases"][0]["answer"] is not None
    assert 0.0 <= arch["cases"][0]["precision"] <= 1.0


def test_answer_regex_handles_commas_and_decimals():
    assert ab.ANSWER_RE.search("ANSWER: 452,187").group(1) == "452,187"
    assert ab.ANSWER_RE.search("blah\nANSWER: 10.73").group(1) == "10.73"
    assert ab.ANSWER_RE.search("no answer here") is None


def test_architectures_all_construct():
    # golden-tools and raw-sql need only local artifacts; semantic-layer needs
    # the mf CLI on PATH (present in dev/CI images).
    for name in ("golden-tools", "raw-sql"):
        arch = ab.ARCHITECTURES[name]()
        assert arch["tools"] and arch["system"] and callable(arch["dispatch"])
