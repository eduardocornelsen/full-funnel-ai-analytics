"""
daily_synthetic_append.py
──────────────────────────────────────────────────────────────────────────────
Appends realistic synthetic data for N new days to ALL time-series tables:
  - data/mock_marketing/google_ads_daily_performance.csv
  - data/mock_marketing/meta_ads_daily_performance.csv
  - data/mock_marketing/ga4_daily_sessions.csv
  - data/mock_marketing/marketing_attribution.csv      (revenue for blended ROAS)
  - data/mock_marketing/hubspot_deals.csv
  - data/mock_marketing/hubspot_contacts.csv
  - data/mock_marketing/salesforce_opportunities.csv

Every table advances to the same target end date, each backfilling from its own
last date — so a table that fell behind (or was historically frozen) heals
automatically on the next run.

Postmortem (2026-07): an earlier version appended only the 3 ad/GA4 tables.
Spend kept growing daily while attribution revenue and CRM data stayed frozen,
which would have made blended ROAS collapse toward 0 in any recent window.
If you add a new time-series table, it MUST be appended here too.

Values are seeded per calendar date (same day = same data) with day-of-week and
monthly seasonality — a live-feed simulation with no external connection.

Usage:
    python scripts/daily_synthetic_append.py              # append 1 day
    python scripts/daily_synthetic_append.py --days 7    # backfill 7 days
    python scripts/daily_synthetic_append.py --reset     # regenerate full baseline

After running, re-run dbt + generate_golden_metrics.py:
    dbt run --target duckdb
    python scripts/generate_golden_metrics.py --live
"""

import argparse
import subprocess
import sys
from pathlib import Path
from datetime import date, timedelta

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent
MOCK_DIR = PROJECT_ROOT / "data" / "mock_marketing"

# Reproducible per-session noise (seed per calendar date so same day = same data)
# `salt` decorrelates the tables that share a date without breaking determinism.
def _rng(seed_date: date, salt: int = 0) -> np.random.Generator:
    seed = int(seed_date.strftime("%Y%m%d")) + salt
    return np.random.default_rng(seed)


# ── Seasonality helpers ────────────────────────────────────────────────────────

_MONTH_FACTOR = {1: 0.70, 2: 0.85, 3: 0.95, 4: 1.00, 5: 1.10, 6: 1.10,
                 7: 1.00, 8: 0.95, 9: 1.00, 10: 1.10, 11: 1.80, 12: 1.40}


def _season(d: date) -> float:
    dow = 0.80 if d.weekday() >= 5 else 1.00
    return _MONTH_FACTOR.get(d.month, 1.0) * dow


# ── Google Ads ─────────────────────────────────────────────────────────────────

_GOOGLE_CAMPAIGNS = [
    {"campaign_id": "C001", "campaign_name": "Brand - Olist",             "campaign_type": "SEARCH",   "daily_budget": 150.0},
    {"campaign_id": "C002", "campaign_name": "Generic - Electronics",     "campaign_type": "SEARCH",   "daily_budget": 300.0},
    {"campaign_id": "C003", "campaign_name": "Generic - Home & Garden",   "campaign_type": "SEARCH",   "daily_budget": 250.0},
    {"campaign_id": "C004", "campaign_name": "Shopping - All Products",   "campaign_type": "SHOPPING", "daily_budget": 400.0},
    {"campaign_id": "C005", "campaign_name": "Display - Retargeting",     "campaign_type": "DISPLAY",  "daily_budget": 200.0},
    {"campaign_id": "C006", "campaign_name": "YouTube - Brand Awareness", "campaign_type": "VIDEO",    "daily_budget": 100.0},
]

_GOOGLE_BASE_IMP  = {"SEARCH": 5000, "SHOPPING": 8000, "DISPLAY": 20000, "VIDEO": 15000}
_GOOGLE_CTR       = {"SEARCH": 0.035, "SHOPPING": 0.020, "DISPLAY": 0.005, "VIDEO": 0.012}
_GOOGLE_CPC       = {"SEARCH": 0.85,  "SHOPPING": 0.45,  "DISPLAY": 0.25,  "VIDEO": 0.15}
_GOOGLE_CONV_RATE = {"SEARCH": 0.028, "SHOPPING": 0.022, "DISPLAY": 0.008, "VIDEO": 0.003}


def _google_day(d: date) -> list[dict]:
    rng = _rng(d)
    sf = _season(d)
    rows = []
    for c in _GOOGLE_CAMPAIGNS:
        ct = c["campaign_type"]
        imp   = int(_GOOGLE_BASE_IMP[ct]  * sf * rng.uniform(0.7, 1.3))
        ctr   = _GOOGLE_CTR[ct] * rng.uniform(0.8, 1.2)
        clicks = int(imp * ctr)
        cpc   = _GOOGLE_CPC[ct] * rng.uniform(0.7, 1.4) * sf
        cost  = round(min(clicks * cpc, c["daily_budget"] * rng.uniform(0.9, 1.1)), 2)
        cvr   = _GOOGLE_CONV_RATE[ct] * rng.uniform(0.6, 1.5)
        conv  = int(clicks * cvr)
        conv_val = round(conv * rng.uniform(80, 250), 2)
        rows.append({
            "date": d.isoformat(),
            "campaign_id": c["campaign_id"],
            "campaign_name": c["campaign_name"],
            "campaign_type": ct,
            "impressions": imp,
            "clicks": clicks,
            "cost": cost,
            "conversions": conv,
            "conversion_value": conv_val,
            "ctr": round(ctr * 100, 2),
            "avg_cpc": round(cost / max(clicks, 1), 2),
            "cost_per_conversion": round(cost / max(conv, 1), 2),
            "roas": round(conv_val / max(cost, 0.01), 2),
        })
    return rows


# ── Meta Ads ───────────────────────────────────────────────────────────────────

_META_CAMPAIGNS = [
    {"campaign_id": "META_C001", "campaign_name": "Prospecting - Lookalike Purchasers", "objective": "CONVERSIONS",   "daily_budget": 250.0},
    {"campaign_id": "META_C002", "campaign_name": "Retargeting - Add to Cart",          "objective": "CONVERSIONS",   "daily_budget": 150.0},
    {"campaign_id": "META_C003", "campaign_name": "Brand Awareness - Video",            "objective": "AWARENESS",     "daily_budget": 100.0},
    {"campaign_id": "META_C004", "campaign_name": "Catalog Sales - Dynamic",            "objective": "CATALOG_SALES", "daily_budget": 300.0},
    {"campaign_id": "META_C005", "campaign_name": "Instagram Stories - Flash Sales",    "objective": "CONVERSIONS",   "daily_budget": 200.0},
]


def _meta_day(d: date) -> list[dict]:
    rng = _rng(d)
    sf = _season(d)
    rows = []
    for c in _META_CAMPAIGNS:
        imp     = int(rng.uniform(8000, 30000) * sf)
        reach   = int(imp * rng.uniform(0.60, 0.85))
        cpm     = rng.uniform(4.0, 12.0) * sf
        spend   = round(min((imp / 1000) * cpm, c["daily_budget"] * rng.uniform(0.85, 1.05)), 2)
        clicks  = int(imp * rng.uniform(0.008, 0.025))
        purch   = int(clicks * rng.uniform(0.010, 0.060))
        pval    = round(purch * rng.uniform(90, 200), 2)
        rows.append({
            "date": d.isoformat(),
            "campaign_id": c["campaign_id"],
            "campaign_name": c["campaign_name"],
            "objective": c["objective"],
            "impressions": imp,
            "reach": reach,
            "spend": spend,
            "link_clicks": clicks,
            "ctr": round((clicks / max(imp, 1)) * 100, 2),
            "cpc": round(spend / max(clicks, 1), 2),
            "cpm": round(cpm, 2),
            "purchases": purch,
            "purchase_value": pval,
            "cost_per_purchase": round(spend / max(purch, 1), 2),
            "roas": round(pval / max(spend, 0.01), 2),
        })
    return rows


# ── GA4 ───────────────────────────────────────────────────────────────────────

_GA4_CHANNELS = ["organic_search", "paid_search", "paid_social", "direct",
                 "email", "referral", "organic_social"]
_GA4_WEIGHTS  = [0.25, 0.20, 0.18, 0.15, 0.10, 0.07, 0.05]
_GA4_DEVICES  = ["mobile", "desktop", "tablet"]
_GA4_DEV_W    = [0.55, 0.35, 0.10]
_GA4_BOUNCE   = {"organic_search": 0.45, "paid_search": 0.38, "paid_social": 0.55,
                 "direct": 0.30, "email": 0.25, "referral": 0.50, "organic_social": 0.60}
_GA4_CVR      = {"organic_search": 0.025, "paid_search": 0.032, "paid_social": 0.018,
                 "direct": 0.035, "email": 0.042, "referral": 0.020, "organic_social": 0.012}


def _ga4_day(d: date) -> list[dict]:
    rng = _rng(d)
    sf = _season(d)
    rows = []
    for ch, cw in zip(_GA4_CHANNELS, _GA4_WEIGHTS):
        for dev, dw in zip(_GA4_DEVICES, _GA4_DEV_W):
            sess = int(500 * cw * dw * sf * rng.uniform(0.7, 1.3) * 10)
            br   = _GA4_BOUNCE[ch] * rng.uniform(0.85, 1.15)
            eng  = int(sess * (1 - br))
            conv = int(sess * _GA4_CVR[ch] * rng.uniform(0.7, 1.3))
            rev  = round(conv * rng.uniform(80, 220), 2)
            rows.append({
                "date": d.isoformat(),
                "channel_group": ch,
                "device_category": dev,
                "sessions": sess,
                "engaged_sessions": eng,
                "bounce_rate": round(br * 100, 1),
                "avg_session_duration_sec": round(float(rng.uniform(60, 300)) * (1 - br * 0.5), 0),
                "pages_per_session": round(float(rng.uniform(1.5, 6.0)) * (1 - br * 0.3), 1),
                "new_users": int(sess * rng.uniform(0.5, 0.8)),
                "conversions": conv,
                "revenue": rev,
                "conversion_rate": round((conv / max(sess, 1)) * 100, 2),
            })
    return rows


# ── Marketing attribution ─────────────────────────────────────────────────────
# Touchpoint-level rows feeding blended / channel ROAS. Channel mix and
# touchpoint-count distribution mirror the committed baseline data.

_ATT_CHANNELS = [
    ("google_ads_search",   "google_ads", 0.223),
    ("meta_prospecting",    "meta_ads",   0.176),
    ("google_ads_shopping", "google_ads", 0.153),
    ("organic_search",      "ga4",        0.152),
    ("meta_retargeting",    "meta_ads",   0.108),
    ("direct",              "ga4",        0.099),
    ("email_marketing",     "hubspot",    0.089),
]
_ATT_TOUCH_COUNTS  = [1, 2, 3, 4]
_ATT_TOUCH_WEIGHTS = [0.14, 0.33, 0.35, 0.18]


def _attribution_day(d: date) -> list[dict]:
    rng = _rng(d, salt=1)
    sf = _season(d)
    n_orders = int(70 * sf * rng.uniform(0.85, 1.15))
    ch_names   = [c[0] for c in _ATT_CHANNELS]
    ch_weights = np.array([c[2] for c in _ATT_CHANNELS])
    ch_weights = ch_weights / ch_weights.sum()
    platform_of = {c[0]: c[1] for c in _ATT_CHANNELS}

    rows = []
    for i in range(n_orders):
        order_id = f"syn{d.strftime('%Y%m%d')}{i:04d}"
        revenue  = round(float(rng.uniform(45, 340)), 2)
        touches  = int(rng.choice(_ATT_TOUCH_COUNTS, p=_ATT_TOUCH_WEIGHTS))
        channels = rng.choice(ch_names, size=touches, p=ch_weights)
        # Touchpoints lead up to the order date; the last one lands on it.
        offsets = sorted(rng.integers(0, 7, size=touches), reverse=True)
        offsets[-1] = 0
        for pos in range(touches):
            rows.append({
                "order_id":            order_id,
                "touchpoint_position": pos + 1,
                "total_touchpoints":   touches,
                "channel":             str(channels[pos]),
                "platform":            platform_of[str(channels[pos])],
                "touchpoint_date":     (d - timedelta(days=int(offsets[pos]))).isoformat(),
                "order_date":          d.isoformat(),
                "order_revenue":       revenue,
                "first_touch_credit":  1.0 if pos == 0 else 0.0,
                "last_touch_credit":   1.0 if pos == touches - 1 else 0.0,
                "linear_credit":       round(1.0 / touches, 4),
            })
    return rows


# ── HubSpot ────────────────────────────────────────────────────────────────────

_HS_STAGES = [
    ("closed_won",             0.653),
    ("prospecting",            0.118),
    ("qualified",              0.078),
    ("presentation_scheduled", 0.052),
    ("proposal_sent",          0.039),
    ("closed_lost",            0.033),
    ("negotiation",            0.027),
]
_HS_LEAD_SOURCES = ["referral", "organic_search", "paid_search", "email",
                    "paid_social", "direct", "social"]
_BR_CITIES = [("sao paulo", "SP"), ("rio de janeiro", "RJ"), ("belo horizonte", "MG"),
              ("curitiba", "PR"), ("porto alegre", "RS"), ("campinas", "SP"),
              ("salvador", "BA"), ("fortaleza", "CE")]
_FIRST_NAMES = ["Ana", "Bruno", "Carla", "Diego", "Elena", "Felipe", "Gabriela",
                "Hugo", "Isabela", "Joao", "Larissa", "Marcos"]
_LAST_NAMES  = ["Silva", "Santos", "Oliveira", "Souza", "Costa", "Pereira",
                "Almeida", "Lima", "Gomes", "Ribeiro"]


def _hubspot_deals_day(d: date) -> list[dict]:
    rng = _rng(d, salt=2)
    sf = _season(d)
    n = int(135 * sf * rng.uniform(0.85, 1.15))
    stages  = [s[0] for s in _HS_STAGES]
    weights = np.array([s[1] for s in _HS_STAGES]); weights /= weights.sum()
    rows = []
    for i in range(n):
        stage  = str(rng.choice(stages, p=weights))
        amount = round(float(rng.uniform(40, 330)), 2)
        closed = stage.startswith("closed")
        order_id = f"syn{d.strftime('%Y%m%d')}{i:04d}"
        rows.append({
            "deal_id":    f"DEAL_SYN_{d.strftime('%Y%m%d')}_{i:05d}",
            "order_id":   order_id,
            "deal_name":  f"Order {order_id[:11]}",
            "deal_stage": stage,
            "pipeline":   "default",
            "amount":     amount,
            "create_date": d.isoformat(),
            "close_date":  d.isoformat() if closed else "",
            "deal_type":   str(rng.choice(["new_business", "existing_business"], p=[0.8, 0.2])),
            "lead_source": str(rng.choice(_HS_LEAD_SOURCES)),
        })
    return rows


def _hubspot_contacts_day(d: date) -> list[dict]:
    rng = _rng(d, salt=3)
    sf = _season(d)
    n = int(125 * sf * rng.uniform(0.85, 1.15))
    rows = []
    for i in range(n):
        first = str(rng.choice(_FIRST_NAMES))
        last  = str(rng.choice(_LAST_NAMES))
        city, state = _BR_CITIES[int(rng.integers(0, len(_BR_CITIES)))]
        num_orders = int(rng.choice([1, 2, 3], p=[0.75, 0.18, 0.07]))
        rows.append({
            "contact_id":       f"HS_SYN_{d.strftime('%Y%m%d')}_{i:05d}",
            "customer_id":      f"syncust{d.strftime('%Y%m%d')}{i:05d}",
            "email":            f"{first.lower()}.{last.lower()}{d.strftime('%y%m%d')}{i}@example.com",
            "first_name":       first,
            "last_name":        last,
            "city":             city,
            "state":            state,
            "create_date":      d.isoformat(),
            "lifecycle_stage":  "customer",
            "lead_source":      str(rng.choice(_HS_LEAD_SOURCES[:6])),
            "num_orders":       num_orders,
            "total_revenue":    round(float(rng.uniform(45, 340)) * num_orders, 2),
            "first_order_date": d.isoformat(),
            "last_activity_date": d.isoformat(),
        })
    return rows


# ── Salesforce ─────────────────────────────────────────────────────────────────

_SF_STAGES = [
    ("Closed Won",           1.00, 0.676),
    ("Prospecting",          0.10, 0.101),
    ("Qualification",        0.20, 0.068),
    ("Needs Analysis",       0.30, 0.047),
    ("Value Proposition",    0.50, 0.034),
    ("Proposal/Price Quote", 0.65, 0.027),
    ("Closed Lost",          0.00, 0.027),
    ("Negotiation/Review",   0.80, 0.020),
]
_SF_LEAD_SOURCES = ["Email", "Referral", "Direct", "Web", "Paid Search",
                    "Social Media", "Phone", "Partner", "Other"]


def _salesforce_day(d: date) -> list[dict]:
    rng = _rng(d, salt=4)
    sf = _season(d)
    n = int(100 * sf * rng.uniform(0.85, 1.15))
    stages  = [(s[0], s[1]) for s in _SF_STAGES]
    weights = np.array([s[2] for s in _SF_STAGES]); weights /= weights.sum()
    rows = []
    for i in range(n):
        idx = int(rng.choice(len(stages), p=weights))
        stage, prob = stages[idx]
        amount = round(float(rng.uniform(40, 340)), 2)
        closed = stage.startswith("Closed")
        close_d = d if closed else d + timedelta(days=int(rng.integers(7, 60)))
        rows.append({
            "opportunity_id":   f"OPP_SYN_{d.strftime('%Y%m%d')}_{i:05d}",
            "order_id":         f"syn{d.strftime('%Y%m%d')}{i:04d}",
            "opportunity_name": f"Deal syn{d.strftime('%Y%m%d')}{i:04d}",
            "stage":            stage,
            "probability":      prob,
            "amount":           amount,
            "created_date":     d.isoformat(),
            "close_date":       close_d.isoformat(),
            "lead_source":      str(rng.choice(_SF_LEAD_SOURCES)),
            "type":             str(rng.choice(["New Business", "Existing Business"], p=[0.8, 0.2])),
            "fiscal_quarter":   f"Q{(close_d.month - 1) // 3 + 1} {close_d.year}",
            "expected_revenue": round(amount * prob, 2),
        })
    return rows


# ── I/O helpers ────────────────────────────────────────────────────────────────

def _last_date(csv_path: Path, column: str = "date") -> date | None:
    if not csv_path.exists():
        return None
    df = pd.read_csv(csv_path, usecols=[column])
    if df.empty:
        return None
    return pd.to_datetime(df[column], errors="coerce").max().date()


def _append_rows(csv_path: Path, rows: list[dict]) -> None:
    df_new = pd.DataFrame(rows)
    if csv_path.exists():
        df_new.to_csv(csv_path, mode="a", header=False, index=False)
    else:
        MOCK_DIR.mkdir(parents=True, exist_ok=True)
        df_new.to_csv(csv_path, index=False)


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Append daily synthetic marketing data rows."
    )
    parser.add_argument("--days", type=int, default=1,
                        help="Number of days to append (default: 1)")
    parser.add_argument("--reset", action="store_true",
                        help="Regenerate full dataset from scratch (delegates to generate_mock_marketing_data.py)")
    args = parser.parse_args()

    if args.reset:
        print("Delegating to generate_mock_marketing_data.py for full reset ...")
        subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "generate_mock_marketing_data.py")],
            check=True,
        )
        return

    # Every time-series table this feed maintains: (path, date column, generator).
    # A table missing from this list silently freezes while spend keeps growing —
    # that exact bug broke blended ROAS for post-2026-03 windows (see module docstring).
    tables = [
        (MOCK_DIR / "google_ads_daily_performance.csv", "date",         _google_day),
        (MOCK_DIR / "meta_ads_daily_performance.csv",   "date",         _meta_day),
        (MOCK_DIR / "ga4_daily_sessions.csv",           "date",         _ga4_day),
        (MOCK_DIR / "marketing_attribution.csv",        "order_date",   _attribution_day),
        (MOCK_DIR / "hubspot_deals.csv",                "create_date",  _hubspot_deals_day),
        (MOCK_DIR / "hubspot_contacts.csv",             "create_date",  _hubspot_contacts_day),
        (MOCK_DIR / "salesforce_opportunities.csv",     "created_date", _salesforce_day),
    ]

    # All tables advance to one shared target end date, each backfilling from its
    # own last date — a table that fell behind heals on the next run.
    lead_last = (_last_date(tables[0][0]) or date(2026, 3, 15))
    target_end = lead_last + timedelta(days=args.days)
    print(f"Target end date for all tables: {target_end}")

    for csv_path, date_col, generator in tables:
        last = _last_date(csv_path, date_col) or (target_end - timedelta(days=args.days))
        if last >= target_end:
            print(f"   {csv_path.name}: already at {last}, nothing to append")
            continue
        dates = pd.date_range(last + timedelta(days=1), target_end).date
        rows: list[dict] = []
        for d in dates:
            rows.extend(generator(d))
        _append_rows(csv_path, rows)
        print(f"   {csv_path.name}: +{len(rows)} rows ({dates[0]} → {dates[-1]})")

    print(f"\n✅ All tables now run through {target_end}")
    print()
    print("Next steps:")
    print("  dbt run --target duckdb")
    print("  python scripts/generate_golden_metrics.py")


if __name__ == "__main__":
    main()
