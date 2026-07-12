"""
run_sqra.py
─────────────────────────────────────────────────────────────────────────────
CLI entry point for the SQRA (Search Quality & Retrieval Accuracy) benchmark.

Usage:
    python scripts/run_sqra.py                          # all surfaces
    python scripts/run_sqra.py --surface mcp            # single surface
    python scripts/run_sqra.py --surface nl2sql --verbose
    python scripts/run_sqra.py --output sqra_report.json
    python scripts/run_sqra.py --min-score 90           # CI gate (exit 1 if below)

Exit codes:
    0  SQRA >= min_score (or no threshold set)
    1  SQRA < min_score
    2  Benchmark error (missing golden_metrics.json, etc.)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "tests" / "benchmark"))

from run_benchmark import run  # noqa: E402
from scorer import aggregate   # noqa: E402


# ── Report formatting ─────────────────────────────────────────────────────────

SURFACE_LABEL = {
    "mcp":          "MCP Tool Queries   ",
    "golden":       "Golden Layer Reads ",
    "semantic":     "dbt Semantic Layer ",
    "nl2sql":       "NL → SQL Fidelity  ",
    "query_window": "query_window.py    ",
}

def _render_report(results: list[dict], summary: dict) -> str:
    lines = []
    lines.append("╔══════════════════════════════════════════════════════════════╗")
    lines.append("║   SQRA — Search Quality & Retrieval Accuracy Index           ║")
    n_total = summary["case_count"]
    n_canon = summary["non_adversarial_count"]
    lines.append(f"║   Cases: {n_total:2d} ({n_canon} canonical + {summary['adversarial_total']} adversarial)            ║")
    lines.append(f"║   Canonical pass rate (≥90): {summary['pass_rate']:5.1f}%                     ║")
    lines.append("╠══════════════════════════════════════════════════════════════╣")
    lines.append("║  Surface               Precision   Relevance    SQRA        ║")
    lines.append("║  ───────────────────   ─────────   ─────────    ────        ║")

    for surface, sqra_val in summary["by_surface"].items():
        label = SURFACE_LABEL.get(surface, surface.ljust(19))
        # Canonical (non-adversarial) rows only for per-surface P/R
        surf_results = [r for r in results if r["surface"] == surface and not r.get("adversarial")]
        if not surf_results:
            continue
        prec = sum(r["precision"] for r in surf_results) / len(surf_results) * 100
        relv = sum(r["relevance"] for r in surf_results) / len(surf_results) * 100
        lines.append(f"║  {label}   {prec:6.1f}%     {relv:6.1f}%     {sqra_val:5.1f}     ║")

    lines.append("║  ───────────────────   ─────────   ─────────    ────        ║")
    overall = summary["overall"]
    lines.append(f"║  Overall SQRA Index (canonical)                 {overall:5.1f}     ║")
    lines.append("╚══════════════════════════════════════════════════════════════╝")

    # Adversarial detection callout
    if summary["adversarial_total"] > 0:
        det = summary["adversarial_detected"]
        tot = summary["adversarial_total"]
        rate = summary["adversarial_detected_rate"]
        symbol = "✅" if det == tot else "⚠"
        lines.append(f"\n{symbol} Adversarial detection: {det}/{tot} flawed queries caught "
                     f"(SQRA < 10) — {rate:.0f}% detection rate")

    # Failures (non-adversarial with SQRA < 90)
    failures = [r for r in results if not r.get("adversarial") and r["sqra"] < 90]
    if failures:
        lines.append(f"\n❌ {len(failures)} canonical case(s) below SQRA 90:")
        for r in failures:
            lines.append(f"   • {r['id']}")
            lines.append(f"     expected={r['expected']}  retrieved={r['retrieved']}")
            lines.append(f"     P={r['precision']:.3f}  R={r['relevance']:.3f}  SQRA={r['sqra']}")
            if r["error"]:
                lines.append(f"     ERROR: {r['error']}")

    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the SQRA search quality & retrieval accuracy benchmark."
    )
    parser.add_argument(
        "--surface",
        default="all",
        choices=["all", "mcp", "golden", "semantic", "nl2sql", "query_window"],
        help="Retrieval surface to benchmark (default: all)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print per-case detail during the run",
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        help="Write machine-readable JSON report to FILE",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=None,
        metavar="N",
        help="Exit code 1 if overall SQRA < N (use for CI gate, e.g. --min-score 90)",
    )
    parser.add_argument(
        "--agents",
        action="store_true",
        help="Run the model-in-the-loop benchmark: three agent architectures "
             "(golden-tools / raw-sql / semantic-layer) answer the same NL "
             "questions; numeric fidelity + token cost. Needs ANTHROPIC_API_KEY.",
    )
    parser.add_argument("--model", default=None,
                        help="Model for --agents (default: claude-haiku-4-5-20251001)")
    parser.add_argument("--limit", type=int, default=None,
                        help="Max questions per architecture for --agents")
    parser.add_argument("--arch", action="append", default=None,
                        choices=["golden-tools", "raw-sql", "semantic-layer"],
                        help="Restrict --agents to specific architecture(s); repeatable")

    args = parser.parse_args()

    if args.agents:
        from agent_benchmark import DEFAULT_MODEL, run_agents
        report = run_agents(model=args.model or DEFAULT_MODEL,
                            limit=args.limit, architectures=args.arch)
        print(f"\n══ SQRA Agent Benchmark · {report['model']} · "
              f"{report['question_count']} questions ══")
        print(f"{'architecture':<16}{'accuracy':>10}{'mean prec':>11}{'tokens/q':>10}")
        for name, a in report["architectures"].items():
            print(f"{name:<16}{a['accuracy_pct']:>9.1f}%{a['mean_precision']:>11.3f}"
                  f"{a['tokens_per_question']:>10}")
        out = Path(args.output) if args.output else (
            PROJECT_ROOT / "tests" / "benchmark" / f"agent_results_{report['model']}.json")
        out.write_text(json.dumps(report, indent=2))
        print(f"\nReport written to: {out}")
        return 0

    golden_path = PROJECT_ROOT / "dashboards" / "golden_metrics.json"
    if not golden_path.exists():
        print("❌ golden_metrics.json not found. Run:")
        print("   python scripts/generate_golden_metrics.py --target duckdb")
        return 2

    print(f"Running SQRA benchmark — surface: {args.surface} …\n")

    try:
        results = run(surface=args.surface, verbose=args.verbose)
    except Exception as exc:
        print(f"❌ Benchmark error: {exc}")
        return 2

    summary = aggregate(results)

    print(_render_report(results, summary))

    if args.output:
        report = {
            "summary": summary,
            "cases": results,
        }
        Path(args.output).write_text(json.dumps(report, indent=2))
        print(f"\nReport written to: {args.output}")

    if args.min_score is not None:
        if summary["overall"] < args.min_score:
            print(f"\n❌ SQRA {summary['overall']} < threshold {args.min_score} — CI gate FAILED")
            return 1
        print(f"\n✅ SQRA {summary['overall']} ≥ threshold {args.min_score} — CI gate PASSED")

    return 0


if __name__ == "__main__":
    sys.exit(main())
