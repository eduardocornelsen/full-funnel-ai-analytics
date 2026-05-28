"""
generate_golden_metrics.py
───────────────────────────────────────────────────────────────────────────────
Queries the dbt golden layer and writes dashboards/golden_metrics.json.

This file is the SINGLE SOURCE OF TRUTH for all dashboard numbers.
The AI agent must read this file when generating dashboards — never
recalculate metrics independently.

Usage:
    python scripts/generate_golden_metrics.py                   # DuckDB (default)
    python scripts/generate_golden_metrics.py --target bigquery
    python scripts/generate_golden_metrics.py --target snowflake

Run after every `dbt run` to refresh the golden snapshot.

Date anchoring:
    By default, anchor = MAX(date) from fct_marketing_daily, so the 90-day window
    always follows the latest appended data (daily_synthetic_append.py).
    Use --anchor YYYY-MM-DD to pin a specific date for reproducible CI snapshots.
    See CLAUDE.md §9 for the full dataset-detection rules.
"""

import argparse
import sys
from pathlib import Path
import json
import duckdb
from datetime import date, timedelta, datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))
from _warehouse_adapters import get_connection as _get_warehouse_connection  # noqa: E402

# ── Paths ──────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH      = PROJECT_ROOT / "data" / "olist_analytics.duckdb"
OUTPUT_PATH  = PROJECT_ROOT / "dashboards" / "golden_metrics.json"

# ── Canonical Date Anchoring ───────────────────────────────────────────────────
WINDOW_DAYS  = 90

# ── AOV for Google ROAS (mirrors CLAUDE.md §8 + metrics.js) ───────────────────
GOOGLE_AOV = 100.0


def get_connection(target: str = "duckdb"):
    """Return a warehouse-agnostic connection for the given dbt target."""
    return _get_warehouse_connection(target)


def connect():
    """Legacy no-arg helper — kept for backwards compatibility."""
    return _get_warehouse_connection("duckdb")


# ── Helpers ────────────────────────────────────────────────────────────────────

def fd(d: date) -> str:
    return d.strftime("%Y-%m-%d")


def google_roas(conversions: float, cost: float) -> float:
    """Canonical Google ROAS: conversions × $100 / cost."""
    return round((conversions * GOOGLE_AOV) / cost, 2) if cost else 0.0


def session_cvr(conversions: float, sessions: float) -> float:
    """Canonical Session CVR %."""
    return round(conversions / sessions * 100, 2) if sessions else 0.0


# ── Query Functions ─────────────────────────────────────────────────────────────

def q_marketing_totals(con, start: date, end: date) -> dict:
    """Spend + GA4 sessions/conversions from fct_marketing_daily (date-filtered)."""
    row = con.execute("""
        SELECT
            SUM(total_google_spend)        AS google_spend,
            SUM(total_meta_spend)          AS meta_spend,
            SUM(total_spend)               AS total_spend,
            SUM(total_ad_conversions)      AS ad_conversions,
            SUM(total_conversions)         AS ga4_conversions,
            SUM(ga4_total_sessions)        AS sessions,
            SUM(ga4_engaged_sessions)      AS engaged_sessions
        FROM fct_marketing_daily
        WHERE date BETWEEN ? AND ?
    """, [fd(start), fd(end)]).fetchone()
    keys = ["google_spend", "meta_spend", "total_spend", "ad_conversions",
            "ga4_conversions", "sessions", "engaged_sessions"]
    d = dict(zip(keys, [float(v or 0) for v in row]))
    d["session_cvr_pct"]     = session_cvr(d["ga4_conversions"], d["sessions"])
    d["engagement_rate_pct"] = round(d["engaged_sessions"] / d["sessions"] * 100, 2) if d["sessions"] else 0.0
    return d


def q_attribution_by_channel(con, start: date, end: date) -> list[dict]:
    """
    Attribution revenue by channel, date-filtered on touchpoint_date.
    Uses stg_marketing_attribution (row-level) so window filtering works.
    fct_marketing_attribution is all-time only — not used here.
    """
    rows = con.execute("""
        SELECT
            channel,
            SUM(first_touch_credit * order_revenue)  AS first_touch_revenue,
            SUM(last_touch_credit  * order_revenue)  AS last_touch_revenue,
            SUM(linear_credit      * order_revenue)  AS linear_revenue,
            COUNT(DISTINCT order_id)                 AS total_orders
        FROM stg_marketing_attribution
        WHERE touchpoint_date BETWEEN ? AND ?
        GROUP BY channel
        ORDER BY linear_revenue DESC
    """, [fd(start), fd(end)]).fetchall()
    cols = ["channel", "first_touch_revenue", "last_touch_revenue",
            "linear_revenue", "total_orders"]
    return [dict(zip(cols, [str(r[0])] + [round(float(v or 0), 2) for v in r[1:]])) for r in rows]


def q_channel_performance(con, start: date, end: date) -> list[dict]:
    """
    Platform-level spend + attributed revenue for the given window.
    Computes directly from staging tables so date filtering applies.
    """
    rows = con.execute("""
        WITH spend_agg AS (
            SELECT 'google_ads' AS channel, SUM(cost)  AS total_spend
            FROM stg_google_ads_performance
            WHERE date BETWEEN ? AND ?
            UNION ALL
            SELECT 'meta_ads'   AS channel, SUM(spend) AS total_spend
            FROM stg_meta_ads_performance
            WHERE date BETWEEN ? AND ?
        ),
        revenue_mapped AS (
            SELECT
                CASE
                    WHEN channel LIKE 'google_ads%' THEN 'google_ads'
                    WHEN channel LIKE 'meta_%'      THEN 'meta_ads'
                    ELSE channel
                END AS channel,
                SUM(linear_credit * order_revenue) AS linear_revenue,
                COUNT(DISTINCT order_id)           AS total_orders
            FROM stg_marketing_attribution
            WHERE touchpoint_date BETWEEN ? AND ?
            GROUP BY 1
        )
        SELECT
            COALESCE(s.channel, r.channel)                                AS channel,
            COALESCE(s.total_spend, 0)                                    AS total_spend,
            COALESCE(r.linear_revenue, 0)                                 AS attributed_revenue,
            COALESCE(r.total_orders, 0)                                   AS total_orders,
            COALESCE(s.total_spend / NULLIF(r.total_orders, 0), 0)        AS cac,
            COALESCE(r.linear_revenue / NULLIF(s.total_spend, 0), 0)      AS roas
        FROM spend_agg s
        FULL OUTER JOIN revenue_mapped r ON s.channel = r.channel
        WHERE COALESCE(s.channel, r.channel) IS NOT NULL
        ORDER BY attributed_revenue DESC
    """, [fd(start), fd(end), fd(start), fd(end), fd(start), fd(end)]).fetchall()

    cols = ["channel", "total_spend", "attributed_revenue", "total_orders", "cac", "roas"]
    return [dict(zip(cols, [str(r[0])] + [round(float(v or 0), 2) for v in r[1:]])) for r in rows]


def q_blended_roas(marketing: dict, attribution: list[dict]) -> float:
    """Canonical Blended ROAS: total linear attributed revenue / total ad spend."""
    total_linear_rev = sum(c["linear_revenue"] for c in attribution)
    total_spend      = marketing["total_spend"]
    return round(total_linear_rev / total_spend, 2) if total_spend else 0.0


def q_ga4_by_channel(con, start: date, end: date) -> list[dict]:
    """GA4 sessions, engagement, and conversions by channel group."""
    rows = con.execute("""
        SELECT channel_group,
               SUM(sessions)         AS sessions,
               SUM(engaged_sessions) AS engaged_sessions,
               SUM(conversions)      AS conversions
        FROM stg_ga4_sessions
        WHERE date BETWEEN ? AND ?
        GROUP BY channel_group
        ORDER BY sessions DESC
    """, [fd(start), fd(end)]).fetchall()

    result = []
    for r in rows:
        ch, sess, eng, conv = r[0], float(r[1] or 0), float(r[2] or 0), float(r[3] or 0)
        result.append({
            "channel":              ch,
            "sessions":             int(sess),
            "engaged_sessions":     int(eng),
            "conversions":          int(conv),
            "session_cvr_pct":      session_cvr(conv, sess),
            "engagement_rate_pct":  round(eng / sess * 100, 2) if sess else 0.0,
        })
    total_sess = sum(r["sessions"] for r in result)
    for r in result:
        r["session_share_pct"] = round(r["sessions"] / total_sess * 100, 1) if total_sess else 0.0
    return result


def q_google_campaigns(con, start: date, end: date) -> list[dict]:
    """Google Ads campaign performance with canonical ROAS (conversions × $100 / cost)."""
    rows = con.execute("""
        SELECT campaign_name, campaign_type,
               SUM(impressions) AS impressions,
               SUM(clicks)      AS clicks,
               SUM(cost)        AS cost,
               SUM(conversions) AS conversions
        FROM stg_google_ads_performance
        WHERE date BETWEEN ? AND ?
        GROUP BY campaign_name, campaign_type
        ORDER BY cost DESC
    """, [fd(start), fd(end)]).fetchall()

    result = []
    for r in rows:
        name, ctype, imp, clicks, cost, conv = r
        imp   = float(imp   or 0)
        clicks = float(clicks or 0)
        cost  = float(cost  or 0)
        conv  = float(conv  or 0)
        result.append({
            "campaign_name":   name,
            "campaign_type":   ctype,
            "impressions":     int(imp),
            "clicks":          int(clicks),
            "cost":            round(cost, 2),
            "conversions":     int(conv),
            "ctr_pct":         round(clicks / imp * 100, 2) if imp else 0.0,
            "click_cvr_pct":   round(conv / clicks * 100, 2) if clicks else 0.0,
            "roas":            google_roas(conv, cost),
        })
    return result


def q_meta_campaigns(con, start: date, end: date) -> list[dict]:
    """Meta Ads campaign performance. ROAS = purchases × $100 / spend (platform-native)."""
    rows = con.execute("""
        SELECT campaign_name, objective,
               SUM(impressions)                             AS impressions,
               SUM(link_clicks)                            AS link_clicks,
               SUM(spend)                                  AS spend,
               SUM(purchases)                              AS purchases,
               SUM(purchases * 100.0) / NULLIF(SUM(spend), 0) AS platform_roas
        FROM stg_meta_ads_performance
        WHERE date BETWEEN ? AND ?
        GROUP BY campaign_name, objective
        ORDER BY spend DESC
    """, [fd(start), fd(end)]).fetchall()

    result = []
    for r in rows:
        name, obj, imp, clicks, spend, purchases, roas = r
        imp = float(imp or 0); clicks = float(clicks or 0)
        spend = float(spend or 0); purchases = float(purchases or 0)
        roas = float(roas or 0)
        result.append({
            "campaign_name":  name,
            "objective":      obj,
            "impressions":    int(imp),
            "link_clicks":    int(clicks),
            "spend":          round(spend, 2),
            "purchases":      int(purchases),
            "cpm":            round(spend / imp * 1000, 2) if imp else 0.0,
            "click_cvr_pct":  round(purchases / clicks * 100, 2) if clicks else 0.0,
            "roas":           round(roas, 2),
        })
    return result


def q_hubspot_pipeline(con) -> dict:
    """HubSpot: all-time contacts count + pipeline by stage.
    NOTE: Contacts are always all-time (lifetime CRM metric, not funnel step).
    """
    stages = con.execute("""
        SELECT deal_stage, COUNT(*) AS deal_count, SUM(amount) AS total_value
        FROM stg_hubspot_deals
        GROUP BY deal_stage
        ORDER BY total_value DESC
    """).fetchall()

    contacts = con.execute("SELECT COUNT(*) FROM stg_hubspot_contacts").fetchone()[0]

    return {
        "total_contacts":      int(contacts),
        "total_pipeline_value": round(sum(float(r[2] or 0) for r in stages), 2),
        "pipeline_by_stage": [
            {"stage": r[0], "deal_count": int(r[1]), "total_value": round(float(r[2] or 0), 2)}
            for r in stages
        ],
    }


def q_salesforce_pipeline(con) -> dict:
    """Salesforce: all-time pipeline + closed-won by lead source."""
    stages = con.execute("""
        SELECT stage, COUNT(*) AS opp_count, SUM(amount) AS total_value,
               SUM(weighted_amount) AS expected_revenue
        FROM stg_salesforce_opportunities
        GROUP BY stage ORDER BY total_value DESC
    """).fetchall()

    sources = con.execute("""
        SELECT lead_source, SUM(amount) AS revenue, COUNT(*) AS won_count
        FROM stg_salesforce_opportunities
        WHERE is_won = TRUE
        GROUP BY lead_source ORDER BY revenue DESC
    """).fetchall()

    closed_won = con.execute(
        "SELECT SUM(amount) FROM stg_salesforce_opportunities WHERE is_won = TRUE"
    ).fetchone()[0]

    return {
        "closed_won_revenue": round(float(closed_won or 0), 2),
        "pipeline_by_stage": [
            {"stage": r[0], "opp_count": int(r[1]),
             "total_value": round(float(r[2] or 0), 2),
             "expected_revenue": round(float(r[3] or 0), 2)}
            for r in stages
        ],
        "closed_won_by_source": [
            {"lead_source": r[0], "revenue": round(float(r[1] or 0), 2), "won_count": int(r[2])}
            for r in sources
        ],
    }


# ── Section Builder ─────────────────────────────────────────────────────────────

def build_section(con, start: date, end: date, label: str) -> dict:
    marketing    = q_marketing_totals(con, start, end)
    attribution  = q_attribution_by_channel(con, start, end)
    channel_perf = q_channel_performance(con, start, end)
    blended_roas = q_blended_roas(marketing, attribution)
    ga4_channels = q_ga4_by_channel(con, start, end)
    goog_camps   = q_google_campaigns(con, start, end)
    meta_camps   = q_meta_campaigns(con, start, end)
    hs           = q_hubspot_pipeline(con)
    sf           = q_salesforce_pipeline(con)

    return {
        "label":  label,
        "window": {"start": fd(start), "end": fd(end)},
        "spend": {
            "google": marketing["google_spend"],
            "meta":   marketing["meta_spend"],
            "total":  marketing["total_spend"],
        },
        "sessions": {
            "total":               int(marketing["sessions"]),
            "engaged":             int(marketing["engaged_sessions"]),
            "engagement_rate_pct": marketing["engagement_rate_pct"],
        },
        "conversions": {
            "ga4_total":       int(marketing["ga4_conversions"]),
            "ad_platform":     int(marketing["ad_conversions"]),
            "session_cvr_pct": marketing["session_cvr_pct"],
        },
        "blended_roas":        blended_roas,
        "channel_performance": channel_perf,
        "attribution_by_channel": attribution,
        "ga4_by_channel":      ga4_channels,
        "campaigns": {
            "google": goog_camps,
            "meta":   meta_camps,
        },
        "crm": {
            "hubspot":    hs,
            "salesforce": sf,
        },
    }


# ── Main ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate golden_metrics.json from dbt mart tables.")
    parser.add_argument("--target", default="duckdb",
                        choices=["duckdb", "bigquery", "snowflake"],
                        help="dbt target warehouse (default: duckdb)")
    parser.add_argument("--anchor",
                        metavar="YYYY-MM-DD",
                        help="Fix the anchor date instead of auto-detecting from DB. "
                             "Useful for reproducible CI snapshots. "
                             "Default: auto-detect MAX(date) from fct_marketing_daily.")
    args = parser.parse_args()

    if args.target == "duckdb":
        print(f"Connecting to DuckDB: {DB_PATH}")
    else:
        print(f"Connecting to {args.target} ...")
    con = get_connection(args.target)

    dataset_start = date(2024, 7, 16)

    if args.anchor:
        anchor = date.fromisoformat(args.anchor)
        print(f"--anchor override: {anchor}")
    else:
        # Auto-detect the latest date so the window follows daily_synthetic_append.py
        latest = con.execute("SELECT MAX(date) FROM fct_marketing_daily").fetchone()[0]
        anchor = date.fromisoformat(str(latest)[:10]) if not isinstance(latest, date) else latest
        print(f"Auto-detected anchor={anchor} from fct_marketing_daily")

    window_start = anchor - timedelta(days=WINDOW_DAYS - 1)
    window_end   = anchor
    print(f"90d window: {window_start} → {window_end}")

    dataset_end = anchor

    print("Building all-time section …")
    all_time = build_section(con, dataset_start, dataset_end, "All-time (dataset full range)")

    # ── Pre-computed rolling windows (relative to anchor) ─────────────────────
    sections: dict = {}
    for days, key in [(7, "windowed_7d"), (30, "windowed_30d"),
                      (60, "windowed_60d"), (90, "windowed_90d"),
                      (180, "windowed_180d")]:
        ws = anchor - timedelta(days=days - 1)
        label = f"{days}-day window ({fd(ws)} → {fd(anchor)})"
        print(f"Building {days}-day window ({fd(ws)} → {fd(anchor)}) …")
        sections[key] = build_section(con, ws, anchor, label)

    # ── Pre-computed calendar months (last 3 relative to anchor) ─────────────
    import calendar as _cal
    month_sections: dict = {}
    for offset in range(3):
        # Walk backwards: anchor month, then previous months
        y = anchor.year
        m = anchor.month - offset
        if m <= 0:
            m += 12
            y -= 1
        last_day = _cal.monthrange(y, m)[1]
        ms = date(y, m, 1)
        me = date(y, m, last_day)
        key   = f"month_{y}_{m:02d}"
        label = f"{ms.strftime('%B %Y')} (full month)"
        print(f"Building {label} …")
        month_sections[key] = build_section(con, ms, me, label)

    con.close()

    # ── Canonical window metadata (for AI agent reference) ────────────────────
    available_windows = (
        {k: sections[k]["window"] for k in sections}
        | {k: month_sections[k]["window"] for k in month_sections}
        | {"all_time": {"start": fd(dataset_start), "end": fd(dataset_end)}}
    )

    output = {
        "_meta": {
            "generated_at":      datetime.now(timezone.utc).isoformat(),
            "anchor_date":       fd(anchor),
            "dataset_start":     fd(dataset_start),
            "dataset_end":       fd(dataset_end),
            "window_days":       WINDOW_DAYS,
            "window_start":      fd(window_start),
            "window_end":        fd(window_end),
            "dbt_source":        str(DB_PATH) if args.target == "duckdb" else args.target,
            "dbt_target":        args.target,
            "schema_version":    "2.2",
            "google_aov":        GOOGLE_AOV,
            "available_windows": available_windows,
            "note": (
                "SINGLE SOURCE OF TRUTH for all dashboard numbers. "
                "AI agent must read and copy values — never recalculate independently. "
                "For windows not listed in available_windows, use query_window.py. "
                "Regenerate after dbt run: python scripts/generate_golden_metrics.py"
            ),
        },
        "all_time":    all_time,
    }
    output.update(sections)        # windowed_7d … windowed_180d
    output.update(month_sections)  # month_2026_03, month_2026_02, month_2026_01

    OUTPUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False))

    print(f"\n✅ Written: {OUTPUT_PATH}")
    print(f"   All-time   → Blended ROAS: {all_time['blended_roas']}x"
          f"  |  Sessions: {all_time['sessions']['total']:,}"
          f"  |  Spend: ${all_time['spend']['total']:,.2f}")
    w90 = sections["windowed_90d"]
    print(f"   90d window → Blended ROAS: {w90['blended_roas']}x"
          f"  |  Sessions: {w90['sessions']['total']:,}"
          f"  |  Spend: ${w90['spend']['total']:,.2f}")
    print(f"\n   Pre-computed windows: {', '.join(list(sections) + list(month_sections))}")
    print(f"   For other ranges: python scripts/query_window.py --last-days N")


if __name__ == "__main__":
    main()
