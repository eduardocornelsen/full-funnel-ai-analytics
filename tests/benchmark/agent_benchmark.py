"""SQRA agent benchmark — model-in-the-loop, three architectures compared.

The question the market never answers neutrally: given the same natural-
language questions and the same underlying data, does an AI agent reproduce
the organization's canonical KPIs — and at what token cost — when grounded in:

  A. golden-tools    the governed analytics server (pre-computed + envelopes)
  B. raw-sql         a schema dump + free SQL against the warehouse
  C. semantic-layer  MetricFlow (`mf query`) over the dbt semantic layer

Ground truth: the same golden-derived expected values the deterministic
surfaces use (tests/benchmark/cases.json → expected_ref), so agent answers are
scored with the exact same tolerance-typed precision function.

Requires ANTHROPIC_API_KEY. Run via:
    python scripts/run_sqra.py --agents [--model claude-haiku-4-5-20251001]

The agent loop accepts an injectable client factory so the harness itself is
unit-tested with a scripted fake — no network in CI's test job.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "streamlit_app"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from scorer import precision_score  # noqa: E402
from run_benchmark import _load_cases  # noqa: E402

DEFAULT_MODEL = "claude-haiku-4-5-20251001"
MAX_TURNS = 8

ANSWER_RE = re.compile(r"ANSWER:\s*([-+]?[\d,]*\.?\d+)")


# ── Question set ──────────────────────────────────────────────────────────────

def load_questions(limit: int | None = None) -> list[dict]:
    """Numeric-valued canonical questions with golden-derived ground truth."""
    cases = [c for c in _load_cases("all")
             if not c.get("is_adversarial")
             and c["surface"] in ("mcp", "golden")
             and isinstance(c.get("expected_value"), (int, float))]
    # De-duplicate by question text (mcp and golden share some intents)
    seen, out = set(), []
    for c in cases:
        if c["question"] not in seen:
            seen.add(c["question"])
            out.append({"id": c["id"], "question": c["question"],
                        "expected": float(c["expected_value"]),
                        "tolerance": c["tolerance"]})
    return out[:limit] if limit else out


# ── Architecture definitions ──────────────────────────────────────────────────

def _golden_tools_arch() -> dict:
    from lib.governed_chat import GOVERNED_TOOLS, build_system_prompt, dispatch_tool
    return {
        "name": "golden-tools",
        "system": build_system_prompt() +
                  "\nWhen you have the number, end your reply with a line: ANSWER: <number>",
        "tools": GOVERNED_TOOLS,
        "dispatch": dispatch_tool,
    }


def _raw_sql_arch() -> dict:
    import duckdb
    db = PROJECT_ROOT / "data" / "olist_analytics.duckdb"
    con = duckdb.connect(str(db), read_only=True)
    schema_rows = con.execute(
        "SELECT table_name, string_agg(column_name, ', ') FROM information_schema.columns "
        "WHERE table_schema='main' GROUP BY table_name ORDER BY table_name").fetchall()
    schema = "\n".join(f"{t}: {cols}" for t, cols in schema_rows)

    def dispatch(name: str, tool_input: dict) -> dict:
        try:
            rows = con.execute(tool_input["sql"]).fetchall()
            return {"rows": rows[:50]}
        except Exception as e:
            return {"error": str(e)}

    return {
        "name": "raw-sql",
        "system": ("You are a marketing analytics assistant. Answer using SQL against the "
                   "DuckDB warehouse via the query_database tool.\n\nTables and columns:\n"
                   f"{schema}\n\nWhen you have the number, end your reply with a line: "
                   "ANSWER: <number>"),
        "tools": [{
            "name": "query_database",
            "description": "Execute a DuckDB SQL query and return up to 50 rows.",
            "input_schema": {"type": "object",
                             "properties": {"sql": {"type": "string"}},
                             "required": ["sql"]},
        }],
        "dispatch": dispatch,
    }


def _semantic_layer_arch() -> dict:
    golden_meta = json.loads((PROJECT_ROOT / "dashboards" / "golden_metrics.json")
                             .read_text())["_meta"]

    def dispatch(name: str, tool_input: dict) -> dict:
        cmd = ["mf", "query", "--metrics", tool_input["metrics"]]
        if tool_input.get("group_by"):
            cmd += ["--group-by", tool_input["group_by"]]
        if tool_input.get("start_time"):
            cmd += ["--start-time", tool_input["start_time"]]
        if tool_input.get("end_time"):
            cmd += ["--end-time", tool_input["end_time"]]
        r = subprocess.run(cmd, cwd=PROJECT_ROOT / "dbt_project",
                           capture_output=True, text=True, timeout=300)
        return {"output": (r.stdout + r.stderr)[-3000:]}

    return {
        "name": "semantic-layer",
        "system": ("You are a marketing analytics assistant. Answer ONLY via the dbt "
                   "semantic layer using the query_metrics tool (MetricFlow). Available "
                   "metrics include: total_spend, total_sessions, total_engaged_sessions, "
                   "total_ga4_conversions, session_conversion_rate, blended_roas, "
                   "total_attributed_revenue, channel_spend, channel_revenue (group_by "
                   "channel_date__channel), engagement_rate, total_pipeline_value.\n"
                   f"The canonical 90-day window is {golden_meta['window_start']} → "
                   f"{golden_meta['window_end']}; dataset spans {golden_meta['dataset_start']} → "
                   f"{golden_meta['dataset_end']}. Ratio metrics return fractions — convert to "
                   "percent when the question asks for a rate.\n"
                   "When you have the number, end your reply with a line: ANSWER: <number>"),
        "tools": [{
            "name": "query_metrics",
            "description": "Run `mf query` against the dbt semantic layer.",
            "input_schema": {"type": "object", "properties": {
                "metrics":    {"type": "string", "description": "comma-separated metric names"},
                "group_by":   {"type": "string"},
                "start_time": {"type": "string", "description": "YYYY-MM-DD"},
                "end_time":   {"type": "string", "description": "YYYY-MM-DD"},
            }, "required": ["metrics"]},
        }],
        "dispatch": dispatch,
    }


ARCHITECTURES: dict[str, Callable[[], dict]] = {
    "golden-tools":   _golden_tools_arch,
    "raw-sql":        _raw_sql_arch,
    "semantic-layer": _semantic_layer_arch,
}


# ── Agent loop ────────────────────────────────────────────────────────────────

def run_agent(client: Any, model: str, arch: dict, question: str) -> dict:
    """One question through one architecture. Returns answer + token usage."""
    messages: list[dict] = [{"role": "user", "content": question}]
    tokens_in = tokens_out = tool_calls = 0
    final_text = ""

    for _ in range(MAX_TURNS):
        response = client.messages.create(
            model=model, max_tokens=1500, system=arch["system"],
            tools=arch["tools"], messages=messages,
        )
        tokens_in += response.usage.input_tokens
        tokens_out += response.usage.output_tokens

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            results = []
            for block in response.content:
                if block.type == "tool_use":
                    tool_calls += 1
                    out = arch["dispatch"](block.name, block.input)
                    results.append({"type": "tool_result", "tool_use_id": block.id,
                                    "content": json.dumps(out, default=str)[:6000]})
            messages.append({"role": "user", "content": results})
        else:
            final_text = "".join(getattr(b, "text", "") for b in response.content)
            break

    m = ANSWER_RE.search(final_text or "")
    answer = float(m.group(1).replace(",", "")) if m else None
    return {"answer": answer, "text": final_text, "tokens_in": tokens_in,
            "tokens_out": tokens_out, "tool_calls": tool_calls}


def run_agents(model: str = DEFAULT_MODEL, limit: int | None = None,
               architectures: list[str] | None = None,
               client_factory: Callable[[], Any] | None = None) -> dict:
    """Run every architecture over the question set and score numeric fidelity."""
    if client_factory is None:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            sys.exit("ANTHROPIC_API_KEY not set — the agent benchmark needs a model. "
                     "Deterministic surfaces run without it: python scripts/run_sqra.py")
        import anthropic
        client_factory = anthropic.Anthropic

    questions = load_questions(limit)
    client = client_factory()
    report: dict = {"model": model, "question_count": len(questions), "architectures": {}}

    for arch_name in architectures or list(ARCHITECTURES):
        arch = ARCHITECTURES[arch_name]()
        per_q, correct, tokens = [], 0, 0
        for q in questions:
            r = run_agent(client, model, arch, q["question"])
            p = precision_score(r["answer"], q["expected"], q["tolerance"]) \
                if r["answer"] is not None else 0.0
            correct += p >= 0.99
            tokens += r["tokens_in"] + r["tokens_out"]
            per_q.append({"id": q["id"], "expected": q["expected"],
                          "answer": r["answer"], "precision": round(p, 3),
                          "tool_calls": r["tool_calls"],
                          "tokens": r["tokens_in"] + r["tokens_out"]})
        n = max(len(questions), 1)
        report["architectures"][arch_name] = {
            "accuracy_pct": round(100 * correct / n, 1),
            "mean_precision": round(sum(x["precision"] for x in per_q) / n, 3),
            "total_tokens": tokens,
            "tokens_per_question": round(tokens / n),
            "cases": per_q,
        }
    return report
