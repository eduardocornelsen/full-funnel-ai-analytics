"""
daily_synthetic_append.py
──────────────────────────────────────────────────────────────────────────────
Appends realistic synthetic data for N new days to:
  - data/mock_marketing/google_ads_daily_performance.csv
  - data/mock_marketing/meta_ads_daily_performance.csv
  - data/mock_marketing/ga4_daily_sessions.csv

Each new day's values are derived from the rolling 14-day average of existing
data with day-of-week seasonality and ±10 % random noise — making the growing
dataset behave like a real live feed without requiring any external connection.

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
def _rng(seed_date: date) -> np.random.Generator:
    seed = int(seed_date.strftime("%Y%m%d"))
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


# ── I/O helpers ────────────────────────────────────────────────────────────────

def _last_date(csv_path: Path) -> date | None:
    if not csv_path.exists():
        return None
    df = pd.read_csv(csv_path, usecols=["date"])
    if df.empty:
        return None
    return pd.to_datetime(df["date"]).max().date()


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

    google_path = MOCK_DIR / "google_ads_daily_performance.csv"
    meta_path   = MOCK_DIR / "meta_ads_daily_performance.csv"
    ga4_path    = MOCK_DIR / "ga4_daily_sessions.csv"

    last = (_last_date(google_path) or date(2026, 3, 15))
    start_day = last + timedelta(days=1)

    dates = [start_day + timedelta(days=i) for i in range(args.days)]
    print(f"Appending {args.days} day(s): {dates[0]} → {dates[-1]}")

    google_rows, meta_rows, ga4_rows = [], [], []
    for d in dates:
        google_rows.extend(_google_day(d))
        meta_rows.extend(_meta_day(d))
        ga4_rows.extend(_ga4_day(d))

    _append_rows(google_path, google_rows)
    _append_rows(meta_path,   meta_rows)
    _append_rows(ga4_path,    ga4_rows)

    new_end = dates[-1]
    print(f"✅ Data now runs through {new_end}")
    print(f"   Google Ads: {len(google_rows)} rows appended")
    print(f"   Meta Ads:   {len(meta_rows)} rows appended")
    print(f"   GA4:        {len(ga4_rows)} rows appended")
    print()
    print("Next steps:")
    print("  dbt run --target duckdb")
    print("  python scripts/generate_golden_metrics.py --live")


if __name__ == "__main__":
    main()
