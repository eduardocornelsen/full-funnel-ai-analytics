"""fullfunnel — the project CLI.

One command per pipeline stage, wrapping the repo's scripts and dbt project so
nobody has to memorize the six-step incantation from the README:

    fullfunnel init       write local config (dbt profiles) for a fresh clone
    fullfunnel demo       zero-credential path: synthetic data → DuckDB → dbt →
                          golden metrics → validation (add --serve for Streamlit)
    fullfunnel append     advance the synthetic feed (default: catch up to today)
    fullfunnel refresh    what the daily cron does: append + rebuild + validate
    fullfunnel validate   drift + staleness gates against the warehouse
    fullfunnel bench      run the SQRA retrieval-accuracy benchmark

The CLI operates on a repo checkout (editable install: `pip install -e .`).
It locates the repo root by walking up from the current directory, so it works
from any subdirectory of the clone.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def find_root(start: Path | None = None) -> Path:
    """Walk up from `start` (default: cwd) to the repo root.

    The root is identified by dbt_project/dbt_project.yml — the one marker
    every pipeline stage needs.
    """
    cur = (start or Path.cwd()).resolve()
    for candidate in [cur, *cur.parents]:
        if (candidate / "dbt_project" / "dbt_project.yml").exists():
            return candidate
    sys.exit(
        "fullfunnel: not inside a full-funnel-ai-analytics checkout "
        "(no dbt_project/dbt_project.yml found in any parent directory).\n"
        "Clone the repo and run from inside it: "
        "git clone https://github.com/eduardocornelsen/full-funnel-ai-analytics"
    )


def run(cmd: list[str], cwd: Path, step: str) -> None:
    print(f"\n━━ {step} ━━")
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0:
        sys.exit(f"fullfunnel: step failed — {step} (exit {result.returncode})")


def script(root: Path, name: str, *args: str) -> list[str]:
    return [sys.executable, str(root / "scripts" / name), *args]


# The seven time-series CSVs the pipeline needs — mirrors the registry in
# scripts/daily_synthetic_append.py. If ANY is missing, the baseline must be
# regenerated (the append script backfills existing series; it can't create one).
DATA_FILES = [
    "google_ads_daily_performance.csv",
    "meta_ads_daily_performance.csv",
    "ga4_daily_sessions.csv",
    "marketing_attribution.csv",
    "hubspot_deals.csv",
    "hubspot_contacts.csv",
    "salesforce_opportunities.csv",
]


def ensure_profiles(root: Path) -> None:
    profiles = root / "dbt_project" / "profiles.yml"
    if not profiles.exists():
        example = root / "dbt_project" / "profiles.yml.example"
        if not example.exists():
            sys.exit(f"fullfunnel: {example.relative_to(root)} not found — is this a complete checkout?")
        profiles.write_text(example.read_text())
        print(f"Wrote {profiles.relative_to(root)} from example (DuckDB default)")


def cmd_init(root: Path, _: argparse.Namespace) -> None:
    ensure_profiles(root)
    print(
        "\nMCP clients:\n"
        "  Claude Code    — ready: the repo's .mcp.json uses relative paths\n"
        "  Claude Desktop — copy mcp_servers/claude_desktop_config.example.json into your\n"
        "                   Desktop config and replace /ABSOLUTE/PATH/TO/ with this directory\n"
        f"                   ({root})\n"
        "\nNext: fullfunnel demo"
    )


def cmd_demo(root: Path, args: argparse.Namespace) -> None:
    mock_dir = root / "data" / "mock_marketing"
    if any(not (mock_dir / f).exists() for f in DATA_FILES):
        run(script(root, "generate_mock_marketing_data.py", "--standalone"),
            root, "Generate standalone synthetic dataset (no credentials needed)")
    run(script(root, "daily_synthetic_append.py"), root, "Catch synthetic data up to today")
    _rebuild_and_validate(root)
    print(
        "\n✅ Demo ready: dashboards/golden_metrics.json is fresh and validated.\n"
        "   Ask an AI client `/marketing`, or open the HTML dashboards, or:"
    )
    if args.serve:
        run([sys.executable, "-m", "streamlit", "run", "streamlit_app/app.py"],
            root, "Launch Streamlit app")
    else:
        print("   streamlit run streamlit_app/app.py   (or re-run with --serve)")


def cmd_append(root: Path, args: argparse.Namespace) -> None:
    extra = ["--days", str(args.days)] if args.days is not None else []
    run(script(root, "daily_synthetic_append.py", *extra), root, "Append synthetic data")


def cmd_refresh(root: Path, args: argparse.Namespace) -> None:
    run(script(root, "daily_synthetic_append.py"), root, "Catch synthetic data up to today")
    _rebuild_and_validate(root, strict=True)


def cmd_validate(root: Path, args: argparse.Namespace) -> None:
    extra = ["--target", args.target] + (["--strict-freshness"] if args.strict else [])
    run(script(root, "validate_metrics.py", *extra), root, "Validate golden layer")


def cmd_bench(root: Path, args: argparse.Namespace) -> None:
    extra = ["--min-score", str(args.min_score)] if args.min_score is not None else []
    run(script(root, "run_sqra.py", *extra), root, "SQRA benchmark")


def _rebuild_and_validate(root: Path, strict: bool = False) -> None:
    ensure_profiles(root)
    dbt_dir = root / "dbt_project"
    run(script(root, "load_duckdb.py"), root, "Load CSVs into DuckDB")
    run(["dbt", "deps"], dbt_dir, "dbt deps")
    run(["dbt", "run", "--target", "duckdb"], dbt_dir, "dbt run")
    run(["dbt", "test", "--target", "duckdb"], dbt_dir, "dbt test")
    run(script(root, "generate_golden_metrics.py"), root, "Generate golden metrics")
    validate_args = ["--strict-freshness"] if strict else []
    run(script(root, "validate_metrics.py", *validate_args), root,
        "Validate golden layer (drift + staleness)")


def main() -> None:
    parser = argparse.ArgumentParser(prog="fullfunnel", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="write local config for a fresh clone")

    p_demo = sub.add_parser("demo", help="zero-credential demo: data → dbt → golden → validate")
    p_demo.add_argument("--serve", action="store_true", help="launch the Streamlit app at the end")

    p_append = sub.add_parser("append", help="advance the synthetic feed (default: to today)")
    p_append.add_argument("--days", type=int, default=None,
                          help="append exactly N days past the frontier instead")

    sub.add_parser("refresh", help="append + rebuild + strict validation (the daily cron)")

    p_val = sub.add_parser("validate", help="drift + staleness gates")
    p_val.add_argument("--target", default="duckdb", choices=["duckdb", "bigquery", "snowflake"])
    p_val.add_argument("--strict", action="store_true", help="fail if data trails today")

    p_bench = sub.add_parser("bench", help="run the SQRA benchmark")
    p_bench.add_argument("--min-score", type=float, default=None,
                         help="exit non-zero if the overall score is below this")

    args = parser.parse_args()
    root = find_root()
    {
        "init":     cmd_init,
        "demo":     cmd_demo,
        "append":   cmd_append,
        "refresh":  cmd_refresh,
        "validate": cmd_validate,
        "bench":    cmd_bench,
    }[args.command](root, args)


if __name__ == "__main__":
    main()
