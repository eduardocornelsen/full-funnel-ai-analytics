"""First-boot warehouse bootstrap — makes hosted deploys (Streamlit Cloud) work.

The DuckDB file and Olist raw data are never committed (by design), so a fresh
deploy has only the frozen baseline CSVs + code. Historically that meant
Streamlit Cloud crashed on first query. This module builds everything the app
needs, once, at startup:

    CSVs missing?      → generate standalone synthetic baseline (no credentials)
    data behind today? → deterministic catch-up append
    DuckDB missing?    → load CSVs + dbt run
    golden missing?    → generate golden_metrics.json

Idempotent: on a machine that already ran `fullfunnel demo`, this is a no-op.
Kept free of Streamlit imports so it's unit-testable; the app wraps it in
st.cache_resource + a status spinner.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH      = PROJECT_ROOT / "data" / "olist_analytics.duckdb"
GOLDEN_PATH  = PROJECT_ROOT / "dashboards" / "golden_metrics.json"
LEAD_CSV     = PROJECT_ROOT / "data" / "mock_marketing" / "google_ads_daily_performance.csv"


def _run(cmd: list[str], step: str, cwd: Path | None = None) -> None:
    result = subprocess.run(cmd, cwd=cwd or PROJECT_ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Bootstrap step failed — {step}:\n{result.stdout[-2000:]}\n{result.stderr[-2000:]}")


def needs_bootstrap() -> bool:
    return not (DB_PATH.exists() and GOLDEN_PATH.exists())


def ensure_warehouse(progress=print) -> bool:
    """Build the warehouse + golden artifact if absent. Returns True if work ran.

    `progress` is called with human-readable step names (the app passes a
    Streamlit status writer; tests pass a collector).
    """
    if not needs_bootstrap():
        return False

    if not LEAD_CSV.exists():
        progress("Generating standalone synthetic dataset (no credentials needed)…")
        _run([sys.executable, "scripts/generate_mock_marketing_data.py", "--standalone"],
             "generate baseline")

    progress("Catching synthetic data up to today (deterministic)…")
    _run([sys.executable, "scripts/daily_synthetic_append.py"], "catch-up append")

    progress("Loading CSVs into DuckDB…")
    _run([sys.executable, "scripts/load_duckdb.py"], "load DuckDB")

    progress("Building dbt models…")
    _run(["dbt", "deps"], "dbt deps", cwd=PROJECT_ROOT / "dbt_project")
    _run(["dbt", "run", "--target", "duckdb"], "dbt run", cwd=PROJECT_ROOT / "dbt_project")

    progress("Generating golden metrics…")
    # --skip-semantic-check: bootstrap optimizes for availability on constrained
    # hosts; the MetricFlow cross-check is enforced in CI and the daily refresh.
    _run([sys.executable, "scripts/generate_golden_metrics.py", "--skip-semantic-check"],
         "generate golden metrics")

    progress("Warehouse ready.")
    return True
