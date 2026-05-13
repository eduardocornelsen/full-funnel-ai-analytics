"""
validate_metrics.py
───────────────────────────────────────────────────────────────────────────────
Validates that dashboards/golden_metrics.json is in sync with the live DuckDB
golden layer. Detects metric drift.

Usage:
    python scripts/validate_metrics.py

Returns:
    Exit code 0 — no drift detected
    Exit code 1 — drift found (details printed)

Run before generating any new dashboard, or in CI after dbt run.
"""

from pathlib import Path
import json
import sys
import duckdb
from datetime import date, timedelta

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH      = PROJECT_ROOT / "data" / "olist_analytics.duckdb"
GOLDEN_PATH  = PROJECT_ROOT / "dashboards" / "golden_metrics.json"

# Tolerance thresholds
DOLLAR_TOLERANCE_ABS  = 1.00    # $1 absolute tolerance for dollar amounts
RATIO_TOLERANCE_PCT   = 0.50    # 0.5% relative tolerance (accounts for rounding in stored JSON)
COUNT_TOLERANCE_ABS   = 1       # 1 row tolerance for counts


def load_golden() -> dict:
    if not GOLDEN_PATH.exists():
        print(f"❌ golden_metrics.json not found at {GOLDEN_PATH}")
        print("   Run: python scripts/generate_golden_metrics.py")
        sys.exit(1)
    return json.loads(GOLDEN_PATH.read_text())


def connect():
    return duckdb.connect(str(DB_PATH), read_only=True)


def check(name: str, golden_val: float, live_val: float,
          tolerance: float, tolerance_type: str = "abs") -> dict:
    """Compare a golden value to a live value. Returns a result dict."""
    if tolerance_type == "pct":
        diff_pct = abs(golden_val - live_val) / max(abs(golden_val), 1e-9) * 100
        drifted = diff_pct > tolerance
        diff_str = f"{diff_pct:.4f}%"
    else:
        diff_abs = abs(golden_val - live_val)
        drifted = diff_abs > tolerance
        diff_str = f"{diff_abs:.4f}"

    return {
        "metric": name,
        "golden": golden_val,
        "live": live_val,
        "diff": diff_str,
        "drifted": drifted,
    }


def validate():
    golden = load_golden()
    meta   = golden["_meta"]

    print(f"Golden file generated: {meta['generated_at']}")
    print(f"Anchor date: {meta['anchor_date']}  |  Window: {meta['window_start']} → {meta['window_end']}")
    print(f"Connecting to: {DB_PATH}\n")

    con    = connect()
    issues = []
    checks = []

    # ── All-time checks ────────────────────────────────────────────────────────
    g_at = golden["all_time"]

    live = con.execute("""
        SELECT
            SUM(total_google_spend)  AS google_spend,
            SUM(total_meta_spend)    AS meta_spend,
            SUM(total_spend)         AS total_spend,
            SUM(total_conversions)   AS ga4_conversions,
            SUM(ga4_total_sessions)  AS sessions
        FROM fct_marketing_daily
    """).fetchone()

    checks += [
        check("all_time.spend.google",  g_at["spend"]["google"], float(live[0] or 0), DOLLAR_TOLERANCE_ABS),
        check("all_time.spend.meta",    g_at["spend"]["meta"],   float(live[1] or 0), DOLLAR_TOLERANCE_ABS),
        check("all_time.spend.total",   g_at["spend"]["total"],  float(live[2] or 0), DOLLAR_TOLERANCE_ABS),
        check("all_time.conversions.ga4_total", g_at["conversions"]["ga4_total"], float(live[3] or 0), COUNT_TOLERANCE_ABS),
        check("all_time.sessions.total",        g_at["sessions"]["total"],         float(live[4] or 0), COUNT_TOLERANCE_ABS),
    ]

    # Blended ROAS (all-time): linear revenue from stg / total spend
    # Use stg_marketing_attribution (same source as generator, not fct which is pre-aggregated)
    live_rev_at = con.execute("""
        SELECT SUM(linear_credit * order_revenue) FROM stg_marketing_attribution
    """).fetchone()[0]
    live_roas = round(float(live_rev_at or 0) / float(live[2] or 1), 2)
    checks.append(check("all_time.blended_roas", g_at["blended_roas"], live_roas, RATIO_TOLERANCE_PCT, "pct"))

    # HubSpot contacts
    live_contacts = con.execute("SELECT COUNT(*) FROM stg_hubspot_contacts").fetchone()[0]
    checks.append(check("crm.hubspot.total_contacts",
                        g_at["crm"]["hubspot"]["total_contacts"], float(live_contacts), COUNT_TOLERANCE_ABS))

    # Salesforce closed won
    live_sf_won = con.execute("SELECT SUM(amount) FROM stg_salesforce_opportunities WHERE is_won=TRUE").fetchone()[0]
    checks.append(check("crm.salesforce.closed_won_revenue",
                        g_at["crm"]["salesforce"]["closed_won_revenue"], float(live_sf_won or 0), DOLLAR_TOLERANCE_ABS))

    # ── 90d windowed checks ────────────────────────────────────────────────────
    g_90 = golden["windowed_90d"]
    ws   = meta["window_start"]
    we   = meta["window_end"]

    live_90 = con.execute("""
        SELECT
            SUM(total_google_spend), SUM(total_meta_spend), SUM(total_spend),
            SUM(total_conversions), SUM(ga4_total_sessions)
        FROM fct_marketing_daily
        WHERE date BETWEEN ? AND ?
    """, [ws, we]).fetchone()

    checks += [
        check("90d.spend.google", g_90["spend"]["google"], float(live_90[0] or 0), DOLLAR_TOLERANCE_ABS),
        check("90d.spend.meta",   g_90["spend"]["meta"],   float(live_90[1] or 0), DOLLAR_TOLERANCE_ABS),
        check("90d.spend.total",  g_90["spend"]["total"],  float(live_90[2] or 0), DOLLAR_TOLERANCE_ABS),
        check("90d.conversions.ga4_total", g_90["conversions"]["ga4_total"], float(live_90[3] or 0), COUNT_TOLERANCE_ABS),
        check("90d.sessions.total",        g_90["sessions"]["total"],         float(live_90[4] or 0), COUNT_TOLERANCE_ABS),
    ]

    # Session CVR (90d)
    live_cvr_90 = (float(live_90[3] or 0) / float(live_90[4] or 1)) * 100
    checks.append(check("90d.conversions.session_cvr_pct",
                        g_90["conversions"]["session_cvr_pct"], round(live_cvr_90, 2), RATIO_TOLERANCE_PCT, "pct"))

    # ── Channel performance ROAS check — same collapsed-channel logic as generator ──
    live_ch = con.execute("""
        WITH spend AS (
            SELECT 'google_ads' AS channel, SUM(cost)  AS total_spend FROM stg_google_ads_performance
            UNION ALL
            SELECT 'meta_ads'   AS channel, SUM(spend) AS total_spend FROM stg_meta_ads_performance
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
            GROUP BY 1
        )
        SELECT s.channel,
               COALESCE(r.linear_revenue / NULLIF(s.total_spend, 0), 0) AS roas
        FROM spend s
        LEFT JOIN rev r ON s.channel = r.ch
    """).fetchall()
    golden_ch = {c["channel"]: c["roas"] for c in g_at["channel_performance"]}
    for ch_name, live_roas_val in live_ch:
        if ch_name in golden_ch:
            checks.append(check(f"channel_roas.{ch_name}",
                                golden_ch[ch_name], float(live_roas_val or 0), RATIO_TOLERANCE_PCT, "pct"))

    con.close()

    # ── Report ─────────────────────────────────────────────────────────────────
    drifted = [c for c in checks if c["drifted"]]
    passed  = [c for c in checks if not c["drifted"]]

    print(f"Checks run: {len(checks)}   ✅ Passed: {len(passed)}   ❌ Drifted: {len(drifted)}\n")

    if drifted:
        print("DRIFT DETECTED — regenerate golden_metrics.json with:")
        print("    python scripts/generate_golden_metrics.py\n")
        for c in drifted:
            print(f"  ❌ {c['metric']}")
            print(f"     golden={c['golden']}  live={c['live']}  diff={c['diff']}")
        return 1
    else:
        print("✅ No metric drift detected. Golden layer is in sync.")
        return 0


if __name__ == "__main__":
    sys.exit(validate())
