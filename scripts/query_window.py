"""
query_window.py
─────────────────────────────────────────────────────────────────────────────
On-demand metric query for ANY date window.

The golden layer (golden_metrics.json) covers common pre-computed windows
(7d, 30d, 60d, 90d, 180d, monthly).  When a user asks for a custom range —
"last 45 days", "Q1 2026", a specific month — this script queries the CSV
source files directly via DuckDB in-memory and returns the same metric
schema as a golden_metrics.json section.

Usage:
    # Arbitrary range
    python scripts/query_window.py --start 2025-09-16 --end 2026-03-15

    # Relative shortcuts
    python scripts/query_window.py --last-days 60
    python scripts/query_window.py --last-days 1          # yesterday (anchor-relative)

    # Calendar shortcuts
    python scripts/query_window.py --month 2026-02        # Feb 2026
    python scripts/query_window.py --month 2025-12
    python scripts/query_window.py --year 2025

    # Machine-readable output
    python scripts/query_window.py --last-days 30 --output metrics_30d.json

    # Python import (no subprocess)
    from scripts.query_window import query_window
    section = query_window(start=date(2026,1,1), end=date(2026,3,15))

Notes:
  - Data is always sourced from data/mock_marketing/*.csv
  - CRM data (HubSpot, Salesforce) is always all-time — it is a lifetime
    count and must not be date-filtered. Labelled "(CRM all-time)" in output.
  - --last-days is relative to MAX(date) in the CSV data, so it always
    follows daily_synthetic_append.py without manual updates.
  - Results are ad-hoc and may diverge from golden_metrics.json by rounding
    (~$0.01) since they bypass the dbt mart layer. Label any dashboard built
    from this output with "⚡ Ad-hoc query · not from golden layer".
"""

from __future__ import annotations

import argparse
import calendar
import json
import sys
from datetime import date, timedelta
from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR     = PROJECT_ROOT / "data" / "mock_marketing"

GOOGLE_AOV  = 100.0


def _latest_csv_date() -> date:
    """Return MAX(date) from the GA4 daily sessions CSV — used for --last-days anchor."""
    csv = DATA_DIR / "ga4_daily_sessions.csv"
    con = duckdb.connect(":memory:")
    result = con.execute(
        f"SELECT MAX(CAST(date AS DATE)) FROM read_csv_auto('{csv}')"
    ).fetchone()[0]
    con.close()
    if result is None:
        raise RuntimeError(f"No dates found in {csv}")
    return result if isinstance(result, date) else date.fromisoformat(str(result)[:10])


# ── CSV-backed DuckDB connection ──────────────────────────────────────────────

def build_csv_connection() -> duckdb.DuckDBPyConnection:
    """
    In-memory DuckDB with staging views over mock CSVs.
    Replicates the dbt staging layer so query functions run without
    the mart tables being pre-built.
    """
    con = duckdb.connect(":memory:")
    d   = DATA_DIR

    # Simple 1-to-1 CSV → view mappings
    for view, csv in [
        ("stg_ga4_sessions",            "ga4_daily_sessions.csv"),
        ("stg_google_ads_performance",  "google_ads_daily_performance.csv"),
        ("stg_meta_ads_performance",    "meta_ads_daily_performance.csv"),
        ("stg_marketing_attribution",   "marketing_attribution.csv"),
        ("stg_hubspot_contacts",        "hubspot_contacts.csv"),
        ("stg_hubspot_deals",           "hubspot_deals.csv"),
    ]:
        con.execute(
            f"CREATE VIEW {view} AS SELECT * FROM read_csv_auto('{d / csv}')"
        )

    # Salesforce: add computed columns not present in the CSV
    con.execute(f"""
        CREATE VIEW stg_salesforce_opportunities AS
        SELECT *,
            (stage = 'Closed Won')         AS is_won,
            expected_revenue               AS weighted_amount
        FROM read_csv_auto('{d / "salesforce_opportunities.csv"}')
    """)

    # fct_marketing_daily: daily spine joining all three ad/session sources.
    # Replicates the dbt mart table so query_functions from
    # generate_golden_metrics.py work unchanged.
    con.execute("""
        CREATE VIEW fct_marketing_daily AS
        WITH google AS (
            SELECT CAST(date AS DATE) AS date,
                   SUM(cost)          AS google_spend,
                   SUM(conversions)   AS google_conversions
            FROM stg_google_ads_performance GROUP BY 1
        ),
        meta AS (
            SELECT CAST(date AS DATE) AS date,
                   SUM(spend)     AS meta_spend,
                   SUM(purchases) AS meta_purchases
            FROM stg_meta_ads_performance GROUP BY 1
        ),
        ga4 AS (
            SELECT CAST(date AS DATE) AS date,
                   SUM(sessions)          AS sessions,
                   SUM(engaged_sessions)  AS engaged_sessions,
                   SUM(conversions)       AS ga4_conversions
            FROM stg_ga4_sessions GROUP BY 1
        ),
        spine AS (
            SELECT DISTINCT date FROM (
                SELECT date FROM google UNION ALL
                SELECT date FROM meta   UNION ALL
                SELECT date FROM ga4
            )
        )
        SELECT
            s.date,
            COALESCE(g.google_spend, 0)                                  AS total_google_spend,
            COALESCE(m.meta_spend, 0)                                    AS total_meta_spend,
            COALESCE(g.google_spend, 0) + COALESCE(m.meta_spend, 0)     AS total_spend,
            COALESCE(g.google_conversions, 0) + COALESCE(m.meta_purchases, 0) AS total_ad_conversions,
            COALESCE(ga4.ga4_conversions, 0)   AS total_conversions,
            COALESCE(ga4.sessions, 0)           AS ga4_total_sessions,
            COALESCE(ga4.engaged_sessions, 0)   AS ga4_engaged_sessions
        FROM spine s
        LEFT JOIN google g  ON s.date = g.date
        LEFT JOIN meta m    ON s.date = m.date
        LEFT JOIN ga4       ON s.date = ga4.date
    """)

    return con


# ── Date window parsing ───────────────────────────────────────────────────────

def parse_window(args) -> tuple[date, date, str]:
    """
    Resolve CLI args to (start, end, label).

    --last-days N         : N days ending at the latest date in the CSV data
    --start/--end         : explicit range
    --month YYYY-MM       : full calendar month
    --year YYYY           : full calendar year
    """
    if args.last_days is not None:
        end   = _latest_csv_date()
        start = end - timedelta(days=int(args.last_days) - 1)
        label = f"Last {args.last_days} days (ending {end})"

    elif args.month is not None:
        y, m  = map(int, args.month.split("-"))
        start = date(y, m, 1)
        end   = date(y, m, calendar.monthrange(y, m)[1])
        label = f"{start.strftime('%B %Y')} (full month)"

    elif args.year is not None:
        y     = int(args.year)
        start = date(y, 1, 1)
        end   = date(y, 12, 31)
        label = f"Full year {y}"

    elif args.start and args.end:
        start = date.fromisoformat(args.start)
        end   = date.fromisoformat(args.end)
        label = f"Custom window {start} → {end}"

    else:
        raise ValueError(
            "Specify one of: --last-days N, --month YYYY-MM, --year YYYY, "
            "or --start YYYY-MM-DD --end YYYY-MM-DD"
        )

    return start, end, label


# ── Query section builder ─────────────────────────────────────────────────────
# These mirror the q_*() functions in generate_golden_metrics.py but use the
# CSV-backed connection from build_csv_connection(). Kept in sync manually.

def _fd(d: date) -> str:
    return d.strftime("%Y-%m-%d")


def _google_roas(conv: float, cost: float) -> float:
    return round((conv * GOOGLE_AOV) / cost, 2) if cost else 0.0


def _session_cvr(conv: float, sessions: float) -> float:
    return round(conv / sessions * 100, 2) if sessions else 0.0


def build_window_section(con: duckdb.DuckDBPyConnection,
                         start: date, end: date, label: str) -> dict:
    """
    Build a metrics section for any date window.
    Identical schema to a golden_metrics.json section — dashboards and AI
    agents can use the output interchangeably.
    """
    ws, we = _fd(start), _fd(end)

    # ── Spend + sessions ──────────────────────────────────────────────────────
    row = con.execute("""
        SELECT
            SUM(total_google_spend), SUM(total_meta_spend), SUM(total_spend),
            SUM(total_ad_conversions), SUM(total_conversions),
            SUM(ga4_total_sessions),  SUM(ga4_engaged_sessions)
        FROM fct_marketing_daily WHERE date BETWEEN ? AND ?
    """, [ws, we]).fetchone()
    g_sp, m_sp, t_sp, ad_conv, ga4_conv, sess, eng = [float(v or 0) for v in row]

    # ── Attribution by channel ────────────────────────────────────────────────
    attr_rows = con.execute("""
        SELECT channel,
               SUM(first_touch_credit * order_revenue)  AS first_touch_revenue,
               SUM(last_touch_credit  * order_revenue)  AS last_touch_revenue,
               SUM(linear_credit      * order_revenue)  AS linear_revenue,
               COUNT(DISTINCT order_id)                 AS total_orders
        FROM stg_marketing_attribution
        WHERE CAST(touchpoint_date AS DATE) BETWEEN ? AND ?
        GROUP BY channel ORDER BY linear_revenue DESC
    """, [ws, we]).fetchall()
    attribution = [
        {
            "channel":              r[0],
            "first_touch_revenue":  round(float(r[1] or 0), 2),
            "last_touch_revenue":   round(float(r[2] or 0), 2),
            "linear_revenue":       round(float(r[3] or 0), 2),
            "total_orders":         int(r[4] or 0),
        }
        for r in attr_rows
    ]
    total_linear = sum(a["linear_revenue"] for a in attribution)
    blended_roas = round(total_linear / t_sp, 2) if t_sp else 0.0

    # ── Channel performance ───────────────────────────────────────────────────
    ch_rows = con.execute("""
        WITH spend_agg AS (
            SELECT 'google_ads' AS channel, SUM(cost)  AS total_spend
            FROM stg_google_ads_performance WHERE CAST(date AS DATE) BETWEEN ? AND ?
            UNION ALL
            SELECT 'meta_ads',              SUM(spend) AS total_spend
            FROM stg_meta_ads_performance   WHERE CAST(date AS DATE) BETWEEN ? AND ?
        ),
        rev AS (
            SELECT
                CASE WHEN channel LIKE 'google_ads%' THEN 'google_ads'
                     WHEN channel LIKE 'meta_%'      THEN 'meta_ads'
                     ELSE channel END AS channel,
                SUM(linear_credit * order_revenue)  AS linear_revenue,
                COUNT(DISTINCT order_id)            AS total_orders
            FROM stg_marketing_attribution
            WHERE CAST(touchpoint_date AS DATE) BETWEEN ? AND ?
            GROUP BY 1
        )
        SELECT s.channel,
               COALESCE(s.total_spend, 0)                                     AS total_spend,
               COALESCE(r.linear_revenue, 0)                                  AS attributed_revenue,
               COALESCE(r.total_orders, 0)                                    AS total_orders,
               COALESCE(s.total_spend / NULLIF(r.total_orders, 0), 0)         AS cac,
               COALESCE(r.linear_revenue / NULLIF(s.total_spend, 0), 0)       AS roas
        FROM spend_agg s
        LEFT JOIN rev r ON s.channel = r.channel
        ORDER BY attributed_revenue DESC
    """, [ws, we, ws, we, ws, we]).fetchall()
    channel_perf = [
        {
            "channel":            r[0],
            "total_spend":        round(float(r[1] or 0), 2),
            "attributed_revenue": round(float(r[2] or 0), 2),
            "total_orders":       int(r[3] or 0),
            "cac":                round(float(r[4] or 0), 2),
            "roas":               round(float(r[5] or 0), 2),
        }
        for r in ch_rows
    ]

    # ── GA4 by channel ────────────────────────────────────────────────────────
    ga4_rows = con.execute("""
        SELECT channel_group,
               SUM(sessions) AS s, SUM(engaged_sessions) AS e, SUM(conversions) AS c
        FROM stg_ga4_sessions
        WHERE CAST(date AS DATE) BETWEEN ? AND ?
        GROUP BY channel_group ORDER BY s DESC
    """, [ws, we]).fetchall()
    total_sess = sum(float(r[1] or 0) for r in ga4_rows)
    ga4_by_ch = [
        {
            "channel":             r[0],
            "sessions":            int(r[1] or 0),
            "engaged_sessions":    int(r[2] or 0),
            "conversions":         int(r[3] or 0),
            "session_cvr_pct":     _session_cvr(float(r[3] or 0), float(r[1] or 0)),
            "engagement_rate_pct": round(float(r[2] or 0) / float(r[1] or 1) * 100, 2),
            "session_share_pct":   round(float(r[1] or 0) / total_sess * 100, 1) if total_sess else 0.0,
        }
        for r in ga4_rows
    ]

    # ── Campaigns — Google ────────────────────────────────────────────────────
    g_camps = con.execute("""
        SELECT campaign_name, campaign_type,
               SUM(impressions), SUM(clicks), SUM(cost), SUM(conversions)
        FROM stg_google_ads_performance
        WHERE CAST(date AS DATE) BETWEEN ? AND ?
        GROUP BY 1, 2 ORDER BY SUM(cost) DESC
    """, [ws, we]).fetchall()
    google_camps = [
        {
            "campaign_name": r[0], "campaign_type": r[1],
            "impressions":   int(r[2] or 0), "clicks":   int(r[3] or 0),
            "cost":          round(float(r[4] or 0), 2),
            "conversions":   int(r[5] or 0),
            "ctr_pct":       round(float(r[3] or 0) / float(r[2] or 1) * 100, 2),
            "click_cvr_pct": round(float(r[5] or 0) / float(r[3] or 1) * 100, 2),
            "roas":          _google_roas(float(r[5] or 0), float(r[4] or 0)),
        }
        for r in g_camps
    ]

    # ── Campaigns — Meta ──────────────────────────────────────────────────────
    m_camps = con.execute("""
        SELECT campaign_name, objective,
               SUM(impressions), SUM(link_clicks), SUM(spend), SUM(purchases),
               SUM(purchases * 100.0) / NULLIF(SUM(spend), 0) AS platform_roas
        FROM stg_meta_ads_performance
        WHERE CAST(date AS DATE) BETWEEN ? AND ?
        GROUP BY 1, 2 ORDER BY SUM(spend) DESC
    """, [ws, we]).fetchall()
    meta_camps = [
        {
            "campaign_name": r[0], "objective": r[1],
            "impressions":   int(r[2] or 0), "link_clicks": int(r[3] or 0),
            "spend":         round(float(r[4] or 0), 2),
            "purchases":     int(r[5] or 0),
            "cpm":           round(float(r[4] or 0) / float(r[2] or 1) * 1000, 2),
            "click_cvr_pct": round(float(r[5] or 0) / float(r[3] or 1) * 100, 2),
            "roas":          round(float(r[6] or 0), 2),
        }
        for r in m_camps
    ]

    # ── CRM — always all-time (CLAUDE.md §1, §5) ─────────────────────────────
    hs_stages = con.execute("""
        SELECT deal_stage, COUNT(*) AS deal_count, SUM(amount) AS total_value
        FROM stg_hubspot_deals GROUP BY deal_stage ORDER BY total_value DESC
    """).fetchall()
    hs_contacts = con.execute("SELECT COUNT(*) FROM stg_hubspot_contacts").fetchone()[0]

    sf_stages = con.execute("""
        SELECT stage, COUNT(*) AS opp_count, SUM(amount) AS total_value,
               SUM(weighted_amount) AS expected_revenue
        FROM stg_salesforce_opportunities
        GROUP BY stage ORDER BY total_value DESC
    """).fetchall()
    sf_sources = con.execute("""
        SELECT lead_source, SUM(amount) AS revenue, COUNT(*) AS won_count
        FROM stg_salesforce_opportunities WHERE is_won = TRUE
        GROUP BY lead_source ORDER BY revenue DESC
    """).fetchall()
    sf_closed_won = con.execute(
        "SELECT SUM(amount) FROM stg_salesforce_opportunities WHERE is_won = TRUE"
    ).fetchone()[0]

    return {
        "label":  label,
        "window": {"start": _fd(start), "end": _fd(end)},
        "spend": {
            "google": round(g_sp, 2),
            "meta":   round(m_sp, 2),
            "total":  round(t_sp, 2),
        },
        "sessions": {
            "total":               int(sess),
            "engaged":             int(eng),
            "engagement_rate_pct": round(eng / sess * 100, 2) if sess else 0.0,
        },
        "conversions": {
            "ga4_total":       int(ga4_conv),
            "ad_platform":     int(ad_conv),
            "session_cvr_pct": _session_cvr(ga4_conv, sess),
        },
        "blended_roas":           blended_roas,
        "channel_performance":    channel_perf,
        "attribution_by_channel": attribution,
        "ga4_by_channel":         ga4_by_ch,
        "campaigns": {
            "google": google_camps,
            "meta":   meta_camps,
        },
        "crm": {
            "_note": "CRM data is always all-time (lifetime count). "
                     "Not filtered to the query window. See CLAUDE.md §1, §5.",
            "hubspot": {
                "total_contacts": int(hs_contacts),
                "total_pipeline_value": round(
                    sum(float(r[2] or 0) for r in hs_stages), 2
                ),
                "pipeline_by_stage": [
                    {"stage": r[0], "deal_count": int(r[1]),
                     "total_value": round(float(r[2] or 0), 2)}
                    for r in hs_stages
                ],
            },
            "salesforce": {
                "closed_won_revenue": round(float(sf_closed_won or 0), 2),
                "pipeline_by_stage": [
                    {"stage": r[0], "opp_count": int(r[1]),
                     "total_value": round(float(r[2] or 0), 2),
                     "expected_revenue": round(float(r[3] or 0), 2)}
                    for r in sf_stages
                ],
                "closed_won_by_source": [
                    {"lead_source": r[0],
                     "revenue":    round(float(r[1] or 0), 2),
                     "won_count":  int(r[2])}
                    for r in sf_sources
                ],
            },
        },
    }


def query_window(start: date, end: date, label: str | None = None) -> dict:
    """
    Python API: query metrics for any date window.

    Returns a dict with the same schema as a golden_metrics.json section.
    CRM data is always all-time (not filtered to the window).

    Example:
        from datetime import date
        from scripts.query_window import query_window
        section = query_window(date(2026, 1, 1), date(2026, 3, 15))
        print(section["blended_roas"])
    """
    if label is None:
        label = f"Ad-hoc window {_fd(start)} → {_fd(end)}"
    con = build_csv_connection()
    return build_window_section(con, start, end, label)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Query marketing metrics for any date window.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/query_window.py --last-days 30
  python scripts/query_window.py --last-days 1
  python scripts/query_window.py --month 2026-02
  python scripts/query_window.py --year 2025
  python scripts/query_window.py --start 2025-09-16 --end 2026-03-15
  python scripts/query_window.py --last-days 60 --output metrics_60d.json
        """,
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--last-days", type=int, metavar="N",
                       help="N days ending at the anchor date (2026-03-15)")
    group.add_argument("--month", metavar="YYYY-MM",
                       help="Full calendar month (e.g. 2026-02)")
    group.add_argument("--year", type=int, metavar="YYYY",
                       help="Full calendar year (e.g. 2025)")
    parser.add_argument("--start", metavar="YYYY-MM-DD",
                        help="Window start (requires --end)")
    parser.add_argument("--end",   metavar="YYYY-MM-DD",
                        help="Window end (requires --start)")
    parser.add_argument("--output", metavar="FILE",
                        help="Write JSON output to FILE (default: stdout)")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="Suppress summary line; print only JSON")

    args = parser.parse_args()

    try:
        start, end, label = parse_window(args)
    except ValueError as exc:
        parser.error(str(exc))
        return 1

    if not args.quiet:
        print(f"Querying: {label}", file=sys.stderr)

    con     = build_csv_connection()
    section = build_window_section(con, start, end, label)
    con.close()

    output = json.dumps(section, indent=2, ensure_ascii=False)

    if args.output:
        Path(args.output).write_text(output)
        if not args.quiet:
            print(f"✅ Written: {args.output}", file=sys.stderr)
            print(f"   Sessions: {section['sessions']['total']:,}"
                  f"  |  Spend: ${section['spend']['total']:,.2f}"
                  f"  |  ROAS: {section['blended_roas']}x"
                  f"  |  CVR: {section['conversions']['session_cvr_pct']}%",
                  file=sys.stderr)
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
