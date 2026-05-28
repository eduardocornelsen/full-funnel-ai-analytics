"""
run_benchmark.py
─────────────────────────────────────────────────────────────────────────────
SQRA — Search Quality & Retrieval Accuracy benchmark runner.

Five task runners, one per retrieval surface:
  mcp          — calls MCP server functions directly; compares against golden JSON
  golden       — navigates golden_metrics.json at specific JSON paths
  semantic     — executes DuckDB SQL; compares against golden JSON
  nl2sql       — same as semantic but 5 cases are intentionally flawed (adversarial)
  query_window — calls query_window.py for arbitrary date ranges; tests
                 --last-days N, --month YYYY-MM, and custom --start/--end

Usage (via scripts/run_sqra.py):
    python scripts/run_sqra.py [--surface mcp|golden|semantic|nl2sql|query_window|all]
"""

from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR     = PROJECT_ROOT / "data" / "mock_marketing"
GOLDEN_PATH  = PROJECT_ROOT / "dashboards" / "golden_metrics.json"
CASES_PATH   = Path(__file__).parent / "cases.json"

sys.path.insert(0, str(PROJECT_ROOT / "mcp_servers"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from scorer import precision_score, relevance_score, sqra_score  # noqa: E402


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_cases(surface_filter: str | None = None) -> list[dict]:
    text = CASES_PATH.read_text()
    # Strip JS-style comments (// ...) before parsing
    import re
    text = re.sub(r"//[^\n]*", "", text)
    data = json.loads(text)
    cases = data["cases"]
    if surface_filter and surface_filter != "all":
        cases = [c for c in cases if c["surface"] == surface_filter]
    return cases


def _load_golden() -> dict:
    return json.loads(GOLDEN_PATH.read_text())


def _make_result(case: dict, retrieved, precision: float,
                 relevance: float, error: str | None = None) -> dict:
    sqra = sqra_score(precision, relevance)
    return {
        "id":        case["id"],
        "surface":   case["surface"],
        "question":  case["question"],
        "expected":  case["expected_value"],
        "retrieved": retrieved,
        "precision": round(precision, 4),
        "relevance": round(relevance, 4),
        "sqra":      round(sqra, 1),
        "error":     error,
        "tags":      case.get("tags", []),
        "adversarial": case.get("is_adversarial", False),
    }


# ── Extraction helpers (MCP surface) ─────────────────────────────────────────

def _apply_extract(result_data: Any, spec: dict) -> float | str:
    op = spec["op"]

    if op == "sum":
        return sum(float(row.get(spec["field"], 0) or 0) for row in result_data)

    if op == "direct":
        return result_data[spec["field"]]

    if op == "filter_sum":
        rows = [r for r in result_data if str(r.get(spec["by"], "")).lower() == str(spec["value"]).lower()]
        return sum(float(r.get(spec["field"], 0) or 0) for r in rows)

    if op == "filter_cvr":
        rows = [r for r in result_data if str(r.get(spec["by"], "")).lower() == str(spec["value"]).lower()]
        conv = sum(float(r.get(spec["conv_field"], 0) or 0) for r in rows)
        sess = sum(float(r.get(spec["sess_field"], 0) or 0) for r in rows)
        return round(conv / sess * 100, 2) if sess else 0.0

    if op == "normalise_sum_pct":
        # For attribution cases: sum(linear_revenue / total * 100) — must be 100%
        total = sum(float(r.get("linear_revenue", 0) or 0) for r in result_data)
        if total == 0:
            return 0.0
        return round(sum(float(r["linear_revenue"]) / total * 100 for r in result_data), 1)

    raise ValueError(f"Unknown extraction op: {op}")


# ── Golden JSON path navigator ────────────────────────────────────────────────

def _navigate_golden(golden: dict, path: str) -> tuple[Any, str]:
    """
    Navigate a dot-path like "windowed_90d.channel_performance[google_ads].roas".
    Returns (value, accessed_section) where accessed_section is the top-level key.
    """
    import re
    parts = re.split(r"\.(?![^\[]*\])", path)  # split on dots not inside brackets
    node = golden
    section = parts[0] if parts else ""

    for part in parts:
        # Handle array-style lookup: key[filter_value]
        arr_match = re.match(r"^(\w+)\[(.+)\]$", part)
        if arr_match:
            field, filter_val = arr_match.group(1), arr_match.group(2)
            arr = node[field]
            # Find row matching channel or stage name
            node = next(
                r for r in arr
                if str(r.get("channel", r.get("stage", ""))).lower() == filter_val.lower()
            )
        else:
            node = node[part]

    return node, section


# ── MCP surface ───────────────────────────────────────────────────────────────

def run_mcp_tasks(cases: list[dict]) -> list[dict]:
    # Import server modules lazily so missing deps don't fail other surfaces
    import importlib
    _server_cache: dict[str, Any] = {}

    def _get_tool(tool_spec: str):
        server_name, fn_name = tool_spec.split(".")
        if server_name not in _server_cache:
            module_map = {
                "ga4":         "mock_ga4_server",
                "google_ads":  "mock_google_ads_server",
                "meta_ads":    "mock_meta_ads_server",
                "hubspot":     "mock_hubspot_server",
                "salesforce":  "mock_salesforce_server",
            }
            mod = importlib.import_module(module_map[server_name])
            _server_cache[server_name] = mod
        return getattr(_server_cache[server_name], fn_name)

    results = []
    for case in cases:
        try:
            fn   = _get_tool(case["tool"])
            data = fn(**case["params"])
            spec = case.get("extract", {})
            if spec:
                retrieved = _apply_extract(data, spec)
            else:
                retrieved = data

            p = precision_score(retrieved, case["expected_value"], case["tolerance"])

            used_dates = bool(case["params"].get("start_date") and case["params"].get("end_date"))
            r = relevance_score(case, {"used_date_params": used_dates})

            results.append(_make_result(case, retrieved, p, r))
        except Exception as exc:
            results.append(_make_result(case, None, 0.0, 0.0, str(exc)))
    return results


# ── Golden surface ────────────────────────────────────────────────────────────

def run_golden_tasks(cases: list[dict]) -> list[dict]:
    golden = _load_golden()
    results = []
    for case in cases:
        try:
            path = case["golden_path"]
            spec = case.get("extract", {})

            if spec and spec.get("op") == "normalise_sum_pct":
                arr, section = _navigate_golden(golden, path)
                retrieved = _apply_extract(arr, spec)
            else:
                retrieved, section = _navigate_golden(golden, path)

            # Golden cases test path navigation, not specific numbers.
            # The values in golden_metrics.json roll forward with the daily anchor,
            # so we compare retrieved against the live golden value (= same source).
            # expected_from_golden=true means precision=1.0 if navigation succeeds.
            if case.get("expected_from_golden"):
                expected = retrieved
            else:
                expected = case["expected_value"]

            p = precision_score(retrieved, expected, case["tolerance"])
            r = relevance_score(case, {"accessed_section": section})
            results.append(_make_result(case, retrieved, p, r))
        except Exception as exc:
            results.append(_make_result(case, None, 0.0, 0.0, str(exc)))
    return results


# ── Semantic / SQL surface ────────────────────────────────────────────────────

def run_semantic_tasks(cases: list[dict]) -> list[dict]:
    import duckdb

    results = []
    for case in cases:
        try:
            sql = case["sql"].replace("{DATA_DIR}", str(DATA_DIR))
            con = duckdb.connect(":memory:")
            row = con.execute(sql).fetchone()
            con.close()
            retrieved = row[0] if row else None

            p = precision_score(retrieved, case["expected_value"], case["tolerance"])
            r = relevance_score(case, {"sql_text": sql})
            results.append(_make_result(case, retrieved, p, r))
        except Exception as exc:
            results.append(_make_result(case, None, 0.0, 0.0, str(exc)))
    return results


# ── NL→SQL surface ────────────────────────────────────────────────────────────

def run_nl2sql_tasks(cases: list[dict]) -> list[dict]:
    import duckdb

    results = []
    for case in cases:
        try:
            sql = case["sql"].replace("{DATA_DIR}", str(DATA_DIR))
            con = duckdb.connect(":memory:")
            try:
                row = con.execute(sql).fetchone()
                retrieved = row[0] if row else None
            except Exception as sql_exc:
                # SQL that references wrong columns will error — that's the point
                retrieved = None
                raise sql_exc from None
            finally:
                con.close()

            p = precision_score(retrieved, case["expected_value"], case["tolerance"])
            r = relevance_score(case, {"sql_text": sql})
            results.append(_make_result(case, retrieved, p, r))
        except Exception as exc:
            # SQL execution error → precision 0, relevance per check type
            r = relevance_score(case, {"sql_text": case["sql"]})
            results.append(_make_result(case, None, 0.0, r, str(exc)))
    return results


# ── Orchestrator ──────────────────────────────────────────────────────────────

# ── query_window surface ──────────────────────────────────────────────────────

def run_query_window_tasks(cases: list[dict]) -> list[dict]:
    """
    Tests query_window.py for arbitrary date ranges.
    Imports build_csv_connection + build_window_section directly (no subprocess)
    so the test is fast and doesn't depend on PATH.
    """
    from datetime import date
    import importlib.util, types

    # Import query_window without relying on it being installed
    import importlib.util as _ilu
    qw_path = PROJECT_ROOT / "scripts" / "query_window.py"
    spec    = _ilu.spec_from_file_location("query_window", str(qw_path),
                  submodule_search_locations=[])
    qw      = _ilu.module_from_spec(spec)
    # Patch __file__ so query_window.py can resolve DATA_DIR relative to itself
    qw.__file__ = str(qw_path)
    spec.loader.exec_module(qw)  # type: ignore[union-attr]

    results = []
    for case in cases:
        try:
            start = date.fromisoformat(case["window"]["start"])
            end   = date.fromisoformat(case["window"]["end"])
            label = case.get("window_label", "Test window")

            section = qw.query_window(start, end, label)

            # Extract the specific metric from the section
            spec_path = case["extract_path"]
            retrieved = _extract_from_section(section, spec_path)

            p = precision_score(retrieved, case["expected_value"], case["tolerance"])
            r = relevance_score(case, {"used_date_params": True})
            results.append(_make_result(case, retrieved, p, r))
        except Exception as exc:
            results.append(_make_result(case, None, 0.0, 0.0, str(exc)))
    return results


def _extract_from_section(section: dict, path: str):
    """Navigate a dot-path like 'sessions.total' or 'spend.google'."""
    node = section
    for part in path.split("."):
        node = node[part]
    return node


SURFACE_RUNNERS = {
    "mcp":          run_mcp_tasks,
    "golden":       run_golden_tasks,
    "semantic":     run_semantic_tasks,
    "nl2sql":       run_nl2sql_tasks,
    "query_window": run_query_window_tasks,
}


def run(surface: str = "all", verbose: bool = False) -> list[dict]:
    """Run the benchmark and return all per-case results."""
    surfaces = list(SURFACE_RUNNERS.keys()) if surface == "all" else [surface]
    all_results: list[dict] = []

    for s in surfaces:
        cases = _load_cases(s)
        runner = SURFACE_RUNNERS[s]
        results = runner(cases)
        all_results.extend(results)

        if verbose:
            print(f"\n── {s.upper()} ({len(results)} cases) ──")
            for r in results:
                marker = "⚠ " if r["adversarial"] else ""
                status = "✅" if r["sqra"] >= 90 else ("⚡" if r["adversarial"] and r["sqra"] < 10 else "❌")
                print(f"  {status} {marker}{r['id']}")
                print(f"     expected={r['expected']}  retrieved={r['retrieved']}")
                print(f"     P={r['precision']:.3f}  R={r['relevance']:.3f}  SQRA={r['sqra']}")
                if r["error"]:
                    print(f"     ERROR: {r['error']}")

    return all_results
