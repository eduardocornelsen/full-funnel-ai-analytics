"""
validate_metrics.py
───────────────────────────────────────────────────────────────────────────────
Validates that dashboards/golden_metrics.json is in sync with the live
golden layer. Detects metric drift AND staleness.

Drift and staleness are different failure modes and both must be gated:
  - Drift:     golden values diverge from the warehouse for the same window.
  - Staleness: golden and warehouse agree perfectly — on months-old data.
    (2026-07 postmortem: a frozen mart kept this validator green for ~3 months
    while raw CSVs grew daily. Divergence checks alone cannot see that.)

Usage:
    python scripts/validate_metrics.py                    # DuckDB (default)
    python scripts/validate_metrics.py --target bigquery
    python scripts/validate_metrics.py --target snowflake

Returns:
    Exit code 0 — no drift, golden layer fresh
    Exit code 1 — drift or staleness found (details printed)

Run before generating any new dashboard, or in CI after dbt run.
"""

import argparse
import sys
from datetime import date
from pathlib import Path
import json

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from _warehouse_adapters import get_connection  # noqa: E402

PROJECT_ROOT = Path(__file__).parent.parent
GOLDEN_PATH  = PROJECT_ROOT / "dashboards" / "golden_metrics.json"
MOCK_DIR     = PROJECT_ROOT / "data" / "mock_marketing"

# Every time-series table and its date column — mirrors the registry in
# daily_synthetic_append.py. Freshness must be checked per table: the original
# staleness bug advanced 3 tables while 4 stayed frozen, and a single-table
# frontier check would have stayed green through it.
RAW_TABLES = [
    ("google_ads_daily_performance.csv", "date"),
    ("meta_ads_daily_performance.csv",   "date"),
    ("ga4_daily_sessions.csv",           "date"),
    ("marketing_attribution.csv",        "order_date"),
    ("hubspot_deals.csv",                "create_date"),
    ("hubspot_contacts.csv",             "create_date"),
    ("salesforce_opportunities.csv",     "created_date"),
]

DOLLAR_TOLERANCE_ABS = 1.00
RATIO_TOLERANCE_PCT  = 0.50
COUNT_TOLERANCE_ABS  = 1
ANCHOR_LAG_TOLERANCE_DAYS = 1   # anchor may trail the raw data frontier by at most this
TABLE_SKEW_TOLERANCE_DAYS = 2   # any table may trail the most-advanced table by at most this
WALL_CLOCK_TOLERANCE_DAYS = 3   # raw frontier may trail today by at most this (strict mode)


def check_freshness(meta: dict, strict: bool = False) -> list[str]:
    """Return a list of staleness errors (empty = fresh).

    Three orthogonal checks:
    1. Anchor vs RAW data frontier (always enforced) — catches a frozen mart or
       stale golden snapshot. Compares against the raw CSVs, not the mart,
       because the mart can itself be frozen (that was the bug).
    2. Cross-table skew (always enforced) — every table's frontier must be
       within tolerance of the most-advanced table's. Catches a partial append
       (spend advancing while attribution revenue / CRM stay frozen), which
       silently deflates blended ROAS in recent windows.
    3. Raw frontier vs today's wall clock (warn by default, error with
       --strict-freshness) — catches the append automation being down entirely.
       Warn-only by default so a fresh clone or a fork PR with slightly older
       committed data doesn't fail; the scheduled refresh runs strict.
    """
    errors: list[str] = []
    anchor = date.fromisoformat(meta["anchor_date"])

    frontiers: dict[str, date] = {}
    for filename, col in RAW_TABLES:
        path = MOCK_DIR / filename
        if not path.exists():
            continue
        s = pd.to_datetime(pd.read_csv(path, usecols=[col])[col], errors="coerce")
        if s.notna().any():
            frontiers[filename] = s.max().date()

    if not frontiers:
        msg = "no raw CSVs found locally — freshness cannot be verified"
        if strict:
            errors.append(f"STALE (unverifiable): {msg}; --strict-freshness requires the raw data")
        else:
            print(f"⚠️  Freshness: {msg} — skipping")
        return errors

    lead = max(frontiers.values())

    # 1. Golden anchor must track the raw frontier
    lag = (lead - anchor).days
    if lag > ANCHOR_LAG_TOLERANCE_DAYS:
        errors.append(
            f"STALE: golden anchor_date {anchor} lags raw data frontier {lead} "
            f"by {lag} days (tolerance: {ANCHOR_LAG_TOLERANCE_DAYS}). "
            f"The mart or the golden snapshot is not rolling forward. "
            f"Fix the pipeline, then: dbt run && python scripts/generate_golden_metrics.py"
        )
    else:
        print(f"Freshness: anchor {anchor} vs raw frontier {lead} (lag {lag}d) ✅")

    # 2. No table may fall behind the pack
    laggards = {f: fr for f, fr in frontiers.items()
                if (lead - fr).days > TABLE_SKEW_TOLERANCE_DAYS}
    if laggards:
        detail = ", ".join(f"{f} at {fr} (-{(lead - fr).days}d)" for f, fr in laggards.items())
        errors.append(
            f"STALE (partial append): tables lag the {lead} frontier beyond "
            f"{TABLE_SKEW_TOLERANCE_DAYS}d tolerance: {detail}. "
            f"Heal with: python scripts/daily_synthetic_append.py"
        )
    else:
        print(f"Freshness: all {len(frontiers)} tables within {TABLE_SKEW_TOLERANCE_DAYS}d of frontier ✅")

    # 3. The frontier itself must track the wall clock (strict mode hard-fails)
    clock_lag = (date.today() - lead).days
    if clock_lag > WALL_CLOCK_TOLERANCE_DAYS:
        msg = (
            f"Raw data frontier {lead} trails today by {clock_lag} days "
            f"(tolerance: {WALL_CLOCK_TOLERANCE_DAYS}) — is the daily append "
            f"automation running? Catch up with: python scripts/daily_synthetic_append.py"
        )
        if strict:
            errors.append("STALE (wall clock): " + msg)
        else:
            print(f"⚠️  {msg}")
    else:
        print(f"Freshness: raw frontier {lead} vs today (lag {clock_lag}d) ✅")

    return errors


def load_golden() -> dict:
    if not GOLDEN_PATH.exists():
        print(f"❌ golden_metrics.json not found at {GOLDEN_PATH}")
        print("   Run: python scripts/generate_golden_metrics.py")
        sys.exit(1)
    return json.loads(GOLDEN_PATH.read_text())


def check(name: str, golden_val: float, live_val: float,
          tolerance: float, tolerance_type: str = "abs") -> dict:
    if tolerance_type == "pct":
        diff_pct = abs(golden_val - live_val) / max(abs(golden_val), 1e-9) * 100
        drifted = diff_pct > tolerance
        diff_str = f"{diff_pct:.4f}%"
    else:
        diff_abs = abs(golden_val - live_val)
        drifted = diff_abs > tolerance
        diff_str = f"{diff_abs:.4f}"
    return {"metric": name, "golden": golden_val, "live": live_val,
            "diff": diff_str, "drifted": drifted}


def validate_completed_months(target: str = "duckdb") -> int:
    """Spot-check the COMMITTED golden artifact against the warehouse.

    Regular validation runs after the generator, so it checks a freshly
    generated artifact — the committed file itself is only validated at the
    moment the scheduled refresh writes it. This mode closes that gap for PR
    CI: completed calendar months are anchor-independent (identical no matter
    which day generated them), so the committed file's full-month sections
    must match a warehouse rebuilt on any later day. Run BEFORE regenerating
    golden_metrics.json in the workspace.

    Deliberately skips freshness gates and CRM/all-time values: the committed
    anchor legitimately trails a CI runner's regenerated frontier, and CRM
    sections are lifetime-scoped, not month-scoped.
    """
    golden = load_golden()
    months = {k: v for k, v in golden.items()
              if k.startswith("month_") and "(full month)" in v.get("label", "")}
    if not months:
        print("No completed-month sections in golden_metrics.json — nothing to spot-check.")
        return 0

    con = get_connection(target)
    checks = []
    for key, sec in sorted(months.items()):
        ws, we = sec["window"]["start"], sec["window"]["end"]
        live = con.execute("""
            SELECT SUM(total_google_spend), SUM(total_meta_spend), SUM(total_spend),
                   SUM(total_conversions),  SUM(ga4_total_sessions)
            FROM fct_marketing_daily
            WHERE date BETWEEN ? AND ?
        """, [ws, we]).fetchone()
        live_rev = con.execute(
            "SELECT SUM(linear_credit * order_revenue) FROM stg_marketing_attribution"
            " WHERE touchpoint_date BETWEEN ? AND ?", [ws, we]
        ).fetchone()[0]
        live_roas = round(float(live_rev or 0) / float(live[2] or 1), 2)
        checks += [
            check(f"{key}.spend.google",          sec["spend"]["google"],            float(live[0] or 0), DOLLAR_TOLERANCE_ABS),
            check(f"{key}.spend.meta",            sec["spend"]["meta"],              float(live[1] or 0), DOLLAR_TOLERANCE_ABS),
            check(f"{key}.spend.total",           sec["spend"]["total"],             float(live[2] or 0), DOLLAR_TOLERANCE_ABS),
            check(f"{key}.conversions.ga4_total", sec["conversions"]["ga4_total"],   float(live[3] or 0), COUNT_TOLERANCE_ABS),
            check(f"{key}.sessions.total",        sec["sessions"]["total"],          float(live[4] or 0), COUNT_TOLERANCE_ABS),
            check(f"{key}.blended_roas",          sec["blended_roas"],               live_roas,           RATIO_TOLERANCE_PCT, "pct"),
        ]
    con.close()

    drifted = [c for c in checks if c["drifted"]]
    print(f"Committed-artifact spot check ({len(months)} completed months): "
          f"{len(checks)} checks, ❌ {len(drifted)} drifted")
    if drifted:
        print("\nThe COMMITTED golden_metrics.json disagrees with a warehouse rebuilt "
              "from this checkout. Either this PR changed metric logic without "
              "regenerating the artifact (fix: python scripts/generate_golden_metrics.py, "
              "commit the result in the same PR) or generation is no longer deterministic "
              "(see tests/test_determinism.py).")
        for c in drifted:
            print(f"  ❌ {c['metric']}: golden={c['golden']}  live={c['live']}  diff={c['diff']}")
        return 1
    print("✅ Committed golden artifact matches the regenerated warehouse.")
    return 0


def validate(target: str = "duckdb", strict_freshness: bool = False) -> int:
    golden = load_golden()
    meta   = golden["_meta"]

    print(f"Golden file generated: {meta['generated_at']}")
    print(f"Anchor date: {meta['anchor_date']}  |  Window: {meta['window_start']} → {meta['window_end']}")

    # Staleness gate first — a perfectly consistent but frozen golden layer
    # must fail loudly before any drift comparison runs.
    staleness_errors = check_freshness(meta, strict=strict_freshness)
    if staleness_errors:
        for e in staleness_errors:
            print(f"\n❌ {e}")
        return 1

    print(f"Connecting to: {target}\n")

    con    = get_connection(target)
    checks = []

    g_at = golden["all_time"]
    ws   = meta["window_start"]
    we   = meta["window_end"]
    ds   = meta["dataset_start"]
    de   = meta["dataset_end"]

    # ── All-time totals (bounded to the dataset window that generated the golden) ─
    live = con.execute("""
        SELECT
            SUM(total_google_spend), SUM(total_meta_spend), SUM(total_spend),
            SUM(total_conversions),  SUM(ga4_total_sessions)
        FROM fct_marketing_daily
        WHERE date BETWEEN ? AND ?
    """, [ds, de]).fetchone()

    checks += [
        check("all_time.spend.google",          g_at["spend"]["google"],            float(live[0] or 0), DOLLAR_TOLERANCE_ABS),
        check("all_time.spend.meta",            g_at["spend"]["meta"],              float(live[1] or 0), DOLLAR_TOLERANCE_ABS),
        check("all_time.spend.total",           g_at["spend"]["total"],             float(live[2] or 0), DOLLAR_TOLERANCE_ABS),
        check("all_time.conversions.ga4_total", g_at["conversions"]["ga4_total"],   float(live[3] or 0), COUNT_TOLERANCE_ABS),
        check("all_time.sessions.total",        g_at["sessions"]["total"],          float(live[4] or 0), COUNT_TOLERANCE_ABS),
    ]

    # Blended ROAS (all-time): linear attributed revenue / total spend
    live_rev_at = con.execute(
        "SELECT SUM(linear_credit * order_revenue) FROM stg_marketing_attribution"
        " WHERE touchpoint_date BETWEEN ? AND ?",
        [ds, de]
    ).fetchone()[0]
    live_roas = round(float(live_rev_at or 0) / float(live[2] or 1), 2)
    checks.append(check("all_time.blended_roas", g_at["blended_roas"], live_roas, RATIO_TOLERANCE_PCT, "pct"))

    # CRM all-time
    live_contacts = con.execute("SELECT COUNT(*) FROM stg_hubspot_contacts").fetchone()[0]
    checks.append(check("crm.hubspot.total_contacts",
                        g_at["crm"]["hubspot"]["total_contacts"], float(live_contacts), COUNT_TOLERANCE_ABS))

    live_sf_won = con.execute(
        "SELECT SUM(amount) FROM stg_salesforce_opportunities WHERE is_won=TRUE"
    ).fetchone()[0]
    checks.append(check("crm.salesforce.closed_won_revenue",
                        g_at["crm"]["salesforce"]["closed_won_revenue"],
                        float(live_sf_won or 0), DOLLAR_TOLERANCE_ABS))

    # ── 90-day window ──────────────────────────────────────────────────────────
    g_90    = golden["windowed_90d"]
    live_90 = con.execute("""
        SELECT
            SUM(total_google_spend), SUM(total_meta_spend), SUM(total_spend),
            SUM(total_conversions),  SUM(ga4_total_sessions)
        FROM fct_marketing_daily
        WHERE date BETWEEN ? AND ?
    """, [ws, we]).fetchone()

    checks += [
        check("90d.spend.google",          g_90["spend"]["google"],          float(live_90[0] or 0), DOLLAR_TOLERANCE_ABS),
        check("90d.spend.meta",            g_90["spend"]["meta"],            float(live_90[1] or 0), DOLLAR_TOLERANCE_ABS),
        check("90d.spend.total",           g_90["spend"]["total"],           float(live_90[2] or 0), DOLLAR_TOLERANCE_ABS),
        check("90d.conversions.ga4_total", g_90["conversions"]["ga4_total"], float(live_90[3] or 0), COUNT_TOLERANCE_ABS),
        check("90d.sessions.total",        g_90["sessions"]["total"],        float(live_90[4] or 0), COUNT_TOLERANCE_ABS),
    ]

    live_cvr_90 = (float(live_90[3] or 0) / float(live_90[4] or 1)) * 100
    checks.append(check("90d.conversions.session_cvr_pct",
                        g_90["conversions"]["session_cvr_pct"],
                        round(live_cvr_90, 2), RATIO_TOLERANCE_PCT, "pct"))

    # ── Channel ROAS (bounded to dataset window to match golden) ─────────────
    live_ch = con.execute("""
        WITH spend AS (
            SELECT 'google_ads' AS channel, SUM(cost)  AS total_spend
            FROM stg_google_ads_performance
            WHERE CAST(date AS DATE) BETWEEN ? AND ?
            UNION ALL
            SELECT 'meta_ads'   AS channel, SUM(spend) AS total_spend
            FROM stg_meta_ads_performance
            WHERE CAST(date AS DATE) BETWEEN ? AND ?
        ),
        rev AS (
            SELECT
                CASE
                    WHEN channel LIKE 'google_ads%' THEN 'google_ads'
                    WHEN channel LIKE 'meta_%'      THEN 'meta_ads'
                    ELSE channel
                END AS ch,
                SUM(linear_credit * order_revenue) AS linear_revenue
            FROM stg_marketing_attribution
            WHERE touchpoint_date BETWEEN ? AND ?
            GROUP BY 1
        )
        SELECT s.channel,
               COALESCE(r.linear_revenue / NULLIF(s.total_spend, 0), 0) AS roas
        FROM spend s
        LEFT JOIN rev r ON s.channel = r.ch
    """, [ds, de, ds, de, ds, de]).fetchall()

    golden_ch = {c["channel"]: c["roas"] for c in g_at["channel_performance"]}
    for ch_name, live_roas_val in live_ch:
        if ch_name in golden_ch:
            checks.append(check(f"channel_roas.{ch_name}",
                                golden_ch[ch_name], float(live_roas_val or 0),
                                RATIO_TOLERANCE_PCT, "pct"))

    con.close()

    # ── Report ─────────────────────────────────────────────────────────────────
    drifted = [c for c in checks if c["drifted"]]
    passed  = [c for c in checks if not c["drifted"]]

    print(f"Checks run: {len(checks)}   ✅ Passed: {len(passed)}   ❌ Drifted: {len(drifted)}\n")

    if drifted:
        print(f"DRIFT DETECTED on [{target}] — regenerate golden_metrics.json with:")
        print(f"    python scripts/generate_golden_metrics.py --target {target}\n")
        for c in drifted:
            print(f"  ❌ {c['metric']}")
            print(f"     golden={c['golden']}  live={c['live']}  diff={c['diff']}")
        return 1

    print(f"✅ No metric drift detected on [{target}]. Golden layer is in sync.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate golden_metrics.json against live warehouse.")
    parser.add_argument("--target", default="duckdb",
                        choices=["duckdb", "bigquery", "snowflake"],
                        help="dbt target warehouse (default: duckdb)")
    parser.add_argument("--strict-freshness", action="store_true",
                        help="Fail (not just warn) when the raw data frontier trails "
                             "today's date — use in the scheduled refresh.")
    parser.add_argument("--completed-months-only", action="store_true",
                        help="Spot-check the COMMITTED artifact's completed-month "
                             "sections (anchor-independent) against the warehouse. "
                             "Run in CI before regenerating golden_metrics.json.")
    args = parser.parse_args()
    if args.completed_months_only:
        sys.exit(validate_completed_months(args.target))
    sys.exit(validate(args.target, strict_freshness=args.strict_freshness))
