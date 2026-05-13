"""
generate_golden_metrics.py
───────────────────────────────────────────────────────────────────────────────
Queries the dbt DuckDB golden layer and writes dashboards/golden_metrics.json.

This file is the SINGLE SOURCE OF TRUTH for all dashboard numbers.
The AI agent must read this file when generating dashboards — never
recalculate metrics independently.

Usage:
    python scripts/generate_golden_metrics.py

Run after every `dbt run` to refresh the golden snapshot.

Date anchoring (SYNTHETIC DATASET — this project's default):
    The dataset ends at 2026-03-15 (fixed boundary — does not update daily).
    ANCHOR_DATE is always 2026-03-15. Window: 2025-12-16 → 2026-03-15.
    These dates are locked — do NOT use today().

    LIVE / REAL DATASET (open-source swap-in):
    If you connect a live data source (BigQuery, Supabase, Snowflake, etc.),
    replace ANCHOR_DATE with date.today() and the window will roll automatically.
    See CLAUDE.md §9 for the full dataset-detection rules.
"""

from pathlib import Path
import json
import duckdb
from datetime import date, timedelta, datetime, timezone

# ── Paths ──────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH      = PROJECT_ROOT / "data" / "olist_analytics.duckdb"
OUTPUT_PATH  = PROJECT_ROOT / "dashboards" / "golden_metrics.json"

# ── Canonical Date Anchoring ───────────────────────────────────────────────────
# Dataset ends 2026-03-15. This is FIXED — never use date.today().
ANCHOR_DATE  = date(2026, 3, 15)
WINDOW_DAYS  = 90
WINDOW_START = ANCHOR_DATE - timedelta(days=WINDOW_DAYS - 1)   # 2025-12-16
WINDOW_END   = ANCHOR_DATE                                       # 2026-03-15

# ── AOV for Google ROAS (mirrors CLAUDE.md §8 + metrics.js) ───────────────────
GOOGLE_AOV = 100.0


def connect():
    return duckdb.connect(str(DB_PATH), read_only=True)


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
    print(f"Connecting to DuckDB: {DB_PATH}")
    con = connect()

    dataset_start = date(2024, 7, 16)
    dataset_end   = ANCHOR_DATE

    print(f"Anchor date: {ANCHOR_DATE}  |  90d window: {WINDOW_START} → {WINDOW_END}")

    print("Building all-time section …")
    all_time = build_section(con, dataset_start, dataset_end, "All-time (dataset full range)")

    print("Building 90-day windowed section …")
    windowed_90d = build_section(con, WINDOW_START, WINDOW_END, "90-day window (canonical)")

    con.close()

    output = {
        "_meta": {
            "generated_at":   datetime.now(timezone.utc).isoformat(),
            "anchor_date":    fd(ANCHOR_DATE),
            "dataset_start":  fd(dataset_start),
            "dataset_end":    fd(dataset_end),
            "window_days":    WINDOW_DAYS,
            "window_start":   fd(WINDOW_START),
            "window_end":     fd(WINDOW_END),
            "dbt_source":     str(DB_PATH),
            "schema_version": "2.1",
            "google_aov":     GOOGLE_AOV,
            "note": (
                "SINGLE SOURCE OF TRUTH for all dashboard numbers. "
                "AI agent must read and copy values — never recalculate independently. "
                "Regenerate after dbt run: python scripts/generate_golden_metrics.py"
            ),
        },
        "all_time":    all_time,
        "windowed_90d": windowed_90d,
    }

    OUTPUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False))

    print(f"\n✅ Written: {OUTPUT_PATH}")
    print(f"   All-time   → Blended ROAS: {all_time['blended_roas']}x"
          f"  |  Sessions: {all_time['sessions']['total']:,}"
          f"  |  Spend: ${all_time['spend']['total']:,.2f}"
          f"  |  Linear Rev: ${sum(c['linear_revenue'] for c in all_time['attribution_by_channel']):,.2f}")
    print(f"   90d window → Blended ROAS: {windowed_90d['blended_roas']}x"
          f"  |  Sessions: {windowed_90d['sessions']['total']:,}"
          f"  |  Spend: ${windowed_90d['spend']['total']:,.2f}"
          f"  |  Linear Rev: ${sum(c['linear_revenue'] for c in windowed_90d['attribution_by_channel']):,.2f}")


if __name__ == "__main__":
    main()
