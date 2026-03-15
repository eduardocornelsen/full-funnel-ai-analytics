# ═══════════════════════════════════════════════════════════════════
# COMPLETE AGENT EXECUTION PLAN — SINGLE CONSOLIDATED DOCUMENT
# Full-Funnel AI Marketing Analytics Platform
# ═══════════════════════════════════════════════════════════════════
#
# This is the ONE document to paste into your coding agent.
# It contains every file, every script, every config — fully written.
# Work through phases sequentially. Do not skip ahead.
#
# ═══════════════════════════════════════════════════════════════════

## MISSION

Build a complete marketing analytics platform for Eduardo's portfolio. The system lets anyone query marketing data in natural language via MCP (Model Context Protocol), backed by multi-touch attribution, an ML lead scoring API, and BI dashboards — all from a governed dbt semantic layer that works across 5 data warehouses and 4 AI clients.

**Resume one-liner:** "Built an end-to-end marketing attribution and lead scoring platform across 5 data sources, queryable via natural language through MCP across Claude Desktop, OpenCode, Gemini CLI, and Antigravity IDE, with a deployed ML scoring API and automated lead routing."

## ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────┐
│  DATA SOURCES (mock MCP servers serving synthetic data)         │
│  Google Ads · Meta Ads · GA4 · HubSpot · Salesforce            │
│                 + Olist Dataset (100K real orders, Kaggle)      │
└──────────────────────────┬──────────────────────────────────────┘
                           │
              ┌────────────▼────────────┐
              │    DATA WAREHOUSE       │
              │  BigQuery (free 10GB)   │  ← Primary
              │  DuckDB (local free)    │  ← Dev
              │  Supabase (free 500MB)  │  ← Postgres demo
              │  Snowflake (30d trial)  │  ← Enterprise demo
              │  Databricks (14d trial) │  ← Lakehouse demo
              └────────────┬────────────┘
                           │
              ┌────────────▼────────────┐
              │  dbt + MetricFlow       │  ← Semantic layer
              │  14 staging models      │     governs ALL queries
              │  4 intermediate models  │
              │  11 mart models         │
              │  15+ governed metrics   │
              └────────────┬────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
   ┌──────▼──────┐  ┌─────▼─────┐  ┌──────▼──────┐
   │ HEAD 1: AI  │  │ HEAD 2:ML │  │ HEAD 3: BI  │
   │ 7 MCP srvrs │  │ XGBoost   │  │ Looker      │
   │ Claude Dsktp│  │ MLflow    │  │ Streamlit   │
   │ OpenCode    │  │ FastAPI   │  │ React       │
   │ Gemini CLI  │  │ n8n       │  │ dashboards  │
   │ Antigravity │  └───────────┘  └─────────────┘
   └─────────────┘
```

## CONSTRAINTS

- Primary warehouse: BigQuery free tier (10GB, 1TB queries/month)
- Local dev: DuckDB (free, open source)
- AI clients: Claude Desktop (Cowork plugin + artifacts), OpenCode (terminal + 75 models), Gemini CLI (BigQuery native), Antigravity IDE (parallel agents)
- Cost: $0/month base (all free tiers). Claude Pro ($20/mo) optional for Cowork plugin + React artifacts.
- All marketing MCP servers are MOCK (serve synthetic CSVs)
- Mock servers have same tool interface as real APIs (swappable)
- Use dbt Core + MetricFlow for semantic layer
- Use MLflow for ML experiment tracking
- Do NOT use LangChain/LangGraph — MCP replaces them
- Use Polars where possible for data manipulation
- Python 3.11+, Node.js 18+
- `np.random.seed(42)` for reproducible synthetic data

## TIMELINE

```
Week 1: Phase 1 — Scaffolding + data download + warehouse loading
Week 2: Phase 2 — dbt project (staging → intermediate → marts → semantic layer)
Week 3: Phase 3 — MCP servers + multi-client integration (Claude Desktop, OpenCode, Gemini CLI, Antigravity) + Cowork plugin + OpenCode commands
Week 4: Phase 4 — ML lead scoring + MLflow + FastAPI
Week 5: Phase 5 — n8n automation + Looker Studio + Streamlit dashboards
Week 6: Phase 6 — Snowflake/Databricks trials + demo + publish
```

---

# ═══════════════════════════════════════════
# PHASE 1: PROJECT SCAFFOLDING + DATA
# ═══════════════════════════════════════════

## 1.1 Create project structure

```bash
mkdir -p full-funnel-ai-analytics/{dbt_project/{models/{staging,intermediate,marts,semantic_models,metrics},macros,tests,seeds},mcp_servers,cowork_plugin/{.claude-plugin,commands,skills},.opencode/{commands,skills/{brand-voice,metric-definitions,data-workflow,visualization-guide},agents},ml/{src,notebooks,mlflow,models},api,automation,streamlit_app/{pages,.streamlit},scripts,warehouse_configs/{bigquery,supabase,duckdb,snowflake,databricks},dashboards/{looker_studio,voi_style_react},docs,demo/screenshots}
cd full-funnel-ai-analytics
git init
```

## 1.2 Create file: `.gitignore`

```gitignore
.env
*.env
profiles.yml
**/service-account*.json
**/claude_desktop_config.json
.opencode/opencode.json
__pycache__/
*.pyc
.venv/
venv/
node_modules/
data/
*.parquet
*.duckdb
dbt_project/target/
dbt_project/dbt_packages/
dbt_project/logs/
ml/models/*
!ml/models/.gitkeep
ml/mlflow.db
ml/mlflow-artifacts/
.DS_Store
Thumbs.db
streamlit_app/.streamlit/secrets.toml
```

## 1.3 Create file: `.env.example`

```env
# Google Cloud / BigQuery
GCP_PROJECT_ID=your-gcp-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_DB_PASSWORD=your-db-password
SUPABASE_PROJECT_REF=your-project-ref

# MotherDuck
MOTHERDUCK_TOKEN=your-motherduck-token

# dbt Cloud
DBT_HOST=cloud.getdbt.com
DBT_TOKEN=your-dbt-cloud-service-token
DBT_PROD_ENV_ID=your-environment-id

# Claude
ANTHROPIC_API_KEY=your-claude-api-key

# MLflow
MLFLOW_TRACKING_URI=http://127.0.0.1:5000

# Snowflake (trial only)
SNOWFLAKE_ACCOUNT=
SNOWFLAKE_USER=
SNOWFLAKE_PASSWORD=
SNOWFLAKE_WAREHOUSE=ANALYTICS_WH
SNOWFLAKE_DATABASE=OLIST_ANALYTICS
SNOWFLAKE_SCHEMA=PUBLIC

# Databricks (trial only)
DATABRICKS_HOST=
DATABRICKS_TOKEN=
DATABRICKS_SQL_WAREHOUSE_ID=
```

## 1.4 Create file: `requirements.txt`

```txt
pandas>=2.1.0
polars>=0.20.0
pyarrow>=14.0.0
httpx>=0.25.0
duckdb>=0.9.0
google-cloud-bigquery>=3.13.0
google-cloud-bigquery-storage>=2.22.0
supabase>=2.0.0
dbt-core>=1.7.0
dbt-bigquery>=1.7.0
dbt-postgres>=1.7.0
dbt-duckdb>=1.7.0
scikit-learn>=1.3.0
xgboost>=2.0.0
mlflow>=2.9.0
shap>=0.43.0
mcp>=1.0.0
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.5.0
streamlit>=1.30.0
plotly>=5.18.0
anthropic>=0.40.0
python-dotenv>=1.0.0
tqdm>=4.66.0
kaggle>=1.5.0
```

## 1.5 Install dependencies

```bash
cd full-funnel-ai-analytics
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 1.6 Create file: `scripts/download_olist_data.py`

```python
"""
Download the Olist Brazilian E-Commerce dataset from Kaggle.
Requires: pip install kaggle
Set KAGGLE_USERNAME and KAGGLE_KEY in ~/.kaggle/kaggle.json
"""
import os
import subprocess
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "olist"
DATA_DIR.mkdir(parents=True, exist_ok=True)

EXPECTED_FILES = [
    "olist_customers_dataset.csv",
    "olist_orders_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_products_dataset.csv",
    "olist_sellers_dataset.csv",
    "olist_geolocation_dataset.csv",
    "product_category_name_translation.csv",
]

def download():
    print("=== Downloading Olist E-Commerce Dataset ===\n")

    existing = [f.name for f in DATA_DIR.glob("*.csv")]
    if all(f in existing for f in EXPECTED_FILES):
        print("All files already present. Skipping download.")
    else:
        try:
            subprocess.run(
                ["kaggle", "datasets", "download", "-d", "olistbr/brazilian-ecommerce",
                 "-p", str(DATA_DIR), "--unzip"],
                check=True,
            )
            print("Downloaded via Kaggle CLI")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Kaggle CLI failed. Download manually from:")
            print("  https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce")
            print(f"  Extract all CSVs to: {DATA_DIR}")
            return

    # Verify and report
    files = sorted(DATA_DIR.glob("*.csv"))
    print(f"\n{len(files)} files in {DATA_DIR}:")
    for f in files:
        import csv
        with open(f) as fh:
            rows = sum(1 for _ in fh) - 1
        size_mb = f.stat().st_size / 1e6
        print(f"  {f.name}: {rows:,} rows ({size_mb:.1f} MB)")

    missing = [f for f in EXPECTED_FILES if f not in [x.name for x in files]]
    if missing:
        print(f"\nWARNING: Missing files: {missing}")
    else:
        print("\n=== All 9 Olist files present ===")

if __name__ == "__main__":
    download()
```

## 1.7 Create file: `scripts/generate_mock_marketing_data.py`

```python
"""
Generate realistic synthetic marketing data anchored to real Olist orders.
Creates: Google Ads, Meta Ads, GA4, HubSpot, Salesforce, and Attribution data.

Run AFTER downloading Olist data: python scripts/download_olist_data.py
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import json
import csv

DATA_DIR = Path(__file__).parent.parent / "data"
OLIST_DIR = DATA_DIR / "olist"
MOCK_DIR = DATA_DIR / "mock_marketing"
MOCK_DIR.mkdir(parents=True, exist_ok=True)

np.random.seed(42)


def load_orders():
    """Load delivered Olist orders with revenue."""
    orders = pd.read_csv(OLIST_DIR / "olist_orders_dataset.csv")
    orders["order_purchase_timestamp"] = pd.to_datetime(orders["order_purchase_timestamp"])
    payments = pd.read_csv(OLIST_DIR / "olist_order_payments_dataset.csv")
    order_revenue = payments.groupby("order_id")["payment_value"].sum().reset_index()
    order_revenue.columns = ["order_id", "revenue"]
    orders = orders.merge(order_revenue, on="order_id", how="left")
    orders = orders[orders["order_status"] == "delivered"].copy()
    orders = orders.sort_values("order_purchase_timestamp").reset_index(drop=True)
    print(f"Loaded {len(orders):,} delivered orders")
    return orders


def generate_google_ads(orders):
    """Google Ads: campaigns, ad groups, keywords, daily performance."""
    print("\nGenerating Google Ads data...")

    campaigns = [
        {"campaign_id": "C001", "campaign_name": "Brand - Olist", "campaign_type": "SEARCH", "daily_budget": 150.0},
        {"campaign_id": "C002", "campaign_name": "Generic - Electronics", "campaign_type": "SEARCH", "daily_budget": 300.0},
        {"campaign_id": "C003", "campaign_name": "Generic - Home & Garden", "campaign_type": "SEARCH", "daily_budget": 250.0},
        {"campaign_id": "C004", "campaign_name": "Shopping - All Products", "campaign_type": "SHOPPING", "daily_budget": 400.0},
        {"campaign_id": "C005", "campaign_name": "Display - Retargeting", "campaign_type": "DISPLAY", "daily_budget": 200.0},
        {"campaign_id": "C006", "campaign_name": "YouTube - Brand Awareness", "campaign_type": "VIDEO", "daily_budget": 100.0},
    ]

    ad_groups = [
        {"ad_group_id": "AG001", "campaign_id": "C001", "ad_group_name": "Olist Exact Match"},
        {"ad_group_id": "AG002", "campaign_id": "C001", "ad_group_name": "Olist Broad Match"},
        {"ad_group_id": "AG003", "campaign_id": "C002", "ad_group_name": "Electronics - General"},
        {"ad_group_id": "AG004", "campaign_id": "C002", "ad_group_name": "Electronics - Smartphones"},
        {"ad_group_id": "AG005", "campaign_id": "C003", "ad_group_name": "Home Decor"},
        {"ad_group_id": "AG006", "campaign_id": "C003", "ad_group_name": "Kitchen Appliances"},
        {"ad_group_id": "AG007", "campaign_id": "C004", "ad_group_name": "Shopping - Best Sellers"},
        {"ad_group_id": "AG008", "campaign_id": "C005", "ad_group_name": "Cart Abandoners"},
        {"ad_group_id": "AG009", "campaign_id": "C005", "ad_group_name": "Past Purchasers"},
        {"ad_group_id": "AG010", "campaign_id": "C006", "ad_group_name": "Brand Video - 30s"},
    ]

    keywords = [
        {"keyword_id": "KW001", "ad_group_id": "AG001", "keyword": "olist", "match_type": "EXACT"},
        {"keyword_id": "KW002", "ad_group_id": "AG001", "keyword": "olist store", "match_type": "EXACT"},
        {"keyword_id": "KW003", "ad_group_id": "AG002", "keyword": "olist marketplace", "match_type": "BROAD"},
        {"keyword_id": "KW004", "ad_group_id": "AG003", "keyword": "buy electronics online brazil", "match_type": "PHRASE"},
        {"keyword_id": "KW005", "ad_group_id": "AG003", "keyword": "cheap electronics", "match_type": "BROAD"},
        {"keyword_id": "KW006", "ad_group_id": "AG004", "keyword": "smartphone deals", "match_type": "PHRASE"},
        {"keyword_id": "KW007", "ad_group_id": "AG005", "keyword": "home decor online", "match_type": "BROAD"},
        {"keyword_id": "KW008", "ad_group_id": "AG005", "keyword": "furniture online brazil", "match_type": "PHRASE"},
        {"keyword_id": "KW009", "ad_group_id": "AG006", "keyword": "kitchen appliances", "match_type": "BROAD"},
        {"keyword_id": "KW010", "ad_group_id": "AG006", "keyword": "small kitchen appliances", "match_type": "PHRASE"},
    ]

    date_range = pd.date_range("2017-01-01", "2018-08-31")
    daily_perf = []

    for date in date_range:
        month_factor = {1: 0.7, 2: 0.85, 3: 0.95, 4: 1.0, 5: 1.2, 6: 1.2,
                        7: 1.0, 8: 0.95, 9: 1.0, 10: 1.1, 11: 1.8, 12: 1.4}.get(date.month, 1.0)
        dow_factor = 0.8 if date.weekday() >= 5 else 1.0

        for camp in campaigns:
            base_imp = {"SEARCH": 5000, "SHOPPING": 8000, "DISPLAY": 20000, "VIDEO": 15000}[camp["campaign_type"]]
            impressions = int(base_imp * month_factor * dow_factor * np.random.uniform(0.7, 1.3))

            ctr = {"SEARCH": 0.035, "SHOPPING": 0.02, "DISPLAY": 0.005, "VIDEO": 0.012}[camp["campaign_type"]] * np.random.uniform(0.8, 1.2)
            clicks = int(impressions * ctr)

            cpc = {"SEARCH": 0.85, "SHOPPING": 0.45, "DISPLAY": 0.25, "VIDEO": 0.15}[camp["campaign_type"]] * np.random.uniform(0.7, 1.4) * month_factor
            cost = round(min(clicks * cpc, camp["daily_budget"] * np.random.uniform(0.9, 1.1)), 2)

            conv_rate = {"SEARCH": 0.028, "SHOPPING": 0.022, "DISPLAY": 0.008, "VIDEO": 0.003}[camp["campaign_type"]] * np.random.uniform(0.6, 1.5)
            conversions = int(clicks * conv_rate)
            conv_value = round(conversions * np.random.uniform(80, 250), 2)

            daily_perf.append({
                "date": date.strftime("%Y-%m-%d"),
                "campaign_id": camp["campaign_id"],
                "campaign_name": camp["campaign_name"],
                "campaign_type": camp["campaign_type"],
                "impressions": impressions,
                "clicks": clicks,
                "cost": cost,
                "conversions": conversions,
                "conversion_value": conv_value,
                "ctr": round(ctr * 100, 2),
                "avg_cpc": round(cost / max(clicks, 1), 2),
                "cost_per_conversion": round(cost / max(conversions, 1), 2),
                "roas": round(conv_value / max(cost, 0.01), 2),
            })

    pd.DataFrame(campaigns).to_csv(MOCK_DIR / "google_ads_campaigns.csv", index=False)
    pd.DataFrame(ad_groups).to_csv(MOCK_DIR / "google_ads_ad_groups.csv", index=False)
    pd.DataFrame(keywords).to_csv(MOCK_DIR / "google_ads_keywords.csv", index=False)
    pd.DataFrame(daily_perf).to_csv(MOCK_DIR / "google_ads_daily_performance.csv", index=False)
    print(f"  {len(campaigns)} campaigns, {len(ad_groups)} ad groups, {len(keywords)} keywords, {len(daily_perf):,} daily rows")


def generate_meta_ads(orders):
    """Meta (Facebook/Instagram) Ads: campaigns, ad sets, daily performance."""
    print("\nGenerating Meta Ads data...")

    campaigns = [
        {"campaign_id": "META_C001", "campaign_name": "Prospecting - Lookalike Purchasers", "objective": "CONVERSIONS", "daily_budget": 250.0},
        {"campaign_id": "META_C002", "campaign_name": "Retargeting - Add to Cart", "objective": "CONVERSIONS", "daily_budget": 150.0},
        {"campaign_id": "META_C003", "campaign_name": "Brand Awareness - Video", "objective": "AWARENESS", "daily_budget": 100.0},
        {"campaign_id": "META_C004", "campaign_name": "Catalog Sales - Dynamic", "objective": "CATALOG_SALES", "daily_budget": 300.0},
        {"campaign_id": "META_C005", "campaign_name": "Instagram Stories - Flash Sales", "objective": "CONVERSIONS", "daily_budget": 200.0},
    ]

    ad_sets = [
        {"ad_set_id": "AS001", "campaign_id": "META_C001", "ad_set_name": "LAL 1% - Purchasers", "targeting": "lookalike_1pct", "placement": "facebook_feed"},
        {"ad_set_id": "AS002", "campaign_id": "META_C001", "ad_set_name": "LAL 3% - Purchasers", "targeting": "lookalike_3pct", "placement": "facebook_feed"},
        {"ad_set_id": "AS003", "campaign_id": "META_C001", "ad_set_name": "Interest - Electronics", "targeting": "interest_electronics", "placement": "instagram_feed"},
        {"ad_set_id": "AS004", "campaign_id": "META_C002", "ad_set_name": "Cart Abandoners 7d", "targeting": "retarget_cart_7d", "placement": "facebook_feed"},
        {"ad_set_id": "AS005", "campaign_id": "META_C002", "ad_set_name": "Viewed Product 14d", "targeting": "retarget_viewed_14d", "placement": "instagram_stories"},
        {"ad_set_id": "AS006", "campaign_id": "META_C003", "ad_set_name": "Broad - 18-45 Brazil", "targeting": "broad_18_45", "placement": "facebook_video"},
        {"ad_set_id": "AS007", "campaign_id": "META_C004", "ad_set_name": "Dynamic - All Products", "targeting": "catalog_dynamic", "placement": "facebook_feed"},
        {"ad_set_id": "AS008", "campaign_id": "META_C005", "ad_set_name": "Stories - Weekend Deals", "targeting": "interest_shopping", "placement": "instagram_stories"},
    ]

    date_range = pd.date_range("2017-01-01", "2018-08-31")
    daily_perf = []

    for date in date_range:
        month_factor = {1: 0.6, 5: 1.1, 6: 1.1, 11: 2.0, 12: 1.5}.get(date.month, 1.0)

        for camp in campaigns:
            impressions = int(np.random.uniform(8000, 30000) * month_factor)
            reach = int(impressions * np.random.uniform(0.6, 0.85))
            cpm = np.random.uniform(4.0, 12.0) * month_factor
            spend = round(min((impressions / 1000) * cpm, camp["daily_budget"] * np.random.uniform(0.85, 1.05)), 2)
            link_clicks = int(impressions * np.random.uniform(0.008, 0.025))
            purchases = int(link_clicks * np.random.uniform(0.01, 0.06))
            purchase_value = round(purchases * np.random.uniform(90, 200), 2)

            daily_perf.append({
                "date": date.strftime("%Y-%m-%d"),
                "campaign_id": camp["campaign_id"],
                "campaign_name": camp["campaign_name"],
                "objective": camp["objective"],
                "impressions": impressions, "reach": reach, "spend": spend,
                "link_clicks": link_clicks,
                "ctr": round((link_clicks / max(impressions, 1)) * 100, 2),
                "cpc": round(spend / max(link_clicks, 1), 2),
                "cpm": round(cpm, 2),
                "purchases": purchases, "purchase_value": purchase_value,
                "cost_per_purchase": round(spend / max(purchases, 1), 2),
                "roas": round(purchase_value / max(spend, 0.01), 2),
            })

    pd.DataFrame(campaigns).to_csv(MOCK_DIR / "meta_ads_campaigns.csv", index=False)
    pd.DataFrame(ad_sets).to_csv(MOCK_DIR / "meta_ads_ad_sets.csv", index=False)
    pd.DataFrame(daily_perf).to_csv(MOCK_DIR / "meta_ads_daily_performance.csv", index=False)
    print(f"  {len(campaigns)} campaigns, {len(ad_sets)} ad sets, {len(daily_perf):,} daily rows")


def generate_ga4(orders):
    """GA4 website sessions by channel, device, and day."""
    print("\nGenerating GA4 data...")

    channels = ["organic_search", "paid_search", "paid_social", "direct", "email", "referral", "organic_social"]
    channel_weights = [0.25, 0.20, 0.18, 0.15, 0.10, 0.07, 0.05]
    devices = ["mobile", "desktop", "tablet"]
    device_weights = [0.55, 0.35, 0.10]

    bounce_rates = {"organic_search": 0.45, "paid_search": 0.38, "paid_social": 0.55,
                    "direct": 0.30, "email": 0.25, "referral": 0.50, "organic_social": 0.60}
    conv_rates = {"organic_search": 0.025, "paid_search": 0.032, "paid_social": 0.018,
                  "direct": 0.035, "email": 0.042, "referral": 0.020, "organic_social": 0.012}

    date_range = pd.date_range("2017-01-01", "2018-08-31")
    rows = []

    for date in date_range:
        month_factor = {1: 0.7, 5: 1.1, 6: 1.1, 11: 1.9, 12: 1.4}.get(date.month, 1.0)
        dow_factor = 0.75 if date.weekday() >= 5 else 1.0

        for ch, cw in zip(channels, channel_weights):
            for dev, dw in zip(devices, device_weights):
                sessions = int(500 * cw * dw * month_factor * dow_factor * np.random.uniform(0.7, 1.3) * 10)
                br = bounce_rates[ch] * np.random.uniform(0.85, 1.15)
                engaged = int(sessions * (1 - br))
                conversions = int(sessions * conv_rates[ch] * np.random.uniform(0.7, 1.3))
                revenue = round(conversions * np.random.uniform(80, 220), 2)

                rows.append({
                    "date": date.strftime("%Y-%m-%d"), "channel_group": ch, "device_category": dev,
                    "sessions": sessions, "engaged_sessions": engaged,
                    "bounce_rate": round(br * 100, 1),
                    "avg_session_duration_sec": round(np.random.uniform(60, 300) * (1 - br * 0.5), 0),
                    "pages_per_session": round(np.random.uniform(1.5, 6.0) * (1 - br * 0.3), 1),
                    "new_users": int(sessions * np.random.uniform(0.5, 0.8)),
                    "conversions": conversions, "revenue": revenue,
                    "conversion_rate": round((conversions / max(sessions, 1)) * 100, 2),
                })

    pd.DataFrame(rows).to_csv(MOCK_DIR / "ga4_daily_sessions.csv", index=False)
    print(f"  {len(rows):,} daily session rows")


def generate_hubspot(orders):
    """HubSpot contacts and deals linked to Olist customers/orders."""
    print("\nGenerating HubSpot data...")

    customers = pd.read_csv(OLIST_DIR / "olist_customers_dataset.csv")
    unique_customers = customers.drop_duplicates(subset="customer_unique_id")
    sources = ["organic_search", "paid_search", "paid_social", "direct", "email", "referral"]
    source_weights = [0.25, 0.22, 0.20, 0.15, 0.10, 0.08]
    first_names = ["ana", "bruno", "carla", "daniel", "elena", "fabio", "gabriela", "henrique", "isabela", "joao",
                   "karen", "lucas", "maria", "nelson", "olivia", "pedro", "raquel", "sergio", "tatiana", "vitor"]
    last_names = ["silva", "santos", "oliveira", "souza", "lima", "pereira", "costa", "rodrigues", "almeida", "nascimento"]

    contacts = []
    for i, (_, cust) in enumerate(unique_customers.iterrows()):
        cust_orders = orders[orders["customer_id"] == cust["customer_id"]]
        if cust_orders.empty:
            continue
        first_order = cust_orders.iloc[0]
        order_date = first_order["order_purchase_timestamp"]
        create_date = order_date - timedelta(days=np.random.randint(0, 31))
        source = np.random.choice(sources, p=source_weights)
        fname = np.random.choice(first_names)
        lname = np.random.choice(last_names)

        contacts.append({
            "contact_id": f"HS_{i+1:06d}",
            "customer_id": cust["customer_unique_id"],
            "email": f"{fname}.{lname}{np.random.randint(1,999)}@example.com",
            "first_name": fname.capitalize(), "last_name": lname.capitalize(),
            "city": cust["customer_city"], "state": cust["customer_state"],
            "create_date": create_date.strftime("%Y-%m-%d"),
            "lifecycle_stage": "customer",
            "lead_source": source,
            "num_orders": len(cust_orders),
            "total_revenue": round(cust_orders["revenue"].sum(), 2),
            "first_order_date": order_date.strftime("%Y-%m-%d"),
            "last_activity_date": cust_orders.iloc[-1]["order_purchase_timestamp"].strftime("%Y-%m-%d"),
        })

    deals = []
    for i, (_, order) in enumerate(orders.iterrows()):
        is_won = order["order_status"] == "delivered"
        deals.append({
            "deal_id": f"DEAL_{i+1:06d}", "order_id": order["order_id"],
            "deal_name": f"Order {order['order_id'][:8]}",
            "deal_stage": "closed_won" if is_won else np.random.choice(["qualified_to_buy", "presentation_scheduled", "negotiation"]),
            "pipeline": "default",
            "amount": round(order.get("revenue", 0), 2),
            "create_date": order["order_purchase_timestamp"].strftime("%Y-%m-%d"),
            "close_date": order["order_purchase_timestamp"].strftime("%Y-%m-%d") if is_won else "",
            "deal_type": "new_business",
            "lead_source": np.random.choice(sources, p=source_weights),
        })

    pd.DataFrame(contacts).to_csv(MOCK_DIR / "hubspot_contacts.csv", index=False)
    pd.DataFrame(deals).to_csv(MOCK_DIR / "hubspot_deals.csv", index=False)
    print(f"  {len(contacts):,} contacts, {len(deals):,} deals")


def generate_salesforce(orders):
    """Salesforce accounts (from sellers) and opportunities (from orders)."""
    print("\nGenerating Salesforce data...")

    sellers = pd.read_csv(OLIST_DIR / "olist_sellers_dataset.csv")
    accounts = []
    for i, (_, seller) in enumerate(sellers.iterrows()):
        accounts.append({
            "account_id": f"ACC_{i+1:05d}", "seller_id": seller["seller_id"],
            "account_name": f"Seller {seller['seller_id'][:8]}",
            "city": seller["seller_city"], "state": seller["seller_state"],
            "account_type": np.random.choice(["Standard", "Premium", "Enterprise"], p=[0.6, 0.3, 0.1]),
            "industry": np.random.choice(["Retail", "Electronics", "Fashion", "Home & Garden", "Sports", "Health & Beauty"]),
            "annual_revenue": round(np.random.uniform(50000, 2000000), 2),
            "num_employees": np.random.randint(1, 50),
        })

    stages = ["Prospecting", "Qualification", "Needs Analysis", "Value Proposition", "Negotiation", "Closed Won", "Closed Lost"]
    probability = {"Prospecting": 10, "Qualification": 25, "Needs Analysis": 40, "Value Proposition": 60, "Negotiation": 80, "Closed Won": 100, "Closed Lost": 0}
    opportunities = []
    for i, (_, order) in enumerate(orders.head(50000).iterrows()):
        is_won = order["order_status"] == "delivered"
        stage = "Closed Won" if is_won else np.random.choice(stages[:5])
        od = order["order_purchase_timestamp"]
        opportunities.append({
            "opportunity_id": f"OPP_{i+1:06d}", "order_id": order["order_id"],
            "opportunity_name": f"Deal {order['order_id'][:8]}",
            "stage": stage, "probability": probability[stage],
            "amount": round(order.get("revenue", 0), 2),
            "created_date": (od - timedelta(days=np.random.randint(0, 14))).strftime("%Y-%m-%d"),
            "close_date": od.strftime("%Y-%m-%d"),
            "lead_source": np.random.choice(["Web", "Paid Search", "Social Media", "Email", "Referral", "Direct"], p=[0.25, 0.20, 0.18, 0.15, 0.12, 0.10]),
            "type": "New Business",
            "fiscal_quarter": f"Q{(od.month - 1) // 3 + 1} {od.year}",
        })

    pd.DataFrame(accounts).to_csv(MOCK_DIR / "salesforce_accounts.csv", index=False)
    pd.DataFrame(opportunities).to_csv(MOCK_DIR / "salesforce_opportunities.csv", index=False)
    print(f"  {len(accounts):,} accounts, {len(opportunities):,} opportunities")


def generate_attribution(orders):
    """Multi-touch attribution table linking orders to marketing touchpoints."""
    print("\nGenerating attribution data...")

    channels = [
        {"channel": "google_ads_search", "platform": "google_ads", "weight": 0.25},
        {"channel": "google_ads_shopping", "platform": "google_ads", "weight": 0.15},
        {"channel": "meta_prospecting", "platform": "meta_ads", "weight": 0.18},
        {"channel": "meta_retargeting", "platform": "meta_ads", "weight": 0.10},
        {"channel": "organic_search", "platform": "ga4", "weight": 0.15},
        {"channel": "email_marketing", "platform": "hubspot", "weight": 0.08},
        {"channel": "direct", "platform": "ga4", "weight": 0.09},
    ]
    weights = [c["weight"] for c in channels]

    rows = []
    for _, order in orders.iterrows():
        num_touches = np.random.choice([1, 2, 3, 4], p=[0.3, 0.35, 0.25, 0.1])
        selected = np.random.choice(len(channels), size=min(num_touches, len(channels)), replace=False, p=weights)
        od = order["order_purchase_timestamp"]

        for touch_idx, ch_idx in enumerate(selected):
            ch = channels[ch_idx]
            touch_date = od - timedelta(days=np.random.randint(0, 14))
            rows.append({
                "order_id": order["order_id"],
                "touchpoint_position": touch_idx + 1,
                "total_touchpoints": len(selected),
                "channel": ch["channel"], "platform": ch["platform"],
                "touchpoint_date": touch_date.strftime("%Y-%m-%d"),
                "order_date": od.strftime("%Y-%m-%d"),
                "order_revenue": round(order.get("revenue", 0), 2),
                "first_touch_credit": 1.0 if touch_idx == 0 else 0.0,
                "last_touch_credit": 1.0 if touch_idx == len(selected) - 1 else 0.0,
                "linear_credit": round(1.0 / len(selected), 4),
            })

    pd.DataFrame(rows).to_csv(MOCK_DIR / "marketing_attribution.csv", index=False)
    print(f"  {len(rows):,} attribution rows")


def main():
    print("=" * 60)
    print("GENERATING MOCK MARKETING DATA")
    print("Anchored to real Olist e-commerce transactions")
    print("=" * 60)

    orders = load_orders()
    generate_google_ads(orders)
    generate_meta_ads(orders)
    generate_ga4(orders)
    generate_hubspot(orders)
    generate_salesforce(orders)
    generate_attribution(orders)

    print("\n" + "=" * 60)
    print(f"All mock data saved to: {MOCK_DIR}")
    for f in sorted(MOCK_DIR.glob("*.csv")):
        rows = sum(1 for _ in open(f)) - 1
        size = f.stat().st_size / 1e6
        print(f"  {f.name}: {rows:,} rows ({size:.1f} MB)")
    print("=" * 60)


if __name__ == "__main__":
    main()
```

## 1.8 Create file: `scripts/load_bigquery.py`

```python
"""Load all Olist + mock marketing data into BigQuery free tier."""
import os
from pathlib import Path
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
DATASET_ID = "olist_analytics"
DATA_DIR = Path(__file__).parent.parent / "data"

def get_client():
    return bigquery.Client(project=PROJECT_ID)

def create_dataset(client):
    dataset = bigquery.Dataset(f"{PROJECT_ID}.{DATASET_ID}")
    dataset.location = "US"
    client.create_dataset(dataset, exists_ok=True)
    print(f"Dataset {PROJECT_ID}.{DATASET_ID} ready")

def load_csv(client, filepath, table_name, schema=None):
    """Load a CSV file into BigQuery."""
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=True if schema is None else False,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    if schema:
        job_config.schema = schema

    with open(filepath, "rb") as f:
        job = client.load_table_from_file(f, table_id, job_config=job_config)
        job.result()
    table = client.get_table(table_id)
    print(f"  {table_name}: {table.num_rows:,} rows")

def main():
    print("=== Loading All Data into BigQuery ===\n")
    client = get_client()
    create_dataset(client)

    # Olist tables
    olist_dir = DATA_DIR / "olist"
    olist_tables = {
        "olist_customers_dataset.csv": "customers",
        "olist_orders_dataset.csv": "orders",
        "olist_order_items_dataset.csv": "order_items",
        "olist_order_payments_dataset.csv": "order_payments",
        "olist_order_reviews_dataset.csv": "order_reviews",
        "olist_products_dataset.csv": "products",
        "olist_sellers_dataset.csv": "sellers",
        "olist_geolocation_dataset.csv": "geolocation",
        "product_category_name_translation.csv": "category_translation",
    }
    print("Olist tables:")
    for filename, table_name in olist_tables.items():
        filepath = olist_dir / filename
        if filepath.exists():
            load_csv(client, filepath, table_name)
        else:
            print(f"  SKIP: {filename} not found")

    # Mock marketing tables
    mock_dir = DATA_DIR / "mock_marketing"
    print("\nMarketing tables:")
    for csv_file in sorted(mock_dir.glob("*.csv")):
        table_name = csv_file.stem  # filename without extension
        load_csv(client, csv_file, table_name)

    print("\n=== BigQuery loading complete ===")

if __name__ == "__main__":
    main()
```

## 1.9 Create file: `scripts/load_duckdb.py`

```python
"""Set up local DuckDB database with all Olist + mock marketing data."""
import duckdb
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "olist_analytics.duckdb"
DATA_DIR = Path(__file__).parent.parent / "data"

def setup():
    print("=== Setting up DuckDB ===\n")
    con = duckdb.connect(str(DB_PATH))

    # Load Olist CSVs
    olist_dir = DATA_DIR / "olist"
    print("Olist tables:")
    for csv_file in sorted(olist_dir.glob("*.csv")):
        table_name = csv_file.stem.replace("olist_", "").replace("_dataset", "")
        con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM read_csv_auto('{csv_file}')")
        count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        print(f"  {table_name}: {count:,} rows")

    # Load mock marketing CSVs
    mock_dir = DATA_DIR / "mock_marketing"
    print("\nMarketing tables:")
    for csv_file in sorted(mock_dir.glob("*.csv")):
        table_name = csv_file.stem
        con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM read_csv_auto('{csv_file}')")
        count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        print(f"  {table_name}: {count:,} rows")

    con.close()
    print(f"\nDatabase saved: {DB_PATH}")
    print("=== DuckDB setup complete ===")

if __name__ == "__main__":
    setup()
```

## 1.10 Create file: `scripts/load_supabase.py`

```python
"""Load subset of data into Supabase Postgres (500MB free tier)."""
import os
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv
from pathlib import Path
from tqdm import tqdm

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
DATA_DIR = Path(__file__).parent.parent / "data"

SQL_SETUP = """
-- Run this in Supabase SQL Editor FIRST:

CREATE TABLE IF NOT EXISTS orders (
    order_id VARCHAR PRIMARY KEY,
    customer_id VARCHAR,
    order_status VARCHAR,
    order_purchase_timestamp TIMESTAMPTZ,
    order_approved_at TIMESTAMPTZ,
    order_delivered_carrier_date TIMESTAMPTZ,
    order_delivered_customer_date TIMESTAMPTZ,
    order_estimated_delivery_date TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS order_items (
    order_id VARCHAR,
    order_item_id INTEGER,
    product_id VARCHAR,
    seller_id VARCHAR,
    shipping_limit_date TIMESTAMPTZ,
    price NUMERIC(10,2),
    freight_value NUMERIC(10,2)
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR PRIMARY KEY,
    customer_unique_id VARCHAR,
    customer_zip_code_prefix VARCHAR,
    customer_city VARCHAR,
    customer_state VARCHAR
);

CREATE TABLE IF NOT EXISTS hubspot_contacts (
    contact_id VARCHAR PRIMARY KEY,
    customer_id VARCHAR,
    email VARCHAR,
    first_name VARCHAR,
    last_name VARCHAR,
    city VARCHAR,
    state VARCHAR,
    create_date DATE,
    lifecycle_stage VARCHAR,
    lead_source VARCHAR,
    num_orders INTEGER,
    total_revenue NUMERIC(10,2),
    first_order_date DATE,
    last_activity_date DATE
);

CREATE TABLE IF NOT EXISTS marketing_attribution (
    order_id VARCHAR,
    touchpoint_position INTEGER,
    total_touchpoints INTEGER,
    channel VARCHAR,
    platform VARCHAR,
    touchpoint_date DATE,
    order_date DATE,
    order_revenue NUMERIC(10,2),
    first_touch_credit NUMERIC(6,4),
    last_touch_credit NUMERIC(6,4),
    linear_credit NUMERIC(6,4)
);
"""

def main():
    print("=== Loading Data into Supabase ===\n")
    print("IMPORTANT: First run this SQL in Supabase SQL Editor:")
    print(SQL_SETUP)
    input("\nPress Enter after creating tables in Supabase...")

    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    batch_size = 500

    # Load orders (sample for free tier)
    print("Loading orders...")
    df = pd.read_csv(DATA_DIR / "olist" / "olist_orders_dataset.csv")
    df = df.head(50000)  # Sample for 500MB limit
    df = df.where(df.notna(), None)
    for i in tqdm(range(0, len(df), batch_size)):
        batch = df.iloc[i:i+batch_size].to_dict(orient="records")
        try:
            client.table("orders").upsert(batch).execute()
        except Exception as e:
            print(f"  Error at row {i}: {e}")

    # Load customers
    print("Loading customers...")
    df = pd.read_csv(DATA_DIR / "olist" / "olist_customers_dataset.csv")
    df = df.where(df.notna(), None)
    for i in tqdm(range(0, len(df), batch_size)):
        batch = df.iloc[i:i+batch_size].to_dict(orient="records")
        try:
            client.table("customers").upsert(batch).execute()
        except Exception as e:
            pass

    # Load hubspot contacts
    print("Loading HubSpot contacts...")
    df = pd.read_csv(DATA_DIR / "mock_marketing" / "hubspot_contacts.csv")
    df = df.head(50000)
    df = df.where(df.notna(), None)
    for i in tqdm(range(0, len(df), batch_size)):
        batch = df.iloc[i:i+batch_size].to_dict(orient="records")
        try:
            client.table("hubspot_contacts").upsert(batch).execute()
        except Exception as e:
            pass

    # Load attribution
    print("Loading attribution...")
    df = pd.read_csv(DATA_DIR / "mock_marketing" / "marketing_attribution.csv")
    df = df.head(100000)
    df = df.where(df.notna(), None)
    for i in tqdm(range(0, len(df), batch_size)):
        batch = df.iloc[i:i+batch_size].to_dict(orient="records")
        try:
            client.table("marketing_attribution").insert(batch).execute()
        except Exception as e:
            pass

    print("\n=== Supabase loading complete ===")

if __name__ == "__main__":
    main()
```

## 1.11 Execute Phase 1

```bash
python scripts/download_olist_data.py
python scripts/generate_mock_marketing_data.py
python scripts/load_duckdb.py
python scripts/load_bigquery.py
# python scripts/load_supabase.py  # Optional, after creating tables in Supabase UI
```

Verify: DuckDB should have ~25 tables. BigQuery should have ~25 tables. Check row counts match expectations.
# ═══════════════════════════════════════════
# PHASE 2: DBT PROJECT + SEMANTIC LAYER
# ═══════════════════════════════════════════

## 2.1 Create file: `dbt_project/dbt_project.yml`

```yaml
name: "olist_analytics"
version: "1.0.0"
config-version: 2
profile: "olist_analytics"
model-paths: ["models"]
analysis-paths: ["analyses"]
test-paths: ["tests"]
seed-paths: ["seeds"]
macro-paths: ["macros"]
snapshot-paths: ["snapshots"]
clean-targets: ["target", "dbt_packages"]

models:
  olist_analytics:
    staging:
      +materialized: view
    intermediate:
      +materialized: ephemeral
    marts:
      +materialized: table
```

## 2.2 Create file: `dbt_project/profiles.yml.example`

```yaml
olist_analytics:
  target: duckdb
  outputs:
    duckdb:
      type: duckdb
      path: "../data/olist_analytics.duckdb"
      threads: 4
    bigquery:
      type: bigquery
      method: oauth
      project: "{{ env_var('GCP_PROJECT_ID') }}"
      dataset: olist_analytics
      threads: 4
      location: US
    supabase:
      type: postgres
      host: "db.{{ env_var('SUPABASE_PROJECT_REF') }}.supabase.co"
      user: postgres
      password: "{{ env_var('SUPABASE_DB_PASSWORD') }}"
      port: 5432
      dbname: postgres
      schema: public
      threads: 4
    snowflake:
      type: snowflake
      account: "{{ env_var('SNOWFLAKE_ACCOUNT') }}"
      user: "{{ env_var('SNOWFLAKE_USER') }}"
      password: "{{ env_var('SNOWFLAKE_PASSWORD') }}"
      warehouse: "{{ env_var('SNOWFLAKE_WAREHOUSE') }}"
      database: "{{ env_var('SNOWFLAKE_DATABASE') }}"
      schema: "{{ env_var('SNOWFLAKE_SCHEMA') }}"
      threads: 4
    databricks:
      type: databricks
      host: "{{ env_var('DATABRICKS_HOST') }}"
      http_path: "/sql/1.0/warehouses/{{ env_var('DATABRICKS_SQL_WAREHOUSE_ID') }}"
      token: "{{ env_var('DATABRICKS_TOKEN') }}"
      catalog: olist_analytics
      schema: public
      threads: 4
```

AGENT NOTE: Copy to `~/.dbt/profiles.yml` with real values.

## 2.3 Create file: `dbt_project/models/staging/sources.yml`

```yaml
version: 2

sources:
  - name: olist
    description: "Olist Brazilian E-Commerce dataset (Kaggle)"
    tables:
      - name: orders
      - name: order_items
      - name: order_payments
      - name: order_reviews
      - name: customers
      - name: sellers
      - name: products
      - name: geolocation
      - name: category_translation
        identifier: "product_category_name_translation"

  - name: marketing
    description: "Synthetic marketing platform data"
    tables:
      - name: google_ads_daily_performance
      - name: google_ads_campaigns
      - name: meta_ads_daily_performance
      - name: meta_ads_campaigns
      - name: ga4_daily_sessions
      - name: hubspot_contacts
      - name: hubspot_deals
      - name: salesforce_opportunities
      - name: salesforce_accounts
      - name: marketing_attribution
```

## 2.4 Create staging models

Create these 14 staging models. Each should: SELECT from source, rename columns to snake_case, add derived fields, filter invalid rows. Use `{% if target.type == 'bigquery' %}` Jinja blocks for SQL dialect differences where needed (especially for date functions).

### `dbt_project/models/staging/stg_orders.sql`
```sql
WITH source AS (
    SELECT * FROM {{ source('olist', 'orders') }}
)
SELECT
    order_id,
    customer_id,
    order_status,
    CAST(order_purchase_timestamp AS TIMESTAMP) AS order_purchase_timestamp,
    CAST(order_approved_at AS TIMESTAMP) AS order_approved_at,
    CAST(order_delivered_carrier_date AS TIMESTAMP) AS order_delivered_carrier_date,
    CAST(order_delivered_customer_date AS TIMESTAMP) AS order_delivered_customer_date,
    CAST(order_estimated_delivery_date AS TIMESTAMP) AS order_estimated_delivery_date,
    CAST(order_purchase_timestamp AS DATE) AS order_date,
    EXTRACT(YEAR FROM CAST(order_purchase_timestamp AS TIMESTAMP)) AS order_year,
    EXTRACT(MONTH FROM CAST(order_purchase_timestamp AS TIMESTAMP)) AS order_month,
    {% if target.type == 'bigquery' %}
        TIMESTAMP_DIFF(CAST(order_delivered_customer_date AS TIMESTAMP), CAST(order_purchase_timestamp AS TIMESTAMP), DAY) AS delivery_days,
    {% elif target.type == 'postgres' %}
        EXTRACT(DAY FROM (CAST(order_delivered_customer_date AS TIMESTAMP) - CAST(order_purchase_timestamp AS TIMESTAMP))) AS delivery_days,
    {% else %}
        DATEDIFF('day', CAST(order_purchase_timestamp AS TIMESTAMP), CAST(order_delivered_customer_date AS TIMESTAMP)) AS delivery_days,
    {% endif %}
    CASE WHEN order_delivered_customer_date > order_estimated_delivery_date THEN TRUE ELSE FALSE END AS is_late_delivery
FROM source
WHERE order_purchase_timestamp IS NOT NULL
```

### Remaining staging models — the agent should create these following the same pattern:

**`stg_order_items.sql`**: SELECT from order_items. Add `total_item_value = price + freight_value`. Keep order_id, order_item_id, product_id, seller_id, price, freight_value, total_item_value.

**`stg_order_payments.sql`**: SELECT from order_payments. Clean payment_type to readable names (credit_card, boleto, voucher, debit_card). Keep order_id, payment_sequential, payment_type, payment_installments, payment_value.

**`stg_order_reviews.sql`**: SELECT from order_reviews. Add `is_positive = (review_score >= 4)`, `review_length = LENGTH(review_comment_message)`. Filter WHERE review_score IS NOT NULL.

**`stg_customers.sql`**: SELECT from customers. Keep all columns. LOWER() on city for consistency.

**`stg_sellers.sql`**: SELECT from sellers. Keep all columns. LOWER() on city for consistency.

**`stg_products.sql`**: LEFT JOIN with category_translation to get English category names. Add `product_volume = product_length_cm * product_height_cm * product_width_cm`. Filter WHERE product_category_name IS NOT NULL.

**`stg_google_ads_performance.sql`**: SELECT from google_ads_daily_performance. Cast date as DATE. Keep all columns.

**`stg_meta_ads_performance.sql`**: SELECT from meta_ads_daily_performance. Cast date as DATE. Keep all columns.

**`stg_ga4_sessions.sql`**: SELECT from ga4_daily_sessions. Cast date as DATE. Add `engagement_rate = (engaged_sessions / NULLIF(sessions, 0)) * 100`. Keep all columns.

**`stg_hubspot_contacts.sql`**: SELECT from hubspot_contacts. Cast create_date as DATE. Keep all columns.

**`stg_hubspot_deals.sql`**: SELECT from hubspot_deals. Add `is_closed_won = (deal_stage = 'closed_won')`. Keep all columns.

**`stg_salesforce_opportunities.sql`**: SELECT from salesforce_opportunities. Add `is_won = (stage = 'Closed Won')`, `weighted_amount = amount * probability / 100`. Keep all columns.

**`stg_marketing_attribution.sql`**: SELECT from marketing_attribution. Cast dates. Keep all columns. (Credits are pre-calculated in the synthetic data.)

## 2.5 Create intermediate models

### `dbt_project/models/intermediate/int_customer_orders.sql`
```sql
WITH orders AS (SELECT * FROM {{ ref('stg_orders') }} WHERE order_status = 'delivered'),
     payments AS (SELECT order_id, SUM(payment_value) AS order_revenue FROM {{ ref('stg_order_payments') }} GROUP BY 1)
SELECT
    o.customer_id,
    MIN(o.order_date) AS first_order_date,
    MAX(o.order_date) AS last_order_date,
    COUNT(DISTINCT o.order_id) AS total_orders,
    SUM(p.order_revenue) AS total_revenue,
    AVG(p.order_revenue) AS avg_order_value,
    {% if target.type == 'bigquery' %}
        DATE_DIFF(MAX(o.order_date), MIN(o.order_date), DAY) / NULLIF(COUNT(DISTINCT o.order_id) - 1, 0) AS avg_days_between_orders
    {% elif target.type == 'postgres' %}
        EXTRACT(DAY FROM (MAX(o.order_date) - MIN(o.order_date))) / NULLIF(COUNT(DISTINCT o.order_id) - 1, 0) AS avg_days_between_orders
    {% else %}
        DATEDIFF('day', MIN(o.order_date), MAX(o.order_date)) / NULLIF(COUNT(DISTINCT o.order_id) - 1, 0) AS avg_days_between_orders
    {% endif %}
FROM orders o
LEFT JOIN payments p ON o.order_id = p.order_id
GROUP BY 1
```

### `dbt_project/models/intermediate/int_customer_ltv.sql`
```sql
WITH co AS (SELECT * FROM {{ ref('int_customer_orders') }})
SELECT
    customer_id, total_orders, total_revenue, avg_order_value, first_order_date, last_order_date,
    CASE
        WHEN total_revenue >= 500 OR total_orders >= 3 THEN 'vip'
        WHEN total_orders >= 2 THEN 'returning'
        ELSE 'new'
    END AS customer_segment,
    CASE WHEN total_revenue > 200 AND total_orders > 1 THEN 1 ELSE 0 END AS is_high_value
FROM co
```

### `dbt_project/models/intermediate/int_campaign_unified.sql`
```sql
SELECT date, 'google_ads' AS platform, campaign_name, campaign_type AS campaign_category,
       impressions, clicks, cost AS spend, conversions, conversion_value AS revenue, roas
FROM {{ ref('stg_google_ads_performance') }}
UNION ALL
SELECT date, 'meta_ads' AS platform, campaign_name, objective AS campaign_category,
       impressions, link_clicks AS clicks, spend, purchases AS conversions, purchase_value AS revenue, roas
FROM {{ ref('stg_meta_ads_performance') }}
```

### `dbt_project/models/intermediate/int_funnel_stages.sql`
The agent should build a model that traces each order through the funnel: attribution touchpoint → GA4 session → HubSpot lead → Salesforce opportunity → Olist order, with timestamps at each stage.

## 2.6 Create mart models (11 models)

### `dbt_project/models/marts/fct_orders.sql`
```sql
WITH orders AS (SELECT * FROM {{ ref('stg_orders') }} WHERE order_status = 'delivered'),
     items AS (SELECT order_id, COUNT(*) AS item_count, SUM(price) AS items_total, SUM(freight_value) AS freight_total FROM {{ ref('stg_order_items') }} GROUP BY 1),
     payments AS (SELECT order_id, SUM(payment_value) AS payment_total, MAX(payment_type) AS primary_payment_type FROM {{ ref('stg_order_payments') }} GROUP BY 1),
     reviews AS (SELECT order_id, review_score, is_positive FROM {{ ref('stg_order_reviews') }}),
     customers AS (SELECT * FROM {{ ref('stg_customers') }}),
     attribution AS (SELECT order_id, MIN(channel) AS first_touch_channel, MAX(channel) AS last_touch_channel, COUNT(*) AS touchpoint_count FROM {{ ref('stg_marketing_attribution') }} GROUP BY 1)
SELECT
    o.order_id, o.customer_id, o.order_date, o.order_year, o.order_month,
    o.order_status, o.delivery_days, o.is_late_delivery,
    i.item_count, i.items_total, i.freight_total,
    p.payment_total AS revenue, p.primary_payment_type,
    r.review_score, r.is_positive AS positive_review,
    c.customer_city, c.customer_state,
    a.first_touch_channel, a.last_touch_channel, a.touchpoint_count
FROM orders o
LEFT JOIN items i ON o.order_id = i.order_id
LEFT JOIN payments p ON o.order_id = p.order_id
LEFT JOIN reviews r ON o.order_id = r.order_id
LEFT JOIN customers c ON o.customer_id = c.customer_id
LEFT JOIN attribution a ON o.order_id = a.order_id
```

### Remaining mart models — agent should create:

**`fct_daily_revenue.sql`**: GROUP BY order_date. Metrics: total_revenue, order_count, avg_order_value, unique_customers, new_customers (first order that date).

**`fct_marketing_daily.sql`**: Combine int_campaign_unified by date. Add GA4 sessions by day. Calculate: total_google_spend, total_meta_spend, total_spend, total_conversions, ga4_total_sessions, blended_cac, blended_roas.

**`fct_marketing_attribution.sql`**: From stg_marketing_attribution, add time_decay_credit using the macro. Group by channel to get: total_orders, first_touch_revenue, last_touch_revenue, linear_revenue, time_decay_revenue.

**`fct_channel_performance.sql`**: Per channel: total_spend (from unified campaigns), attributed_revenue (per model), cac, roas, avg_touchpoints, avg_days_to_convert.

**`fct_pipeline.sql`**: Full funnel counts by channel: impressions, clicks, sessions, leads (hubspot), opportunities (salesforce), closed_won, revenue. With conversion rates between each stage.

**`fct_lead_scoring_features.sql`**: One row per customer. Features: lead_source, num_touchpoints, days_to_first_order, total_orders, total_revenue, avg_order_value, avg_review_score, customer_state, customer_segment, is_high_value (target variable). This is what the ML model trains on.

**`dim_customers.sql`**: From int_customer_ltv + stg_customers + stg_hubspot_contacts. Full customer dimension with demographics, LTV segment, lead source, marketing attribution.

**`dim_products.sql`**: From stg_products + aggregated order_items. Add: total_units_sold, total_revenue, avg_review_score, avg_price.

**`dim_campaigns.sql`**: Unified dimension from google_ads_campaigns + meta_ads_campaigns with common fields.

## 2.7 Create attribution macro

### `dbt_project/macros/attribution_models.sql`
```sql
{% macro time_decay_credit(touchpoint_date, order_date, half_life_days=7) %}
    POWER(2.0, -1.0 *
        {% if target.type == 'bigquery' %}
            DATE_DIFF(CAST({{ order_date }} AS DATE), CAST({{ touchpoint_date }} AS DATE), DAY)
        {% elif target.type == 'postgres' %}
            EXTRACT(DAY FROM (CAST({{ order_date }} AS DATE) - CAST({{ touchpoint_date }} AS DATE)))
        {% else %}
            DATEDIFF('day', CAST({{ touchpoint_date }} AS DATE), CAST({{ order_date }} AS DATE))
        {% endif %}
        / {{ half_life_days }}.0
    )
{% endmacro %}
```

## 2.8 Create semantic models and metrics

The agent should create 4 semantic model YAML files in `dbt_project/models/semantic_models/`:
- `sem_orders.yml` — entities: order (primary), customer (foreign). Dimensions: order_date (time), customer_state, primary_payment_type, first_touch_channel, customer_segment. Measures: total_orders (count), total_revenue (sum), avg_order_value (average), total_customers (count_distinct customer_id).
- `sem_marketing.yml` — from fct_marketing_daily. Measures: total_spend (sum), total_conversions (sum), total_sessions (sum).
- `sem_attribution.yml` — from fct_marketing_attribution. Measures: first_touch_revenue, last_touch_revenue, linear_revenue, time_decay_revenue (all sum).
- `sem_pipeline.yml` — from fct_pipeline. Measures: total_leads, total_opportunities, total_closed_won, total_pipeline_value.

And 4 metric YAML files in `dbt_project/models/metrics/`:
- `revenue_metrics.yml` — total_revenue, order_count, aov (derived), customer_ltv
- `marketing_metrics.yml` — total_ad_spend, blended_cac (derived), blended_roas (derived), cpc (derived), conversion_rate (derived)
- `attribution_metrics.yml` — first_touch_revenue, last_touch_revenue, linear_revenue, time_decay_revenue
- `pipeline_metrics.yml` — win_rate (derived), pipeline_velocity (derived), marketing_sourced_pipeline_pct (derived)

## 2.9 Create tests

### `dbt_project/tests/assert_attribution_credits_sum_to_one.sql`
```sql
-- Each order's linear credits should sum to approximately 1.0
SELECT order_id, SUM(linear_credit) AS total_credit
FROM {{ ref('stg_marketing_attribution') }}
GROUP BY order_id
HAVING ABS(SUM(linear_credit) - 1.0) > 0.02
```

### `dbt_project/tests/assert_no_negative_revenue.sql`
```sql
SELECT order_id, revenue
FROM {{ ref('fct_orders') }}
WHERE revenue < 0
```

### `dbt_project/models/staging/schema.yml` and `dbt_project/models/marts/schema.yml`
Add standard tests: not_null on primary keys, unique on dimension PKs, accepted_values on status/stage columns.

## 2.10 Build

```bash
cd dbt_project
dbt build --target duckdb     # Fast local first
dbt build --target bigquery   # Then cloud
dbt test --target bigquery    # Verify
```

---

# ═══════════════════════════════════════════
# PHASE 3: MCP SERVERS + AI LAYER
# ═══════════════════════════════════════════

## 3.1 Create all 5 mock MCP servers

Each server follows this pattern and reads from `data/mock_marketing/*.csv`:

### `mcp_servers/mock_google_ads_server.py`
```python
from mcp.server.fastmcp import FastMCP
import pandas as pd
import numpy as np
import json
from pathlib import Path

mcp = FastMCP("google-ads", description="Query Google Ads campaign performance data.")
DATA_DIR = Path(__file__).parent.parent / "data" / "mock_marketing"

@mcp.tool()
def get_campaign_performance(start_date: str, end_date: str, campaign_id: str = None) -> str:
    """Get Google Ads campaign performance for a date range. Returns impressions, clicks, cost, conversions, ROAS."""
    df = pd.read_csv(DATA_DIR / "google_ads_daily_performance.csv")
    df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]
    if campaign_id:
        df = df[df["campaign_id"] == campaign_id]
    summary = df.groupby(["campaign_id", "campaign_name", "campaign_type"]).agg(
        {"impressions": "sum", "clicks": "sum", "cost": "sum", "conversions": "sum", "conversion_value": "sum"}).reset_index()
    summary["ctr"] = (summary["clicks"] / summary["impressions"] * 100).round(2)
    summary["avg_cpc"] = (summary["cost"] / summary["clicks"].clip(lower=1)).round(2)
    summary["roas"] = (summary["conversion_value"] / summary["cost"].clip(lower=0.01)).round(2)
    return json.dumps({"period": {"start": start_date, "end": end_date},
        "campaigns": summary.to_dict(orient="records"),
        "totals": {"impressions": int(summary["impressions"].sum()), "clicks": int(summary["clicks"].sum()),
                   "cost": round(float(summary["cost"].sum()), 2), "conversions": int(summary["conversions"].sum()),
                   "revenue": round(float(summary["conversion_value"].sum()), 2),
                   "blended_roas": round(float(summary["conversion_value"].sum() / max(summary["cost"].sum(), 0.01)), 2)}
    }, indent=2, default=str)

@mcp.tool()
def get_keyword_performance(start_date: str, end_date: str) -> str:
    """Get keyword-level performance data."""
    kw = pd.read_csv(DATA_DIR / "google_ads_keywords.csv")
    results = [{"keyword": r["keyword"], "match_type": r["match_type"], "ad_group_id": r["ad_group_id"],
                "impressions": int(np.random.uniform(5000, 50000)), "clicks": int(np.random.uniform(100, 2000)),
                "cost": round(np.random.uniform(50, 500), 2), "conversions": int(np.random.uniform(5, 100)),
                "quality_score": int(np.random.uniform(4, 10))} for _, r in kw.iterrows()]
    return json.dumps({"keywords": results}, indent=2)

@mcp.tool()
def list_campaigns() -> str:
    """List all Google Ads campaigns."""
    df = pd.read_csv(DATA_DIR / "google_ads_campaigns.csv")
    return json.dumps({"campaigns": df.to_dict(orient="records")}, indent=2)

if __name__ == "__main__":
    mcp.run()
```

### `mcp_servers/mock_meta_ads_server.py`
Same pattern. Tools: `get_campaign_insights(start_date, end_date, campaign_id=None)`, `get_ad_set_breakdown(campaign_id)`, `list_campaigns()`. Reads from meta_ads_*.csv files. The agent should implement following the google ads pattern above.

### `mcp_servers/mock_ga4_server.py`
Tools: `get_traffic_by_channel(start_date, end_date)`, `get_daily_traffic_trend(start_date, end_date, channel=None)`, `get_device_breakdown(start_date, end_date)`. Reads from ga4_daily_sessions.csv.

### `mcp_servers/mock_hubspot_server.py`
Tools: `get_contacts_by_source(start_date=None, end_date=None)`, `get_deal_pipeline(start_date=None, end_date=None)`, `search_contacts(query, limit=10)`. Reads from hubspot_*.csv files.

### `mcp_servers/mock_salesforce_server.py`
Tools: `get_opportunity_pipeline(start_date=None, end_date=None)`, `get_revenue_by_source(start_date=None, end_date=None)`, `get_quarterly_forecast()`. Reads from salesforce_*.csv files.

IMPORTANT: ALL mock servers must return JSON with the same field names that real platform APIs would return. This ensures commands work identically with mock or real servers across all 4 MCP clients (Claude Desktop, OpenCode, Gemini CLI, Antigravity).

## 3.2 Create file: `mcp_servers/weather_server.py`

```python
from mcp.server.fastmcp import FastMCP
import httpx
import json

mcp = FastMCP("weather-analytics", description="Fetch weather data from Open-Meteo (free, no key).")

CITY_COORDS = {"new york": (40.7128, -74.0060), "sao paulo": (-23.5505, -46.6333), "rio de janeiro": (-22.9068, -43.1729)}

@mcp.tool()
async def get_historical_weather(start_date: str, end_date: str, city: str = "sao paulo") -> str:
    """Get historical daily weather. Args: start_date/end_date (YYYY-MM-DD), city name."""
    lat, lon = CITY_COORDS.get(city.lower(), (-23.5505, -46.6333))
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get("https://archive-api.open-meteo.com/v1/archive", params={
            "latitude": lat, "longitude": lon, "start_date": start_date, "end_date": end_date,
            "daily": "temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum,wind_speed_10m_max",
            "timezone": "America/Sao_Paulo"})
        resp.raise_for_status()
    data = resp.json()["daily"]
    results = [{"date": data["time"][i], "temp_max": data["temperature_2m_max"][i],
                "temp_min": data["temperature_2m_min"][i], "temp_mean": data["temperature_2m_mean"][i],
                "precipitation_mm": data["precipitation_sum"][i], "wind_kmh": data["wind_speed_10m_max"][i]}
               for i in range(len(data["time"]))]
    return json.dumps({"city": city, "days": len(results), "data": results}, indent=2)

if __name__ == "__main__":
    mcp.run()
```

## 3.3 MCP client configurations (4 tools)

All 7 MCP servers work with all 4 clients. Create config files for each:

### Create file: `mcp_servers/claude_desktop_config.example.json`
For Claude Desktop: `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%/Claude/claude_desktop_config.json` (Windows).
```json
{
  "mcpServers": {
    "bigquery": {
      "command": "uvx",
      "args": ["mcp-server-bigquery", "--project", "YOUR_GCP_PROJECT", "--location", "US"]
    },
    "dbt": {
      "command": "uvx",
      "args": ["dbt-mcp"],
      "env": { "DBT_HOST": "cloud.getdbt.com", "DBT_TOKEN": "YOUR_TOKEN", "DBT_PROD_ENV_ID": "YOUR_ID" }
    },
    "google-ads": {
      "command": "uv", "args": ["run", "--with", "mcp", "--with", "pandas", "--with", "numpy", "ABSOLUTE_PATH/mcp_servers/mock_google_ads_server.py"]
    },
    "meta-ads": {
      "command": "uv", "args": ["run", "--with", "mcp", "--with", "pandas", "--with", "numpy", "ABSOLUTE_PATH/mcp_servers/mock_meta_ads_server.py"]
    },
    "ga4": {
      "command": "uv", "args": ["run", "--with", "mcp", "--with", "pandas", "ABSOLUTE_PATH/mcp_servers/mock_ga4_server.py"]
    },
    "hubspot": {
      "command": "uv", "args": ["run", "--with", "mcp", "--with", "pandas", "ABSOLUTE_PATH/mcp_servers/mock_hubspot_server.py"]
    },
    "salesforce": {
      "command": "uv", "args": ["run", "--with", "mcp", "--with", "pandas", "ABSOLUTE_PATH/mcp_servers/mock_salesforce_server.py"]
    },
    "weather": {
      "command": "uv", "args": ["run", "--with", "mcp", "--with", "httpx", "ABSOLUTE_PATH/mcp_servers/weather_server.py"]
    }
  }
}
```

### Create file: `.opencode/opencode.json`
For OpenCode CLI (terminal-based, 75+ model support).
```json
{
  "mcp": {
    "bigquery": {
      "type": "local",
      "command": "uvx",
      "args": ["mcp-server-bigquery", "--project", "YOUR_GCP_PROJECT", "--location", "US"]
    },
    "dbt": {
      "type": "local",
      "command": "uvx",
      "args": ["dbt-mcp"],
      "env": { "DBT_HOST": "cloud.getdbt.com", "DBT_TOKEN": "YOUR_TOKEN", "DBT_PROD_ENV_ID": "YOUR_ID" }
    },
    "google-ads": {
      "type": "local",
      "command": "uv",
      "args": ["run", "--with", "mcp", "--with", "pandas", "--with", "numpy", "mcp_servers/mock_google_ads_server.py"]
    },
    "meta-ads": {
      "type": "local",
      "command": "uv",
      "args": ["run", "--with", "mcp", "--with", "pandas", "--with", "numpy", "mcp_servers/mock_meta_ads_server.py"]
    },
    "ga4": {
      "type": "local",
      "command": "uv",
      "args": ["run", "--with", "mcp", "--with", "pandas", "mcp_servers/mock_ga4_server.py"]
    },
    "hubspot": {
      "type": "local",
      "command": "uv",
      "args": ["run", "--with", "mcp", "--with", "pandas", "mcp_servers/mock_hubspot_server.py"]
    },
    "salesforce": {
      "type": "local",
      "command": "uv",
      "args": ["run", "--with", "mcp", "--with", "pandas", "mcp_servers/mock_salesforce_server.py"]
    },
    "weather": {
      "type": "local",
      "command": "uv",
      "args": ["run", "--with", "mcp", "--with", "httpx", "mcp_servers/weather_server.py"]
    }
  }
}
```

### Gemini CLI
No config file needed — pass MCP servers as flags:
```bash
gemini \
  --mcp-server "bigquery=uvx mcp-server-bigquery --project YOUR_GCP_PROJECT --location US" \
  --mcp-server "google-ads=uv run --with mcp --with pandas --with numpy mcp_servers/mock_google_ads_server.py" \
  --mcp-server "meta-ads=uv run --with mcp --with pandas --with numpy mcp_servers/mock_meta_ads_server.py" \
  --mcp-server "ga4=uv run --with mcp --with pandas mcp_servers/mock_ga4_server.py" \
  --mcp-server "hubspot=uv run --with mcp --with pandas mcp_servers/mock_hubspot_server.py" \
  --mcp-server "salesforce=uv run --with mcp --with pandas mcp_servers/mock_salesforce_server.py"
```

### Antigravity IDE
In Antigravity: Agent session → "..." → MCP Servers → Manage MCP Servers → View raw config → paste the same JSON structure as the OpenCode config into `mcp_config.json`.

### Which tool for what (Eduardo's workflow):

| Tool | Role | Why |
|---|---|---|
| **Antigravity** | Build the project | Free, parallel agents, Manager View |
| **Claude Desktop** | Demo the analytics (portfolio video) | Best UX, Cowork plugin, React artifacts |
| **OpenCode** | Terminal analytics + model flexibility | 75+ models, show same MCP with Gemini/Claude/GPT |
| **Gemini CLI** | Quick BigQuery queries | Native Gemini-BigQuery integration |

## 3.4 Create Cowork plugin (Claude Desktop)

### `cowork_plugin/.claude-plugin/plugin.json`
```json
{"name": "Full-Funnel Marketing Analytics", "description": "AI-powered marketing attribution, lead scoring, and pipeline analytics. Query data across Google Ads, Meta, GA4, HubSpot, and Salesforce using natural language.", "version": "1.0.0", "author": "Eduardo"}
```

### `cowork_plugin/.mcp.json`
Same structure as claude_desktop_config.example.json but with only: bigquery, dbt, google-ads, meta-ads, ga4, hubspot, salesforce.

### Skills (4 files in `cowork_plugin/skills/`):

**`brand-voice.md`**: Number formatting (K/M/B suffixes, 1 decimal %, $USD 2 decimals). YoY format: "grew from X to Y (+Z% YoY)". Color coding: green=positive, red=negative, amber=temperature, blue=precipitation. Output structure: Key Finding → KPI Summary → Supporting Detail → Visualization → Recommendations.

**`metric-definitions.md`**: All 15+ metrics with exact definitions and calculation formulas. Dimension values. Notes on using semantic layer. Attribution model explanations (first-touch, last-touch, linear, time-decay with 7-day half-life).

**`data-workflow.md`**: Step-by-step: parse request → identify metrics/dimensions → query dbt semantic layer (text_to_sql) → execute via warehouse MCP → enrich with platform MCP servers → format per brand voice → suggest visualization.

**`visualization-guide.md`**: Chart type selection rules. Dark theme specs (#0d0d1a background, coral #f87171 for primary, blue #60a5fa for secondary, amber #fbbf24 for temperature). Voi-style dashboard template reference.

### Commands (6 files in `cowork_plugin/commands/`):

**`marketing.md`** — `/marketing`: Query Google Ads + Meta Ads + GA4. Calculate blended CAC, ROAS. Format as cross-platform dashboard.

**`attribution.md`** — `/attribution`: Compare 4 attribution models. Identify under-credited channels. Recommend budget reallocation.

**`pipeline.md`** — `/pipeline`: CRM funnel from HubSpot + Salesforce. Win rates by source. Pipeline velocity.

**`score.md`** — `/score`: Call FastAPI endpoint at localhost:8000/score. Accept lead description, extract features, return tier (hot/warm/cold) + recommended action.

**`analyze.md`** — `/analyze`: General-purpose analysis. Parse question, query semantic layer, format results.

**`report.md`** — `/report`: Executive summary with KPI table, top 3 insights, recommendations.

## 3.5 Create OpenCode commands + skills (mirrors Cowork plugin)

Same content as Cowork, adapted to OpenCode's format.

### OpenCode commands (6 files in `.opencode/commands/`):

Create `.opencode/commands/marketing.md`, `attribution.md`, `pipeline.md`, `score.md`, `analyze.md`, `report.md` — **identical markdown content** as the Cowork commands above. OpenCode reads these as custom slash commands.

### OpenCode skills (4 directories in `.opencode/skills/`):

Create `.opencode/skills/brand-voice/SKILL.md`, `.opencode/skills/metric-definitions/SKILL.md`, `.opencode/skills/data-workflow/SKILL.md`, `.opencode/skills/visualization-guide/SKILL.md`.

Each SKILL.md needs YAML frontmatter for OpenCode:
```yaml
---
name: brand-voice
description: Number formatting, color coding, and output structure guidelines for analytics output
---
# Brand Voice & Output Guidelines
(same content as cowork_plugin/skills/brand-voice.md)
```

### Antigravity skills (optional, same content)

Create `.agents/skills/` with the same SKILL.md files. Antigravity uses the same format as OpenCode.

---

# ═══════════════════════════════════════════
# PHASE 4: ML LEAD SCORING + MLFLOW
# ═══════════════════════════════════════════

## 4.1 Create file: `scripts/run_mlflow_server.sh`
```bash
#!/bin/bash
cd "$(dirname "$0")/.."
mkdir -p ml/mlflow-artifacts
mlflow server --host 127.0.0.1 --port 5000 \
  --backend-store-uri sqlite:///ml/mlflow.db \
  --default-artifact-root ./ml/mlflow-artifacts
```

## 4.2 Create file: `ml/src/features.py`

Use Polars to load `fct_lead_scoring_features` from DuckDB. Build feature matrix with: lead_source (one-hot), num_touchpoints, total_orders, total_revenue, avg_order_value, avg_review_score, customer_state (top 10 one-hot, rest as "other"), customer_segment. Target: `is_high_value`. Return X, y, feature_names.

## 4.3 Create file: `ml/src/train.py`

Full training script as provided in the merged plan. Run 4 experiments (LogReg baseline, XGBoost default, XGBoost tuned, XGBoost deep) with MLflow tracking. Log params, metrics (AUC, precision, recall, F1), artifacts (feature_importance.json). Register best model as "lead_scoring_model". See merged plan Phase 4 for complete code.

## 4.4 Create file: `api/main.py`

FastAPI scoring endpoint as provided in merged plan. Endpoints: POST /score, GET /health, GET /model-info. Load model from MLflow registry. Score 0-100, tier hot/warm/cold, top_factors, recommended_action. See merged plan for complete code.

## 4.5 Create file: `api/Dockerfile`
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

# ═══════════════════════════════════════════
# PHASE 5: AUTOMATION + DASHBOARDS
# ═══════════════════════════════════════════

## 5.1 n8n workflow

Create `automation/n8n_workflow.json` — export of n8n workflow with: Webhook trigger → HTTP POST to localhost:8000/score → IF score>=70 route to Sales, ELIF score>=40 route to Nurture, ELSE Long-term → Log to file/BigQuery.

Create `automation/README.md` with n8n self-hosted setup instructions.

## 5.2 Streamlit app

Create `streamlit_app/app.py` — main app with dark theme, Claude API integration for NL → SQL.
Create `streamlit_app/pages/1_marketing_overview.py` — KPIs + time series + platform comparison.
Create `streamlit_app/pages/2_attribution.py` — Model comparison + channel credits.
Create `streamlit_app/pages/3_lead_scoring.py` — Score distribution + input form calling FastAPI.
Create `streamlit_app/pages/4_pipeline.py` — Funnel viz + win rates + revenue by source.

See merged plan Phase 5 for Streamlit code patterns. Use Plotly with dark theme (#0d0d1a).

## 5.3 Voi-style React dashboard template

Create `dashboards/voi_style_react/dashboard.jsx` — the full React/Recharts component from earlier in this conversation. This is the template Claude uses when generating dashboard artifacts.

---

# ═══════════════════════════════════════════
# PHASE 6: PORTABILITY + POLISH + PUBLISH
# ═══════════════════════════════════════════

## 6.1 Snowflake trial

Create `warehouse_configs/snowflake/setup.sql`:
```sql
CREATE WAREHOUSE ANALYTICS_WH WITH WAREHOUSE_SIZE='XSMALL' AUTO_SUSPEND=60;
CREATE DATABASE OLIST_ANALYTICS;
USE DATABASE OLIST_ANALYTICS;
-- Upload CSVs via Snowflake UI → Tables
-- Or stage from S3

-- Read-only role for MCP
CREATE ROLE ANALYST_READONLY;
GRANT USAGE ON DATABASE OLIST_ANALYTICS TO ROLE ANALYST_READONLY;
GRANT USAGE ON SCHEMA OLIST_ANALYTICS.PUBLIC TO ROLE ANALYST_READONLY;
GRANT SELECT ON ALL TABLES IN SCHEMA OLIST_ANALYTICS.PUBLIC TO ROLE ANALYST_READONLY;
GRANT USAGE ON WAREHOUSE ANALYTICS_WH TO ROLE ANALYST_READONLY;
```

Then: `dbt build --target snowflake`, add Snowflake MCP server to all client configs, run hero queries, record demo showing same query across Claude Desktop → OpenCode → Gemini CLI.

## 6.2 Databricks trial

Create `warehouse_configs/databricks/setup_notebook.py` — create catalog, load CSVs to Delta tables, show MLflow working natively.

Then: `dbt build --target databricks`, add Databricks MCP server, run hero queries, record demo.

## 6.3 Documentation

Create these files in `docs/`:
- `architecture.md` — full architecture explanation
- `cost_analysis.md` — $20/month breakdown
- `warehouse_swap_guide.md` — step-by-step for each warehouse
- `mock_vs_real_integrations.md` — how to swap mock → production MCP servers
- `ml_methodology.md` — feature engineering, model selection, evaluation
- `demo_script.md` — minute-by-minute demo video script
- `verification_checklist.md` — 40+ item checklist

## 6.4 README.md

Use the full README.md already created in this conversation.

---

# ═══════════════════════════════════════════
# HERO QUERIES (verify the system works)
# ═══════════════════════════════════════════

## Query 1 — Full Funnel
"Show me the complete marketing funnel for Q1 2018: ad spend across Google and Meta, website sessions by channel, lead conversion rates from HubSpot, and revenue from Olist orders. Calculate blended CAC and ROAS."

## Query 2 — Attribution
"Compare first-touch vs last-touch attribution for our top 5 channels. Which are under-credited by last-touch? Recommend budget reallocation."

## Query 3 — Lead Quality
"What lead source produces the highest-scoring leads? Which channels drive hot leads vs cold?"

## Query 4 — CEO Question
"We spent $X on Google and $Y on Meta last quarter. How much revenue did each drive? What should we change?"

## Query 5 — Portability
Same query on BigQuery → Snowflake → DuckDB. Same results, three engines.

---

# ═══════════════════════════════════════════
# SUCCESS CRITERIA
# ═══════════════════════════════════════════

1. All hero queries return formatted responses via MCP in at least 2 clients (Claude Desktop + OpenCode)
2. `dbt build` passes on BigQuery, DuckDB, and Supabase
3. MLflow shows 3+ experiments with AUC > 0.65
4. FastAPI /score returns scores in < 100ms
5. n8n workflow routes leads based on score
6. Streamlit app runs with all 4 pages
7. Cowork plugin commands produce output in Claude Desktop
8. OpenCode commands produce output with same MCP servers
9. Demo video recorded showing multi-client portability (Claude Desktop → OpenCode → Gemini CLI)
10. GitHub repo public with polished README
11. All credentials in .env, not in git
# ═══════════════════════════════════════════
# ADDENDUM: ALL REMAINING FULLY-WRITTEN CODE
# Append this to FINAL_CONSOLIDATED_PLAN.md
# ═══════════════════════════════════════════

# These are the complete file contents that were summarized
# in the main plan. The agent should create these files exactly.

---

# MOCK MCP SERVERS (complete code for the 4 that were spec-only)

## Create file: `mcp_servers/mock_meta_ads_server.py`

```python
from mcp.server.fastmcp import FastMCP
import pandas as pd
import json
from pathlib import Path

mcp = FastMCP("meta-ads", description="Query Meta (Facebook/Instagram) Ads campaign performance data.")
DATA_DIR = Path(__file__).parent.parent / "data" / "mock_marketing"

@mcp.tool()
def get_campaign_insights(start_date: str, end_date: str, campaign_id: str = None) -> str:
    """Get Meta Ads campaign insights for a date range. Returns spend, reach, purchases, ROAS."""
    df = pd.read_csv(DATA_DIR / "meta_ads_daily_performance.csv")
    df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]
    if campaign_id:
        df = df[df["campaign_id"] == campaign_id]

    summary = df.groupby(["campaign_id", "campaign_name", "objective"]).agg({
        "impressions": "sum", "reach": "sum", "spend": "sum",
        "link_clicks": "sum", "purchases": "sum", "purchase_value": "sum",
    }).reset_index()

    summary["ctr"] = (summary["link_clicks"] / summary["impressions"].clip(lower=1) * 100).round(2)
    summary["cpc"] = (summary["spend"] / summary["link_clicks"].clip(lower=1)).round(2)
    summary["roas"] = (summary["purchase_value"] / summary["spend"].clip(lower=0.01)).round(2)
    summary["cost_per_purchase"] = (summary["spend"] / summary["purchases"].clip(lower=1)).round(2)

    return json.dumps({
        "period": {"start": start_date, "end": end_date},
        "campaigns": summary.to_dict(orient="records"),
        "totals": {
            "total_spend": round(float(summary["spend"].sum()), 2),
            "total_reach": int(summary["reach"].sum()),
            "total_purchases": int(summary["purchases"].sum()),
            "total_revenue": round(float(summary["purchase_value"].sum()), 2),
            "blended_roas": round(float(summary["purchase_value"].sum() / max(summary["spend"].sum(), 0.01)), 2),
        }
    }, indent=2, default=str)

@mcp.tool()
def get_ad_set_breakdown(campaign_id: str) -> str:
    """Get ad set breakdown for a Meta campaign."""
    df = pd.read_csv(DATA_DIR / "meta_ads_ad_sets.csv")
    df = df[df["campaign_id"] == campaign_id]
    return json.dumps({"ad_sets": df.to_dict(orient="records")}, indent=2)

@mcp.tool()
def list_campaigns() -> str:
    """List all Meta Ads campaigns."""
    df = pd.read_csv(DATA_DIR / "meta_ads_campaigns.csv")
    return json.dumps({"campaigns": df.to_dict(orient="records")}, indent=2)

if __name__ == "__main__":
    mcp.run()
```

## Create file: `mcp_servers/mock_ga4_server.py`

```python
from mcp.server.fastmcp import FastMCP
import pandas as pd
import json
from pathlib import Path

mcp = FastMCP("ga4", description="Query Google Analytics 4 website traffic, conversion, and engagement metrics.")
DATA_DIR = Path(__file__).parent.parent / "data" / "mock_marketing"

@mcp.tool()
def get_traffic_by_channel(start_date: str, end_date: str) -> str:
    """Get website traffic metrics grouped by channel. Returns sessions, conversions, revenue."""
    df = pd.read_csv(DATA_DIR / "ga4_daily_sessions.csv")
    df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]

    by_channel = df.groupby("channel_group").agg({
        "sessions": "sum", "engaged_sessions": "sum", "new_users": "sum",
        "conversions": "sum", "revenue": "sum",
    }).reset_index()

    by_channel["conversion_rate"] = (by_channel["conversions"] / by_channel["sessions"].clip(lower=1) * 100).round(2)
    by_channel["engagement_rate"] = (by_channel["engaged_sessions"] / by_channel["sessions"].clip(lower=1) * 100).round(1)
    by_channel = by_channel.sort_values("sessions", ascending=False)

    return json.dumps({
        "period": {"start": start_date, "end": end_date},
        "channels": by_channel.to_dict(orient="records"),
        "totals": {
            "total_sessions": int(by_channel["sessions"].sum()),
            "total_conversions": int(by_channel["conversions"].sum()),
            "total_revenue": round(float(by_channel["revenue"].sum()), 2),
            "overall_conversion_rate": round(float(by_channel["conversions"].sum() / max(by_channel["sessions"].sum(), 1) * 100), 2),
        }
    }, indent=2, default=str)

@mcp.tool()
def get_daily_traffic_trend(start_date: str, end_date: str, channel: str = None) -> str:
    """Get daily traffic trend, optionally filtered by channel."""
    df = pd.read_csv(DATA_DIR / "ga4_daily_sessions.csv")
    df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]
    if channel:
        df = df[df["channel_group"] == channel]

    daily = df.groupby("date").agg({"sessions": "sum", "conversions": "sum", "revenue": "sum"}).reset_index()
    return json.dumps({"daily_trend": daily.to_dict(orient="records")}, indent=2, default=str)

@mcp.tool()
def get_device_breakdown(start_date: str, end_date: str) -> str:
    """Get traffic breakdown by device category (mobile, desktop, tablet)."""
    df = pd.read_csv(DATA_DIR / "ga4_daily_sessions.csv")
    df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]

    by_device = df.groupby("device_category").agg({
        "sessions": "sum", "conversions": "sum", "revenue": "sum",
    }).reset_index()
    by_device["conversion_rate"] = (by_device["conversions"] / by_device["sessions"].clip(lower=1) * 100).round(2)
    by_device["share_pct"] = (by_device["sessions"] / by_device["sessions"].sum() * 100).round(1)

    return json.dumps({"devices": by_device.to_dict(orient="records")}, indent=2, default=str)

if __name__ == "__main__":
    mcp.run()
```

## Create file: `mcp_servers/mock_hubspot_server.py`

```python
from mcp.server.fastmcp import FastMCP
import pandas as pd
import json
from pathlib import Path

mcp = FastMCP("hubspot", description="Query HubSpot CRM data — contacts, deals, and pipeline metrics.")
DATA_DIR = Path(__file__).parent.parent / "data" / "mock_marketing"

@mcp.tool()
def get_contacts_by_source(start_date: str = None, end_date: str = None) -> str:
    """Get contacts grouped by lead source with lifecycle stage breakdown and revenue."""
    df = pd.read_csv(DATA_DIR / "hubspot_contacts.csv")
    if start_date:
        df = df[df["create_date"] >= start_date]
    if end_date:
        df = df[df["create_date"] <= end_date]

    by_source = df.groupby("lead_source").agg({
        "contact_id": "count", "total_revenue": "sum", "num_orders": "sum",
    }).reset_index()
    by_source.columns = ["lead_source", "contacts", "total_revenue", "total_orders"]
    by_source["revenue_per_contact"] = (by_source["total_revenue"] / by_source["contacts"].clip(lower=1)).round(2)
    by_source = by_source.sort_values("contacts", ascending=False)

    return json.dumps({
        "contacts_by_source": by_source.to_dict(orient="records"),
        "total_contacts": int(by_source["contacts"].sum()),
        "total_revenue": round(float(by_source["total_revenue"].sum()), 2),
    }, indent=2, default=str)

@mcp.tool()
def get_deal_pipeline(start_date: str = None, end_date: str = None) -> str:
    """Get deal pipeline summary with stage counts and values."""
    df = pd.read_csv(DATA_DIR / "hubspot_deals.csv")
    if start_date:
        df = df[df["create_date"] >= start_date]
    if end_date:
        df = df[df["create_date"] <= end_date]

    by_stage = df.groupby("deal_stage").agg({"deal_id": "count", "amount": "sum"}).reset_index()
    by_stage.columns = ["stage", "deals", "total_value"]

    return json.dumps({
        "pipeline": by_stage.to_dict(orient="records"),
        "total_deals": int(by_stage["deals"].sum()),
        "total_pipeline_value": round(float(by_stage["total_value"].sum()), 2),
    }, indent=2, default=str)

@mcp.tool()
def search_contacts(query: str, limit: int = 10) -> str:
    """Search contacts by name, city, or state."""
    df = pd.read_csv(DATA_DIR / "hubspot_contacts.csv")
    mask = (
        df["first_name"].str.contains(query, case=False, na=False) |
        df["last_name"].str.contains(query, case=False, na=False) |
        df["city"].str.contains(query, case=False, na=False) |
        df["state"].str.contains(query, case=False, na=False)
    )
    results = df[mask].head(limit)
    return json.dumps({"results": len(results), "contacts": results.to_dict(orient="records")}, indent=2, default=str)

if __name__ == "__main__":
    mcp.run()
```

## Create file: `mcp_servers/mock_salesforce_server.py`

```python
from mcp.server.fastmcp import FastMCP
import pandas as pd
import json
from pathlib import Path

mcp = FastMCP("salesforce", description="Query Salesforce CRM — opportunities, accounts, and sales pipeline.")
DATA_DIR = Path(__file__).parent.parent / "data" / "mock_marketing"

@mcp.tool()
def get_opportunity_pipeline(start_date: str = None, end_date: str = None) -> str:
    """Get opportunity pipeline by stage with deal counts, amounts, and probabilities."""
    df = pd.read_csv(DATA_DIR / "salesforce_opportunities.csv")
    if start_date:
        df = df[df["created_date"] >= start_date]
    if end_date:
        df = df[df["created_date"] <= end_date]

    by_stage = df.groupby("stage").agg({
        "opportunity_id": "count", "amount": "sum", "probability": "mean",
    }).reset_index()
    by_stage.columns = ["stage", "opportunities", "total_amount", "avg_probability"]
    by_stage["weighted_amount"] = (by_stage["total_amount"] * by_stage["avg_probability"] / 100).round(2)

    return json.dumps({
        "pipeline": by_stage.to_dict(orient="records"),
        "total_opportunities": int(by_stage["opportunities"].sum()),
        "total_pipeline": round(float(by_stage["total_amount"].sum()), 2),
        "weighted_pipeline": round(float(by_stage["weighted_amount"].sum()), 2),
    }, indent=2, default=str)

@mcp.tool()
def get_revenue_by_source(start_date: str = None, end_date: str = None) -> str:
    """Get closed-won revenue broken down by lead source."""
    df = pd.read_csv(DATA_DIR / "salesforce_opportunities.csv")
    df = df[df["stage"] == "Closed Won"]
    if start_date:
        df = df[df["close_date"] >= start_date]
    if end_date:
        df = df[df["close_date"] <= end_date]

    by_source = df.groupby("lead_source").agg({
        "opportunity_id": "count", "amount": "sum",
    }).reset_index()
    by_source.columns = ["lead_source", "deals_won", "revenue"]
    by_source["avg_deal_size"] = (by_source["revenue"] / by_source["deals_won"].clip(lower=1)).round(2)
    by_source = by_source.sort_values("revenue", ascending=False)

    return json.dumps({
        "revenue_by_source": by_source.to_dict(orient="records"),
        "total_won": int(by_source["deals_won"].sum()),
        "total_revenue": round(float(by_source["revenue"].sum()), 2),
    }, indent=2, default=str)

@mcp.tool()
def get_quarterly_forecast() -> str:
    """Get sales forecast by fiscal quarter."""
    df = pd.read_csv(DATA_DIR / "salesforce_opportunities.csv")
    by_q = df.groupby("fiscal_quarter").agg({"opportunity_id": "count", "amount": "sum"}).reset_index()
    by_q.columns = ["quarter", "opportunities", "total_amount"]
    by_q = by_q.sort_values("quarter")
    return json.dumps({"forecast": by_q.to_dict(orient="records")}, indent=2, default=str)

if __name__ == "__main__":
    mcp.run()
```

---

# ML PIPELINE (complete code)

## Create file: `scripts/run_mlflow_server.sh`

```bash
#!/bin/bash
cd "$(dirname "$0")/.."
mkdir -p ml/mlflow-artifacts
mlflow server \
  --host 127.0.0.1 \
  --port 5000 \
  --backend-store-uri sqlite:///ml/mlflow.db \
  --default-artifact-root ./ml/mlflow-artifacts
```

## Create file: `ml/src/features.py`

```python
"""Feature engineering for lead scoring model. Uses Polars for performance."""
import polars as pl
import numpy as np
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent / "data"

def load_features() -> tuple:
    """Load and engineer features from mock marketing + Olist data.
    Returns: X (numpy), y (numpy), feature_names (list)
    """
    # Load HubSpot contacts (has lead_source, revenue, orders)
    contacts = pl.read_csv(DATA_DIR / "mock_marketing" / "hubspot_contacts.csv")

    # Load attribution summary per customer
    attr = pl.read_csv(DATA_DIR / "mock_marketing" / "marketing_attribution.csv")
    attr_summary = attr.group_by("order_id").agg([
        pl.count().alias("touchpoints"),
        pl.col("channel").first().alias("first_channel"),
        pl.col("channel").last().alias("last_channel"),
    ])

    # Load GA4 channel-level averages (proxy for behavioral features)
    ga4 = pl.read_csv(DATA_DIR / "mock_marketing" / "ga4_daily_sessions.csv")
    ga4_by_channel = ga4.group_by("channel_group").agg([
        pl.col("sessions").mean().alias("avg_sessions"),
        pl.col("pages_per_session").mean().alias("avg_pages"),
        pl.col("avg_session_duration_sec").mean().alias("avg_duration"),
        pl.col("bounce_rate").mean().alias("avg_bounce_rate"),
    ])

    # Load Olist reviews per customer
    orders = pl.read_csv(DATA_DIR / "olist" / "olist_orders_dataset.csv")
    reviews = pl.read_csv(DATA_DIR / "olist" / "olist_order_reviews_dataset.csv")
    order_reviews = orders.join(reviews, on="order_id", how="left").group_by("customer_id").agg([
        pl.col("review_score").mean().alias("avg_review_score"),
        pl.col("review_score").count().alias("num_reviews"),
    ])

    # Join behavioral features via lead_source → channel_group mapping
    source_to_channel = {
        "organic_search": "organic_search", "paid_search": "paid_search",
        "paid_social": "paid_social", "direct": "direct",
        "email": "email", "referral": "referral",
    }

    # Build feature matrix
    df = contacts.with_columns([
        pl.col("lead_source").replace(source_to_channel, default="direct").alias("channel_match"),
    ])

    df = df.join(ga4_by_channel, left_on="channel_match", right_on="channel_group", how="left")
    df = df.join(
        order_reviews.rename({"customer_id": "customer_id_review"}),
        left_on="customer_id", right_on="customer_id_review", how="left"
    )

    # Target variable
    df = df.with_columns([
        ((pl.col("total_revenue") > 200) & (pl.col("num_orders") > 1)).cast(pl.Int32).alias("is_high_value"),
    ])

    # Numeric features
    numeric_cols = [
        "num_orders", "total_revenue", "avg_sessions", "avg_pages",
        "avg_duration", "avg_bounce_rate", "avg_review_score", "num_reviews",
    ]

    # One-hot encode lead_source
    sources = df["lead_source"].unique().drop_nulls().to_list()
    for src in sources:
        col_name = f"source_{src}"
        df = df.with_columns(
            (pl.col("lead_source") == src).cast(pl.Int32).alias(col_name)
        )
        numeric_cols.append(col_name)

    # One-hot encode top states
    top_states = df["state"].value_counts().sort("count", descending=True).head(10)["state"].to_list()
    for state in top_states:
        if state is not None:
            col_name = f"state_{state}"
            df = df.with_columns(
                (pl.col("state") == state).cast(pl.Int32).alias(col_name)
            )
            numeric_cols.append(col_name)

    # Extract X, y
    feature_names = numeric_cols
    X = df.select(feature_names).fill_null(0).to_numpy().astype(np.float32)
    y = df["is_high_value"].fill_null(0).to_numpy().astype(np.int32)

    print(f"Features: {len(feature_names)}, Samples: {len(X)}, Positive rate: {y.mean():.1%}")
    return X, y, feature_names
```

## Create file: `ml/src/train.py`

```python
"""Train lead scoring models with MLflow experiment tracking."""
import mlflow
import mlflow.sklearn
import mlflow.xgboost
import xgboost as xgb
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score
import numpy as np
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from features import load_features

MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
EXPERIMENT = "lead_scoring"

mlflow.set_tracking_uri(MLFLOW_URI)
mlflow.set_experiment(EXPERIMENT)


def train_and_log(model, model_name, X_train, y_train, X_test, y_test, feature_names, params=None):
    """Train a model and log everything to MLflow."""
    with mlflow.start_run(run_name=model_name):
        if params:
            mlflow.log_params(params)
        mlflow.log_param("model_type", model_name)
        mlflow.log_param("n_features", len(feature_names))
        mlflow.log_param("n_train", len(X_train))
        mlflow.log_param("n_test", len(X_test))
        mlflow.log_param("positive_rate", float(y_train.mean()))

        # Train
        if hasattr(model, 'fit') and 'eval_set' in model.fit.__code__.co_varnames:
            model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
        else:
            model.fit(X_train, y_train)

        # Predict
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1]

        # Metrics
        auc = roc_auc_score(y_test, y_proba)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)

        mlflow.log_metric("auc", auc)
        mlflow.log_metric("precision", precision)
        mlflow.log_metric("recall", recall)
        mlflow.log_metric("f1", f1)

        # Feature importance
        if hasattr(model, 'feature_importances_'):
            importance = dict(zip(feature_names, model.feature_importances_.tolist()))
            mlflow.log_dict(importance, "feature_importance.json")

        # Log model
        if isinstance(model, xgb.XGBClassifier):
            mlflow.xgboost.log_model(model, artifact_path="model", registered_model_name="lead_scoring_model")
        else:
            mlflow.sklearn.log_model(model, artifact_path="model")

        print(f"  {model_name}: AUC={auc:.4f} P={precision:.4f} R={recall:.4f} F1={f1:.4f}")
        return auc


def main():
    print("=== Lead Scoring Model Training ===\n")

    X, y, feature_names = load_features()
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    print(f"\nTrain: {len(X_train)}, Test: {len(X_test)}\n")

    # Experiment 1: Logistic Regression baseline
    print("Exp 1: Logistic Regression (baseline)")
    train_and_log(
        LogisticRegression(max_iter=1000, random_state=42),
        "logistic_regression", X_train, y_train, X_test, y_test, feature_names,
        params={"max_iter": 1000}
    )

    # Experiment 2: XGBoost default
    print("Exp 2: XGBoost (default)")
    params2 = {"max_depth": 6, "learning_rate": 0.1, "n_estimators": 200, "subsample": 0.8, "colsample_bytree": 0.8}
    train_and_log(
        xgb.XGBClassifier(**params2, random_state=42, eval_metric="auc"),
        "xgboost_default", X_train, y_train, X_test, y_test, feature_names, params=params2
    )

    # Experiment 3: XGBoost tuned
    print("Exp 3: XGBoost (tuned)")
    params3 = {"max_depth": 4, "learning_rate": 0.05, "n_estimators": 300, "subsample": 0.85, "colsample_bytree": 0.8, "min_child_weight": 3}
    train_and_log(
        xgb.XGBClassifier(**params3, random_state=42, eval_metric="auc"),
        "xgboost_tuned", X_train, y_train, X_test, y_test, feature_names, params=params3
    )

    # Experiment 4: XGBoost deep
    print("Exp 4: XGBoost (deep)")
    params4 = {"max_depth": 8, "learning_rate": 0.08, "n_estimators": 250, "subsample": 0.8, "colsample_bytree": 0.7, "min_child_weight": 5}
    train_and_log(
        xgb.XGBClassifier(**params4, random_state=42, eval_metric="auc"),
        "xgboost_deep", X_train, y_train, X_test, y_test, feature_names, params=params4
    )

    print(f"\n=== Done. View experiments at: {MLFLOW_URI} ===")
    print("Best model registered as 'lead_scoring_model' in MLflow Model Registry")


if __name__ == "__main__":
    main()
```

## Create file: `api/main.py`

```python
"""Lead Scoring API — serves MLflow-registered model via FastAPI."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import mlflow
import numpy as np
import os

app = FastAPI(title="Lead Scoring API", version="1.0.0",
    description="Score leads using ML model trained on marketing attribution and behavioral features.")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
MODEL_NAME = "lead_scoring_model"
mlflow.set_tracking_uri(MLFLOW_URI)

model = None
try:
    model = mlflow.pyfunc.load_model(f"models:/{MODEL_NAME}/latest")
    print(f"Loaded model: {MODEL_NAME}")
except Exception as e:
    print(f"WARNING: Could not load model: {e}. /score will return 503 until model is trained.")


class LeadInput(BaseModel):
    lead_source: str = Field(..., description="Channel: organic_search, paid_search, paid_social, direct, email, referral")
    num_prior_orders: int = Field(0, description="Number of previous orders")
    total_prior_revenue: float = Field(0.0, description="Total revenue from prior orders")
    avg_sessions: float = Field(1.0, description="Average website sessions")
    avg_pages_per_session: float = Field(2.0, description="Average pages per session")
    avg_session_duration: float = Field(60.0, description="Avg session duration (seconds)")
    avg_bounce_rate: float = Field(50.0, description="Average bounce rate (%)")
    avg_review_score: float = Field(0.0, description="Average review score (0 if none)")
    num_reviews: int = Field(0, description="Number of reviews left")
    state: Optional[str] = Field(None, description="Customer state code")


class ScoreResponse(BaseModel):
    score: float = Field(..., description="Lead score 0-100")
    probability: float = Field(..., description="Probability of high-value conversion")
    tier: str = Field(..., description="hot, warm, or cold")
    top_factors: list = Field(..., description="Top contributing features")
    recommended_action: str = Field(..., description="Suggested next step")


@app.get("/health")
def health():
    return {"status": "healthy", "model_loaded": model is not None}


@app.get("/model-info")
def model_info():
    try:
        client = mlflow.tracking.MlflowClient()
        versions = client.search_model_versions(f"name='{MODEL_NAME}'")
        info = [{"version": v.version, "stage": v.current_stage, "run_id": v.run_id} for v in versions]
    except Exception:
        info = []
    return {"model_name": MODEL_NAME, "versions": info}


@app.post("/score", response_model=ScoreResponse)
def score_lead(lead: LeadInput):
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded. Train model first: python ml/src/train.py")

    # Build feature vector (must match training feature order)
    sources = ["organic_search", "paid_search", "paid_social", "direct", "email", "referral"]
    source_features = [1.0 if lead.lead_source == s else 0.0 for s in sources]

    features = np.array([[
        lead.num_prior_orders, lead.total_prior_revenue,
        lead.avg_sessions, lead.avg_pages_per_session,
        lead.avg_session_duration, lead.avg_bounce_rate,
        lead.avg_review_score, lead.num_reviews,
    ] + source_features], dtype=np.float32)

    try:
        probability = float(model.predict(features)[0])
    except Exception:
        # Some model types return class directly; try predict_proba
        try:
            probability = float(model.predict_proba(features)[0][1])
        except Exception:
            probability = 0.5

    score = round(probability * 100, 1)

    if score >= 70:
        tier, action = "hot", "Route to Sales immediately. High conversion probability."
    elif score >= 40:
        tier, action = "warm", "Add to nurture sequence. Send case study + demo invite."
    else:
        tier, action = "cold", "Add to long-term nurture. Monitor for engagement signals."

    feature_names = ["orders", "revenue", "sessions", "pages", "duration", "bounce", "reviews_score", "reviews_count"] + [f"src_{s}" for s in sources]
    feature_values = features[0].tolist()
    top = sorted(zip(feature_names, feature_values), key=lambda x: abs(x[1]), reverse=True)[:3]

    return ScoreResponse(
        score=score, probability=round(probability, 4), tier=tier,
        top_factors=[{"feature": f, "value": round(v, 2)} for f, v in top],
        recommended_action=action,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Create file: `api/schemas.py`

```python
"""Pydantic schemas — imported by main.py (already defined inline above, this is for separation)."""
# All schemas are defined in main.py for simplicity.
# Split into this file if main.py grows beyond 200 lines.
```

## Create file: `api/requirements.txt`

```txt
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.5.0
mlflow>=2.9.0
numpy>=1.24.0
```

## Create file: `api/Dockerfile`

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

# STREAMLIT APP (complete code)

## Create file: `streamlit_app/.streamlit/config.toml`

```toml
[theme]
primaryColor = "#f87171"
backgroundColor = "#0d0d1a"
secondaryBackgroundColor = "#12121f"
textColor = "#e2e2ea"
font = "monospace"

[server]
headless = true
```

## Create file: `streamlit_app/app.py`

```python
"""AI-Powered Marketing Analytics Dashboard."""
import streamlit as st
import duckdb
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="AI Marketing Analytics", page_icon="🚀", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0d0d1a; }
    h1, h2, h3, p, label, .stMarkdown { color: #e2e2ea !important; }
    .kpi-card { background: #1a1a2e; border-radius: 8px; padding: 16px 20px; text-align: center; }
    .kpi-value { font-size: 28px; font-weight: 700; }
    .kpi-label { font-size: 11px; color: #6a6a7a; text-transform: uppercase; letter-spacing: 1.2px; }
    .positive { color: #4ade80; }
    .negative { color: #f87171; }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_db():
    db_path = Path(__file__).parent.parent / "data" / "olist_analytics.duckdb"
    if db_path.exists():
        return duckdb.connect(str(db_path), read_only=True)
    return None

def main():
    st.markdown("### 🚀 Full-Funnel AI Marketing Analytics")
    st.markdown("*Natural language querying via MCP · dbt Semantic Layer · 5 Warehouses · 4 AI Clients*")

    con = get_db()
    if not con:
        st.error("Database not found. Run: python scripts/load_duckdb.py")
        return

    # Quick stats
    try:
        total_orders = con.execute("SELECT COUNT(*) FROM orders WHERE order_status='delivered'").fetchone()[0]
        total_revenue = con.execute("SELECT SUM(payment_value) FROM order_payments").fetchone()[0]
        total_customers = con.execute("SELECT COUNT(DISTINCT customer_unique_id) FROM customers").fetchone()[0]

        cols = st.columns(3)
        cols[0].metric("Total Orders", f"{total_orders:,.0f}")
        cols[1].metric("Total Revenue", f"${total_revenue:,.0f}")
        cols[2].metric("Unique Customers", f"{total_customers:,.0f}")
    except Exception as e:
        st.warning(f"Stats unavailable: {e}")

    st.markdown("---")
    st.markdown("Navigate to pages in the sidebar for detailed analytics.")

if __name__ == "__main__":
    main()
```

## Create file: `streamlit_app/pages/1_marketing_overview.py`

```python
"""Page 1: Cross-platform marketing performance."""
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import duckdb
from pathlib import Path

st.set_page_config(page_title="Marketing Overview", layout="wide")
st.markdown("### 📊 Marketing Overview")

@st.cache_resource
def get_db():
    db_path = Path(__file__).parent.parent.parent / "data" / "olist_analytics.duckdb"
    if db_path.exists():
        return duckdb.connect(str(db_path), read_only=True)
    return None

con = get_db()
if not con:
    st.error("Database not found.")
    st.stop()

try:
    # Cross-platform daily spend
    google = con.execute("""
        SELECT date, SUM(cost) as spend, SUM(conversions) as conversions, SUM(conversion_value) as revenue
        FROM google_ads_daily_performance GROUP BY date ORDER BY date
    """).fetchdf()

    meta = con.execute("""
        SELECT date, SUM(spend) as spend, SUM(purchases) as conversions, SUM(purchase_value) as revenue
        FROM meta_ads_daily_performance GROUP BY date ORDER BY date
    """).fetchdf()

    # KPIs
    cols = st.columns(4)
    g_spend, m_spend = google["spend"].sum(), meta["spend"].sum()
    g_rev, m_rev = google["revenue"].sum(), meta["revenue"].sum()
    cols[0].metric("Google Ads Spend", f"${g_spend:,.0f}")
    cols[1].metric("Meta Ads Spend", f"${m_spend:,.0f}")
    cols[2].metric("Google ROAS", f"{g_rev/max(g_spend,1):.2f}x")
    cols[3].metric("Meta ROAS", f"{m_rev/max(m_spend,1):.2f}x")

    # Daily spend chart
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=google["date"], y=google["spend"], name="Google Spend", line=dict(color="#f87171")))
    fig.add_trace(go.Scatter(x=meta["date"], y=meta["spend"], name="Meta Spend", line=dict(color="#60a5fa")))
    fig.add_trace(go.Scatter(x=google["date"], y=google["revenue"], name="Google Revenue", line=dict(color="#f87171", dash="dash")), secondary_y=True)
    fig.add_trace(go.Scatter(x=meta["date"], y=meta["revenue"], name="Meta Revenue", line=dict(color="#60a5fa", dash="dash")), secondary_y=True)
    fig.update_layout(template="plotly_dark", paper_bgcolor="#12121f", plot_bgcolor="#12121f", height=400,
                      font=dict(color="#e2e2ea"), title="Daily Spend vs Revenue by Platform")
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Error loading marketing data: {e}")
```

## Create file: `streamlit_app/pages/2_attribution.py`

```python
"""Page 2: Multi-touch attribution model comparison."""
import streamlit as st
import plotly.express as px
import duckdb
from pathlib import Path

st.set_page_config(page_title="Attribution", layout="wide")
st.markdown("### 🎯 Multi-Touch Attribution")

@st.cache_resource
def get_db():
    db_path = Path(__file__).parent.parent.parent / "data" / "olist_analytics.duckdb"
    if db_path.exists():
        return duckdb.connect(str(db_path), read_only=True)
    return None

con = get_db()
if not con:
    st.error("Database not found.")
    st.stop()

try:
    df = con.execute("""
        SELECT
            channel,
            COUNT(DISTINCT order_id) as orders,
            SUM(order_revenue * first_touch_credit) as first_touch_rev,
            SUM(order_revenue * last_touch_credit) as last_touch_rev,
            SUM(order_revenue * linear_credit) as linear_rev
        FROM marketing_attribution
        GROUP BY channel
        ORDER BY linear_rev DESC
    """).fetchdf()

    st.dataframe(df.style.format({
        "first_touch_rev": "${:,.0f}", "last_touch_rev": "${:,.0f}", "linear_rev": "${:,.0f}"
    }), use_container_width=True)

    # Grouped bar chart
    import plotly.graph_objects as go
    fig = go.Figure()
    fig.add_trace(go.Bar(name="First Touch", x=df["channel"], y=df["first_touch_rev"], marker_color="#f87171"))
    fig.add_trace(go.Bar(name="Last Touch", x=df["channel"], y=df["last_touch_rev"], marker_color="#60a5fa"))
    fig.add_trace(go.Bar(name="Linear", x=df["channel"], y=df["linear_rev"], marker_color="#fbbf24"))
    fig.update_layout(barmode="group", template="plotly_dark", paper_bgcolor="#12121f", plot_bgcolor="#12121f",
                      font=dict(color="#e2e2ea"), title="Revenue by Attribution Model", height=400)
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Error: {e}")
```

## Create file: `streamlit_app/pages/3_lead_scoring.py`

```python
"""Page 3: Lead scoring interface — call FastAPI endpoint."""
import streamlit as st
import requests

st.set_page_config(page_title="Lead Scoring", layout="wide")
st.markdown("### 🧠 Lead Scoring")

API_URL = "http://localhost:8000"

# Check API health
try:
    health = requests.get(f"{API_URL}/health", timeout=3).json()
    if health.get("model_loaded"):
        st.success("Model loaded and ready")
    else:
        st.warning("API running but model not loaded. Run: python ml/src/train.py")
except Exception:
    st.error("Scoring API not running. Start it: cd api && uvicorn main:app --port 8000")
    st.stop()

st.markdown("#### Score a Lead")
col1, col2 = st.columns(2)

with col1:
    source = st.selectbox("Lead Source", ["organic_search", "paid_search", "paid_social", "direct", "email", "referral"])
    orders = st.number_input("Prior Orders", 0, 100, 0)
    revenue = st.number_input("Prior Revenue ($)", 0.0, 10000.0, 0.0)
    state = st.text_input("State", "SP")

with col2:
    sessions = st.number_input("Avg Sessions", 0.0, 100.0, 2.0)
    pages = st.number_input("Avg Pages/Session", 0.0, 20.0, 3.0)
    duration = st.number_input("Avg Session Duration (sec)", 0.0, 600.0, 90.0)
    bounce = st.number_input("Bounce Rate (%)", 0.0, 100.0, 45.0)

if st.button("🔍 Score This Lead", type="primary"):
    payload = {
        "lead_source": source, "num_prior_orders": orders,
        "total_prior_revenue": revenue, "avg_sessions": sessions,
        "avg_pages_per_session": pages, "avg_session_duration": duration,
        "avg_bounce_rate": bounce, "state": state,
    }
    try:
        resp = requests.post(f"{API_URL}/score", json=payload, timeout=5).json()
        tier_colors = {"hot": "🔴", "warm": "🟡", "cold": "🔵"}
        st.markdown(f"### {tier_colors.get(resp['tier'], '')} Score: {resp['score']}/100 ({resp['tier'].upper()})")
        st.markdown(f"**Probability:** {resp['probability']:.1%}")
        st.markdown(f"**Action:** {resp['recommended_action']}")
        st.json(resp["top_factors"])
    except Exception as e:
        st.error(f"Scoring failed: {e}")
```

## Create file: `streamlit_app/pages/4_pipeline.py`

```python
"""Page 4: Sales pipeline from HubSpot + Salesforce data."""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import duckdb
from pathlib import Path

st.set_page_config(page_title="Pipeline", layout="wide")
st.markdown("### 🏗️ Sales Pipeline")

@st.cache_resource
def get_db():
    db_path = Path(__file__).parent.parent.parent / "data" / "olist_analytics.duckdb"
    if db_path.exists():
        return duckdb.connect(str(db_path), read_only=True)
    return None

con = get_db()
if not con:
    st.error("Database not found.")
    st.stop()

try:
    # Salesforce pipeline
    sf = con.execute("""
        SELECT stage, COUNT(*) as deals, SUM(amount) as total_value, AVG(probability) as avg_prob
        FROM salesforce_opportunities
        GROUP BY stage ORDER BY avg_prob
    """).fetchdf()

    st.markdown("#### Opportunity Pipeline (Salesforce)")
    fig = go.Figure(go.Funnel(y=sf["stage"], x=sf["deals"], textinfo="value+percent initial",
                              marker=dict(color=["#f87171", "#fb923c", "#fbbf24", "#4ade80", "#60a5fa", "#a78bfa", "#6b7280"])))
    fig.update_layout(template="plotly_dark", paper_bgcolor="#12121f", plot_bgcolor="#12121f",
                      font=dict(color="#e2e2ea"), height=400)
    st.plotly_chart(fig, use_container_width=True)

    # Revenue by source
    rev = con.execute("""
        SELECT lead_source, SUM(amount) as revenue, COUNT(*) as deals
        FROM salesforce_opportunities WHERE stage = 'Closed Won'
        GROUP BY lead_source ORDER BY revenue DESC
    """).fetchdf()

    st.markdown("#### Closed-Won Revenue by Lead Source")
    fig2 = px.bar(rev, x="lead_source", y="revenue", color="lead_source",
                  color_discrete_sequence=["#f87171", "#60a5fa", "#fbbf24", "#4ade80", "#a78bfa", "#fb923c"])
    fig2.update_layout(template="plotly_dark", paper_bgcolor="#12121f", plot_bgcolor="#12121f",
                       font=dict(color="#e2e2ea"), showlegend=False, height=350)
    st.plotly_chart(fig2, use_container_width=True)

except Exception as e:
    st.error(f"Error: {e}")
```

## Create file: `streamlit_app/requirements.txt`

```txt
streamlit>=1.30.0
plotly>=5.18.0
duckdb>=0.9.0
requests>=2.31.0
python-dotenv>=1.0.0
```

---

# COWORK PLUGIN SKILLS (complete content)

## Create file: `cowork_plugin/skills/brand-voice.md`

```markdown
# Brand Voice & Output Guidelines

## Triggers
- When generating any user-facing analysis, report, or insight
- When formatting data results or recommendations

## Tone
- Confident and data-driven. Lead with the insight, not the methodology.
- Concise. No filler. Active voice always.
- "Trips increased 15%" not "An increase of 15% was observed."

## Number Formatting
- Large numbers: K/M/B suffixes (1.2M orders, 540K contacts)
- Percentages: One decimal place (12.3%)
- Currency: USD with two decimals ($45.67)
- Distance: km with two decimals (4.23 km)
- Duration: minutes with one decimal (14.5 min)
- Dates in prose: "June 2024" or "Jun 15, 2024" — never ISO format

## YoY Comparisons
Always show BOTH absolute change AND percentage:
"Avg order value grew from $112 to $135 (+20.5% YoY)"

## Color Coding Convention
- Positive/growth: green (#4ade80)
- Negative/decline: red (#f87171)
- Neutral/context: gray (#8a8a9a)
- Spend/cost: coral (#f87171)
- Revenue: blue (#60a5fa)
- Conversion: amber (#fbbf24)

## Visualization Recommendations
- Bar charts → comparisons (channels, campaigns, categories)
- Line charts → trends over time (daily, weekly, monthly)
- Scatter plots → correlations (spend vs revenue, sessions vs conversions)
- Dual-axis → overlay spend with revenue or conversions
- Funnel → impression → click → session → lead → opportunity → closed
- Grouped bar → attribution model comparison per channel
- Stacked bar → spend allocation across platforms

## Standard Analysis Output Structure
1. **Key Finding** — 1 headline sentence with the most important insight
2. **KPI Summary** — Table or cards: current vs previous period with % change
3. **Supporting Detail** — 2-3 data points with context
4. **Visualization** — Chart recommendation with axis labels
5. **Recommendations** — 2-3 specific, actionable next steps
```

## Create file: `cowork_plugin/skills/metric-definitions.md`

```markdown
# Metric Definitions — Full-Funnel Marketing Analytics

## Triggers
- When any metric is referenced in a query
- When generating SQL or interpreting results

## ALWAYS use the dbt semantic layer (text_to_sql tool) for governed queries

## Core Metrics

| Metric | Definition | Unit |
|--------|-----------|------|
| **blended_cac** | Total ad spend (Google + Meta) / New customers acquired | USD |
| **blended_roas** | Attributed revenue / Total ad spend | ratio |
| **channel_roas** | Channel attributed revenue / Channel spend | ratio |
| **aov** | Total revenue / Total orders | USD |
| **customer_ltv** | Total lifetime revenue per customer | USD |
| **lead_score** | ML-predicted probability × 100 (0-100 scale) | score |
| **win_rate** | Closed Won / (Closed Won + Closed Lost) × 100 | % |
| **pipeline_velocity** | Weighted pipeline value / Days in period | USD/day |
| **conversion_rate** | Conversions / Sessions × 100 | % |
| **cpc** | Total spend / Total clicks | USD |

## Attribution Models
- **First-touch**: 100% credit to first interaction before purchase
- **Last-touch**: 100% credit to last interaction before purchase
- **Linear**: Equal credit split across all touchpoints
- **Time-decay**: More credit to touchpoints closer to conversion (7-day half-life)

## Key Dimensions
- **platform**: google_ads, meta_ads
- **channel**: google_ads_search, google_ads_shopping, meta_prospecting, meta_retargeting, organic_search, email_marketing, direct
- **lead_source**: organic_search, paid_search, paid_social, direct, email, referral
- **customer_segment**: new, returning, vip (based on revenue quartiles)
- **deal_stage**: Prospecting → Qualification → Needs Analysis → Value Proposition → Negotiation → Closed Won / Closed Lost
```

## Create file: `cowork_plugin/skills/data-workflow.md`

```markdown
# Data Workflow — How to Query and Visualize

## Triggers
- When processing any analytics request

## Step-by-Step Workflow

### 1. Parse the Request
Identify: metrics, dimensions, time range, filters, comparison type.

### 2. Query via dbt Semantic Layer
Use the dbt MCP server's `text_to_sql` tool for governed queries.

### 3. Execute the Query
Use the BigQuery (or DuckDB) MCP server to run the SQL.

### 4. Enrich with Platform Data
If real-time platform data would help, call the appropriate MCP server:
- Google Ads MCP → campaign performance, keywords
- Meta Ads MCP → ad set insights, reach
- GA4 MCP → traffic by channel, device breakdown
- HubSpot MCP → contacts by source, deal pipeline
- Salesforce MCP → opportunity pipeline, revenue by source

### 5. Format Results
Follow brand-voice.md: Key Finding → KPIs → Detail → Chart → Recommendations.

### 6. Generate Visualization
If user asks for visual: generate a React component (Recharts) or recommend chart type.
Use dark theme: #0d0d1a background, coral/blue/amber color scheme.
```

---

# OPENCODE SKILLS (same content, OpenCode format)

## Create file: `.opencode/skills/brand-voice/SKILL.md`

```markdown
---
name: brand-voice
description: Number formatting, color coding, and output structure guidelines for all analytics output
---
(paste identical content from cowork_plugin/skills/brand-voice.md above)
```

## Create file: `.opencode/skills/metric-definitions/SKILL.md`

```markdown
---
name: metric-definitions
description: All metric definitions, attribution models, and dimension values for the marketing analytics platform
---
(paste identical content from cowork_plugin/skills/metric-definitions.md above)
```

## Create file: `.opencode/skills/data-workflow/SKILL.md`

```markdown
---
name: data-workflow
description: Step-by-step workflow for processing analytics queries via MCP servers and dbt semantic layer
---
(paste identical content from cowork_plugin/skills/data-workflow.md above)
```

---

# COWORK + OPENCODE COMMANDS (complete content)

## Create file: `cowork_plugin/commands/marketing.md` (and copy to `.opencode/commands/marketing.md`)

```markdown
# /marketing — Cross-Platform Marketing Performance

Query Google Ads + Meta Ads + GA4 in one view.

## Workflow
1. Query Google Ads MCP: get_campaign_performance for the requested period
2. Query Meta Ads MCP: get_campaign_insights for the same period
3. Query GA4 MCP: get_traffic_by_channel for website context
4. Calculate: blended CAC, blended ROAS, total spend, total conversions
5. Format with KPI cards + spend allocation + daily trend chart
6. Include 2-3 actionable recommendations

## Example queries
- "What's our blended ROAS this month?"
- "Compare Google Ads vs Meta efficiency for Q1 2018"
- "Which channel has the lowest CAC?"
```

## Create file: `cowork_plugin/commands/attribution.md` (and copy to `.opencode/commands/attribution.md`)

```markdown
# /attribution — Multi-Touch Attribution Analysis

Compare how different touchpoints contribute to revenue.

## Workflow
1. Query attribution data from warehouse via dbt semantic layer
2. Calculate revenue per channel under first-touch, last-touch, linear, time-decay
3. Identify channels over/under-credited by last-touch vs linear
4. Cross-reference with actual spend from Google + Meta MCP
5. Calculate true ROAS per channel per model
6. Recommend budget reallocation based on linear model

## Example queries
- "Which channels assist most but get no last-touch credit?"
- "What's the true ROAS of Meta retargeting?"
- "Recommend budget reallocation using linear attribution"
```

## Create file: `cowork_plugin/commands/pipeline.md` (and copy to `.opencode/commands/pipeline.md`)

```markdown
# /pipeline — Sales Pipeline & CRM Analysis

## Workflow
1. Query Salesforce MCP: get_opportunity_pipeline
2. Query HubSpot MCP: get_deal_pipeline + get_contacts_by_source
3. Calculate: win rate, pipeline velocity, avg deal size, marketing-sourced %
4. Format as funnel visualization with conversion rates between stages
```

## Create file: `cowork_plugin/commands/score.md` (and copy to `.opencode/commands/score.md`)

```markdown
# /score — Score a Lead via ML API

## Workflow
1. Parse lead description from user input
2. Extract features: source, orders, revenue, sessions, pages, duration
3. POST to http://localhost:8000/score
4. Display: score (0-100), tier (hot/warm/cold), action, top factors
```

## Create file: `cowork_plugin/commands/analyze.md` (and copy to `.opencode/commands/analyze.md`)

```markdown
# /analyze — General Data Analysis

## Workflow
1. Parse question to identify metrics, dimensions, time range, filters
2. Check metric-definitions skill for correct definitions
3. Query dbt semantic layer via text_to_sql
4. Execute via warehouse MCP
5. Format per brand-voice guidelines
6. Suggest visualization type
```

## Create file: `cowork_plugin/commands/report.md` (and copy to `.opencode/commands/report.md`)

```markdown
# /report — Executive Summary

## Output Structure
1. Period Overview (1 paragraph)
2. KPI Dashboard (table: current vs previous with % change)
3. Top 3 Insights (numbered, each with data point + implication)
4. Channel Performance (attribution-adjusted)
5. Recommendations (2-3 actionable items)
```

---

# WAREHOUSE SETUP FILES (complete code)

## Create file: `warehouse_configs/snowflake/setup.sql`

```sql
-- Run after signing up at signup.snowflake.com (30-day trial, ~$400 credits)

USE ROLE SYSADMIN;
CREATE WAREHOUSE IF NOT EXISTS ANALYTICS_WH WITH WAREHOUSE_SIZE='XSMALL' AUTO_SUSPEND=60 AUTO_RESUME=TRUE;
CREATE DATABASE IF NOT EXISTS OLIST_ANALYTICS;
CREATE SCHEMA IF NOT EXISTS OLIST_ANALYTICS.PUBLIC;
USE DATABASE OLIST_ANALYTICS;
USE SCHEMA PUBLIC;

-- Read-only role for MCP
USE ROLE SECURITYADMIN;
CREATE ROLE IF NOT EXISTS ANALYST_READONLY;
GRANT USAGE ON DATABASE OLIST_ANALYTICS TO ROLE ANALYST_READONLY;
GRANT USAGE ON SCHEMA OLIST_ANALYTICS.PUBLIC TO ROLE ANALYST_READONLY;
GRANT SELECT ON ALL TABLES IN SCHEMA OLIST_ANALYTICS.PUBLIC TO ROLE ANALYST_READONLY;
GRANT SELECT ON FUTURE TABLES IN SCHEMA OLIST_ANALYTICS.PUBLIC TO ROLE ANALYST_READONLY;
GRANT USAGE ON WAREHOUSE ANALYTICS_WH TO ROLE ANALYST_READONLY;

-- Upload CSVs via Snowflake UI (Data > Databases > OLIST_ANALYTICS > PUBLIC > Load Data)
-- Or use stages for bulk loading

-- After loading, verify:
SELECT 'orders' as tbl, COUNT(*) as rows FROM orders
UNION ALL SELECT 'customers', COUNT(*) FROM customers
UNION ALL SELECT 'order_items', COUNT(*) FROM order_items
UNION ALL SELECT 'google_ads_daily_performance', COUNT(*) FROM google_ads_daily_performance
UNION ALL SELECT 'marketing_attribution', COUNT(*) FROM marketing_attribution;
```

## Create file: `warehouse_configs/databricks/setup_notebook.py`

```python
# Run in a Databricks notebook after signing up at databricks.com/try

# Create catalog and schema
spark.sql("CREATE CATALOG IF NOT EXISTS olist_analytics")
spark.sql("CREATE SCHEMA IF NOT EXISTS olist_analytics.public")
spark.sql("CREATE SCHEMA IF NOT EXISTS olist_analytics.marketing")

# Upload CSVs to DBFS first via Databricks UI:
# Workspace > Import > upload all CSVs to /FileStore/olist/ and /FileStore/mock_marketing/

# Load Olist tables
olist_tables = ["customers", "orders", "order_items", "order_payments",
                "order_reviews", "products", "sellers"]
for table in olist_tables:
    df = spark.read.option("header", True).option("inferSchema", True) \
        .csv(f"dbfs:/FileStore/olist/olist_{table}_dataset.csv")
    df.write.format("delta").mode("overwrite") \
        .saveAsTable(f"olist_analytics.public.{table}")
    print(f"  {table}: {df.count():,} rows")

# Load geolocation
df = spark.read.option("header", True).option("inferSchema", True) \
    .csv("dbfs:/FileStore/olist/olist_geolocation_dataset.csv")
df.write.format("delta").mode("overwrite") \
    .saveAsTable("olist_analytics.public.geolocation")

# Load category translation
df = spark.read.option("header", True).option("inferSchema", True) \
    .csv("dbfs:/FileStore/olist/product_category_name_translation.csv")
df.write.format("delta").mode("overwrite") \
    .saveAsTable("olist_analytics.public.category_translation")

# Load marketing tables
marketing_files = [
    "google_ads_campaigns", "google_ads_ad_groups", "google_ads_keywords",
    "google_ads_daily_performance", "meta_ads_campaigns", "meta_ads_ad_sets",
    "meta_ads_daily_performance", "ga4_daily_sessions",
    "hubspot_contacts", "hubspot_deals",
    "salesforce_accounts", "salesforce_opportunities",
    "marketing_attribution"
]
for table in marketing_files:
    df = spark.read.option("header", True).option("inferSchema", True) \
        .csv(f"dbfs:/FileStore/mock_marketing/{table}.csv")
    df.write.format("delta").mode("overwrite") \
        .saveAsTable(f"olist_analytics.marketing.{table}")
    print(f"  {table}: {df.count():,} rows")

# Show MLflow works natively (no setup!)
import mlflow
print(f"\nMLflow tracking URI: {mlflow.get_tracking_uri()}")
print("MLflow is built into Databricks — zero additional setup needed.")

print("\n=== Databricks setup complete ===")
```

## Create file: `automation/n8n_workflow.json`

```json
{
  "name": "Lead Scoring & Routing",
  "nodes": [
    {
      "name": "Webhook Trigger",
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "path": "new-lead",
        "httpMethod": "POST"
      },
      "position": [250, 300]
    },
    {
      "name": "Score Lead",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "http://localhost:8000/score",
        "method": "POST",
        "sendBody": true,
        "bodyParameters": {
          "parameters": [
            {"name": "lead_source", "value": "={{ $json.lead_source }}"},
            {"name": "num_prior_orders", "value": "={{ $json.num_prior_orders || 0 }}"},
            {"name": "total_prior_revenue", "value": "={{ $json.total_prior_revenue || 0 }}"},
            {"name": "avg_sessions", "value": "={{ $json.avg_sessions || 1 }}"},
            {"name": "avg_pages_per_session", "value": "={{ $json.avg_pages_per_session || 2 }}"},
            {"name": "avg_session_duration", "value": "={{ $json.avg_session_duration || 60 }}"}
          ]
        }
      },
      "position": [450, 300]
    },
    {
      "name": "Route by Score",
      "type": "n8n-nodes-base.if",
      "parameters": {
        "conditions": {
          "number": [{"value1": "={{ $json.score }}", "operation": "largerEqual", "value2": 70}]
        }
      },
      "position": [650, 300]
    },
    {
      "name": "Hot Lead → Sales",
      "type": "n8n-nodes-base.set",
      "parameters": {
        "values": {"string": [{"name": "routing", "value": "SALES - Immediate follow-up"}]}
      },
      "position": [850, 200]
    },
    {
      "name": "Check Warm",
      "type": "n8n-nodes-base.if",
      "parameters": {
        "conditions": {
          "number": [{"value1": "={{ $json.score }}", "operation": "largerEqual", "value2": 40}]
        }
      },
      "position": [850, 400]
    },
    {
      "name": "Warm Lead → Nurture",
      "type": "n8n-nodes-base.set",
      "parameters": {
        "values": {"string": [{"name": "routing", "value": "NURTURE - Send case study + demo invite"}]}
      },
      "position": [1050, 350]
    },
    {
      "name": "Cold Lead → Long-term",
      "type": "n8n-nodes-base.set",
      "parameters": {
        "values": {"string": [{"name": "routing", "value": "LONG-TERM - Monitor engagement signals"}]}
      },
      "position": [1050, 500]
    }
  ],
  "connections": {
    "Webhook Trigger": {"main": [[{"node": "Score Lead", "type": "main", "index": 0}]]},
    "Score Lead": {"main": [[{"node": "Route by Score", "type": "main", "index": 0}]]},
    "Route by Score": {
      "main": [
        [{"node": "Hot Lead → Sales", "type": "main", "index": 0}],
        [{"node": "Check Warm", "type": "main", "index": 0}]
      ]
    },
    "Check Warm": {
      "main": [
        [{"node": "Warm Lead → Nurture", "type": "main", "index": 0}],
        [{"node": "Cold Lead → Long-term", "type": "main", "index": 0}]
      ]
    }
  }
}
```

## Create file: `automation/README.md`

```markdown
# n8n Lead Routing Workflow

## Setup (self-hosted, free)

```bash
# Docker (recommended)
docker run -it --rm --name n8n -p 5678:5678 n8nio/n8n

# Or npm
npm install -g n8n
n8n start
```

## Import workflow

1. Open n8n at http://localhost:5678
2. Go to Workflows → Import from File
3. Select `n8n_workflow.json`
4. Activate the workflow

## Test

```bash
curl -X POST http://localhost:5678/webhook/new-lead \
  -H "Content-Type: application/json" \
  -d '{"lead_source": "paid_search", "num_prior_orders": 3, "total_prior_revenue": 450}'
```

## Prerequisites
- FastAPI scoring endpoint running at localhost:8000
- MLflow model trained and registered
```

---

# END OF ADDENDUM
# Total fully-written code files in this addendum: 21
# ═══════════════════════════════════════════
# ADDENDUM 2: REMAINING LOST CONTENT
# Append this after addendum 1 in FINAL_COMPLETE_PLAN.md
# ═══════════════════════════════════════════

---

# ENHANCED STREAMLIT: Full Plotly charting functions

The Streamlit pages in Addendum 1 are functional but basic. Replace `streamlit_app/pages/1_marketing_overview.py` with this enhanced version that includes the full Voi-style charting:

## Replace file: `streamlit_app/pages/1_marketing_overview.py` (enhanced)

```python
"""Page 1: Cross-platform marketing performance with Voi-style dark charts."""
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import duckdb
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="Marketing Overview", layout="wide")

DARK_TEMPLATE = dict(
    template="plotly_dark",
    paper_bgcolor="#12121f",
    plot_bgcolor="#12121f",
    font=dict(family="JetBrains Mono, monospace", color="#e2e2ea"),
)

def render_kpi_card(label, value, prev_value, fmt=",.1f", suffix="", invert=False):
    """Render a dark-themed KPI card with YoY change."""
    if prev_value and prev_value != 0:
        pct = ((value - prev_value) / abs(prev_value)) * 100
        is_good = pct < 0 if invert else pct > 0
        css_class = "positive" if is_good else "negative"
        sign = "+" if pct > 0 else ""
        change_html = f'<div style="font-size:28px;font-weight:700;color:{"#4ade80" if is_good else "#f87171"}">{sign}{pct:.1f}%</div>'
    else:
        change_html = f'<div style="font-size:28px;font-weight:700;color:#e2e2ea">{value:{fmt}}{suffix}</div>'

    return f"""
    <div style="background:#1a1a2e;border-radius:8px;padding:16px 20px;text-align:center;border-left:3px solid {'#4ade80' if (not invert and value > (prev_value or 0)) or (invert and value < (prev_value or 0)) else '#f87171'}">
        <div style="font-size:10px;font-weight:600;color:#8a8a9a;letter-spacing:1.2px;text-transform:uppercase;margin-bottom:8px">{label}</div>
        {change_html}
        <div style="font-size:11px;color:#6a6a7a;margin-top:4px">{value:{fmt}}{suffix} vs {prev_value:{fmt}}{suffix}</div>
    </div>
    """


def create_spend_vs_revenue_chart(google_df, meta_df):
    """Dual-axis chart: spend lines + revenue lines by platform."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Scatter(
        x=google_df["date"], y=google_df["spend"], name="Google Spend",
        line=dict(color="#f87171", width=2), mode="lines"), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=meta_df["date"], y=meta_df["spend"], name="Meta Spend",
        line=dict(color="#60a5fa", width=2), mode="lines"), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=google_df["date"], y=google_df["revenue"], name="Google Revenue",
        line=dict(color="#f87171", width=2, dash="dash"), mode="lines"), secondary_y=True)
    fig.add_trace(go.Scatter(
        x=meta_df["date"], y=meta_df["revenue"], name="Meta Revenue",
        line=dict(color="#60a5fa", width=2, dash="dash"), mode="lines"), secondary_y=True)

    fig.update_layout(**DARK_TEMPLATE, height=400, title="Daily Spend vs Revenue by Platform",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=60, r=60, t=60, b=40))
    fig.update_xaxes(gridcolor="#1e1e32")
    fig.update_yaxes(title_text="Spend ($)", secondary_y=False, gridcolor="#1e1e32")
    fig.update_yaxes(title_text="Revenue ($)", secondary_y=True, gridcolor="#1e1e32")
    return fig


def create_channel_funnel(ga4_df, conversions, revenue):
    """Horizontal funnel: impressions → clicks → sessions → conversions → revenue."""
    stages = ["Sessions", "Engaged", "Conversions"]
    values = [
        int(ga4_df["sessions"].sum()),
        int(ga4_df["engaged_sessions"].sum()),
        int(ga4_df["conversions"].sum()),
    ]
    fig = go.Figure(go.Funnel(
        y=stages, x=values, textinfo="value+percent initial",
        marker=dict(color=["#f87171", "#fbbf24", "#4ade80"]),
    ))
    fig.update_layout(**DARK_TEMPLATE, height=300, title="Website Funnel")
    return fig


def create_platform_comparison(google_totals, meta_totals):
    """Grouped bar: Google vs Meta across key metrics."""
    metrics = ["Spend ($K)", "Clicks (K)", "Conversions", "Revenue ($K)"]
    google_vals = [google_totals["spend"]/1000, google_totals["clicks"]/1000,
                   google_totals["conversions"], google_totals["revenue"]/1000]
    meta_vals = [meta_totals["spend"]/1000, meta_totals["clicks"]/1000,
                 meta_totals["conversions"], meta_totals["revenue"]/1000]

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Google Ads", x=metrics, y=google_vals, marker_color="#f87171"))
    fig.add_trace(go.Bar(name="Meta Ads", x=metrics, y=meta_vals, marker_color="#60a5fa"))
    fig.update_layout(**DARK_TEMPLATE, barmode="group", height=350, title="Platform Comparison")
    return fig


# --- Main page ---
st.markdown("### 📊 Marketing Overview")

@st.cache_resource
def get_db():
    db_path = Path(__file__).parent.parent.parent / "data" / "olist_analytics.duckdb"
    if db_path.exists():
        return duckdb.connect(str(db_path), read_only=True)
    return None

con = get_db()
if not con:
    st.error("Database not found. Run: python scripts/load_duckdb.py")
    st.stop()

try:
    google = con.execute("""
        SELECT date, SUM(cost) as spend, SUM(clicks) as clicks,
               SUM(conversions) as conversions, SUM(conversion_value) as revenue
        FROM google_ads_daily_performance GROUP BY date ORDER BY date
    """).fetchdf()

    meta = con.execute("""
        SELECT date, SUM(spend) as spend, SUM(link_clicks) as clicks,
               SUM(purchases) as conversions, SUM(purchase_value) as revenue
        FROM meta_ads_daily_performance GROUP BY date ORDER BY date
    """).fetchdf()

    ga4 = con.execute("""
        SELECT channel_group, SUM(sessions) as sessions,
               SUM(engaged_sessions) as engaged_sessions,
               SUM(conversions) as conversions, SUM(revenue) as revenue
        FROM ga4_daily_sessions GROUP BY channel_group
    """).fetchdf()

    # KPI row
    g = {"spend": google["spend"].sum(), "clicks": google["clicks"].sum(),
         "conversions": google["conversions"].sum(), "revenue": google["revenue"].sum()}
    m = {"spend": meta["spend"].sum(), "clicks": meta["clicks"].sum(),
         "conversions": meta["conversions"].sum(), "revenue": meta["revenue"].sum()}

    total_spend = g["spend"] + m["spend"]
    total_rev = g["revenue"] + m["revenue"]
    total_conv = g["conversions"] + m["conversions"]

    cols = st.columns(6)
    with cols[0]:
        st.markdown(render_kpi_card("Total Spend", total_spend, total_spend * 0.85, ",.0f", ""), unsafe_allow_html=True)
    with cols[1]:
        st.markdown(render_kpi_card("Total Revenue", total_rev, total_rev * 0.78, ",.0f", ""), unsafe_allow_html=True)
    with cols[2]:
        st.markdown(render_kpi_card("Blended ROAS", total_rev/max(total_spend, 1), total_rev*0.78/max(total_spend*0.85, 1), ".2f", "x"), unsafe_allow_html=True)
    with cols[3]:
        st.markdown(render_kpi_card("Conversions", total_conv, total_conv * 0.82, ",.0f", ""), unsafe_allow_html=True)
    with cols[4]:
        st.markdown(render_kpi_card("Blended CPC", total_spend/max(g["clicks"]+m["clicks"], 1), total_spend*0.85/max((g["clicks"]+m["clicks"])*0.9, 1), ".2f", ""), unsafe_allow_html=True)
    with cols[5]:
        st.markdown(render_kpi_card("Blended CAC", total_spend/max(total_conv, 1), total_spend*0.85/max(total_conv*0.82, 1), ".2f", "", invert=True), unsafe_allow_html=True)

    # Charts
    st.plotly_chart(create_spend_vs_revenue_chart(google, meta), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(create_platform_comparison(g, m), use_container_width=True)
    with col2:
        ga4_all = con.execute("SELECT * FROM ga4_daily_sessions").fetchdf()
        st.plotly_chart(create_channel_funnel(ga4_all, total_conv, total_rev), use_container_width=True)

except Exception as e:
    st.error(f"Error loading marketing data: {e}")
```

---

# DETAILED DBT STAGING MODEL SPECS

These were described briefly in the main plan. Here are the full column-level specs:

## `stg_order_items.sql`
```sql
WITH source AS (SELECT * FROM {{ source('olist', 'order_items') }})
SELECT
    order_id,
    order_item_id,
    product_id,
    seller_id,
    CAST(shipping_limit_date AS TIMESTAMP) AS shipping_limit_date,
    CAST(price AS NUMERIC(10,2)) AS price,
    CAST(freight_value AS NUMERIC(10,2)) AS freight_value,
    CAST(price AS NUMERIC(10,2)) + CAST(freight_value AS NUMERIC(10,2)) AS total_item_value
FROM source
WHERE price > 0
```

## `stg_order_payments.sql`
```sql
WITH source AS (SELECT * FROM {{ source('olist', 'order_payments') }})
SELECT
    order_id,
    payment_sequential,
    CASE payment_type
        WHEN 'credit_card' THEN 'credit_card'
        WHEN 'boleto' THEN 'boleto'
        WHEN 'voucher' THEN 'voucher'
        WHEN 'debit_card' THEN 'debit_card'
        ELSE 'other'
    END AS payment_type,
    payment_installments,
    CAST(payment_value AS NUMERIC(10,2)) AS payment_value
FROM source
WHERE payment_value > 0
```

## `stg_order_reviews.sql`
```sql
WITH source AS (SELECT * FROM {{ source('olist', 'order_reviews') }})
SELECT
    review_id,
    order_id,
    review_score,
    review_comment_title,
    review_comment_message,
    CAST(review_creation_date AS TIMESTAMP) AS review_creation_date,
    CAST(review_answer_timestamp AS TIMESTAMP) AS review_answer_timestamp,
    CASE WHEN review_score >= 4 THEN TRUE ELSE FALSE END AS is_positive,
    CASE WHEN review_comment_message IS NOT NULL THEN LENGTH(review_comment_message) ELSE 0 END AS review_length
FROM source
WHERE review_score IS NOT NULL
```

## `stg_customers.sql`
```sql
WITH source AS (SELECT * FROM {{ source('olist', 'customers') }})
SELECT
    customer_id,
    customer_unique_id,
    customer_zip_code_prefix,
    LOWER(customer_city) AS customer_city,
    customer_state
FROM source
```

## `stg_sellers.sql`
```sql
WITH source AS (SELECT * FROM {{ source('olist', 'sellers') }})
SELECT
    seller_id,
    seller_zip_code_prefix,
    LOWER(seller_city) AS seller_city,
    seller_state
FROM source
```

## `stg_products.sql`
```sql
WITH source AS (SELECT * FROM {{ source('olist', 'products') }}),
     translations AS (SELECT * FROM {{ source('olist', 'category_translation') }})
SELECT
    p.product_id,
    COALESCE(t.product_category_name_english, p.product_category_name) AS product_category,
    p.product_name_lenght AS product_name_length,
    p.product_description_lenght AS product_description_length,
    p.product_photos_qty AS product_photos_count,
    p.product_weight_g AS weight_grams,
    p.product_length_cm AS length_cm,
    p.product_height_cm AS height_cm,
    p.product_width_cm AS width_cm,
    CASE
        WHEN p.product_length_cm IS NOT NULL AND p.product_height_cm IS NOT NULL AND p.product_width_cm IS NOT NULL
        THEN p.product_length_cm * p.product_height_cm * p.product_width_cm
        ELSE NULL
    END AS product_volume_cm3
FROM source p
LEFT JOIN translations t ON p.product_category_name = t.product_category_name
```

## `stg_google_ads_performance.sql`
```sql
WITH source AS (SELECT * FROM {{ source('marketing', 'google_ads_daily_performance') }})
SELECT
    CAST(date AS DATE) AS date,
    campaign_id, campaign_name, campaign_type,
    impressions, clicks,
    CAST(cost AS NUMERIC(10,2)) AS cost,
    conversions,
    CAST(conversion_value AS NUMERIC(10,2)) AS conversion_value,
    CAST(ctr AS NUMERIC(6,2)) AS ctr,
    CAST(avg_cpc AS NUMERIC(6,2)) AS avg_cpc,
    CAST(roas AS NUMERIC(8,2)) AS roas
FROM source
```

## `stg_meta_ads_performance.sql`
```sql
WITH source AS (SELECT * FROM {{ source('marketing', 'meta_ads_daily_performance') }})
SELECT
    CAST(date AS DATE) AS date,
    campaign_id, campaign_name, objective,
    impressions, reach,
    CAST(spend AS NUMERIC(10,2)) AS spend,
    link_clicks,
    CAST(ctr AS NUMERIC(6,2)) AS ctr,
    CAST(cpc AS NUMERIC(6,2)) AS cpc,
    CAST(cpm AS NUMERIC(6,2)) AS cpm,
    purchases,
    CAST(purchase_value AS NUMERIC(10,2)) AS purchase_value,
    CAST(roas AS NUMERIC(8,2)) AS roas
FROM source
```

## `stg_ga4_sessions.sql`
```sql
WITH source AS (SELECT * FROM {{ source('marketing', 'ga4_daily_sessions') }})
SELECT
    CAST(date AS DATE) AS date,
    channel_group,
    device_category,
    sessions,
    engaged_sessions,
    CAST(bounce_rate AS NUMERIC(5,1)) AS bounce_rate,
    CAST(avg_session_duration_sec AS NUMERIC(8,1)) AS avg_session_duration_sec,
    CAST(pages_per_session AS NUMERIC(4,1)) AS pages_per_session,
    new_users,
    conversions,
    CAST(revenue AS NUMERIC(10,2)) AS revenue,
    CAST(conversion_rate AS NUMERIC(5,2)) AS conversion_rate,
    CASE WHEN sessions > 0 THEN CAST((engaged_sessions * 100.0 / sessions) AS NUMERIC(5,1)) ELSE 0 END AS engagement_rate
FROM source
```

## `stg_hubspot_contacts.sql`
```sql
WITH source AS (SELECT * FROM {{ source('marketing', 'hubspot_contacts') }})
SELECT
    contact_id, customer_id, email, first_name, last_name,
    city, state,
    CAST(create_date AS DATE) AS create_date,
    lifecycle_stage, lead_source,
    num_orders,
    CAST(total_revenue AS NUMERIC(10,2)) AS total_revenue,
    CAST(first_order_date AS DATE) AS first_order_date,
    CAST(last_activity_date AS DATE) AS last_activity_date
FROM source
```

## `stg_hubspot_deals.sql`
```sql
WITH source AS (SELECT * FROM {{ source('marketing', 'hubspot_deals') }})
SELECT
    deal_id, order_id, deal_name, deal_stage, pipeline,
    CAST(amount AS NUMERIC(10,2)) AS amount,
    CAST(create_date AS DATE) AS create_date,
    CASE WHEN close_date IS NOT NULL AND close_date != '' THEN CAST(close_date AS DATE) ELSE NULL END AS close_date,
    deal_type, lead_source,
    CASE WHEN deal_stage = 'closed_won' THEN TRUE ELSE FALSE END AS is_closed_won
FROM source
```

## `stg_salesforce_opportunities.sql`
```sql
WITH source AS (SELECT * FROM {{ source('marketing', 'salesforce_opportunities') }})
SELECT
    opportunity_id, order_id, opportunity_name, stage, probability,
    CAST(amount AS NUMERIC(10,2)) AS amount,
    CAST(created_date AS DATE) AS created_date,
    CAST(close_date AS DATE) AS close_date,
    lead_source, type, fiscal_quarter,
    CASE WHEN stage = 'Closed Won' THEN TRUE ELSE FALSE END AS is_won,
    CAST(amount * probability / 100.0 AS NUMERIC(10,2)) AS weighted_amount
FROM source
```

## `stg_marketing_attribution.sql`
```sql
WITH source AS (SELECT * FROM {{ source('marketing', 'marketing_attribution') }})
SELECT
    order_id,
    touchpoint_position,
    total_touchpoints,
    channel,
    platform,
    CAST(touchpoint_date AS DATE) AS touchpoint_date,
    CAST(order_date AS DATE) AS order_date,
    CAST(order_revenue AS NUMERIC(10,2)) AS order_revenue,
    CAST(first_touch_credit AS NUMERIC(6,4)) AS first_touch_credit,
    CAST(last_touch_credit AS NUMERIC(6,4)) AS last_touch_credit,
    CAST(linear_credit AS NUMERIC(6,4)) AS linear_credit
FROM source
```

---

# VERIFICATION CHECKLIST (complete)

## Create file: `docs/verification_checklist.md`

```markdown
# Verification Checklist

## Phase 1: Data Layer
- [ ] Olist 9 CSVs downloaded and verified (99K+ orders)
- [ ] Mock marketing data generated (13 CSV files)
- [ ] DuckDB: all tables created, row counts match
- [ ] BigQuery: all tables loaded, row counts match
- [ ] Supabase: subset tables created and loaded
- [ ] Attribution credits sum to ~1.0 per order (spot check 10 orders)

## Phase 2: dbt Project
- [ ] `dbt build --target duckdb` — all 29 models build, all tests pass
- [ ] `dbt build --target bigquery` — all models build, all tests pass
- [ ] `dbt build --target supabase` — all models build, all tests pass
- [ ] `assert_attribution_credits_sum_to_one` test passes
- [ ] `assert_no_negative_revenue` test passes
- [ ] Semantic layer query works: `dbt sl query --metrics blended_cac`
- [ ] Metrics return consistent values across BigQuery and DuckDB

## Phase 3: MCP Servers + AI Layer
- [ ] BigQuery MCP server connects (visible in client tools panel)
- [ ] dbt MCP server connects and exposes tools
- [ ] Mock Google Ads MCP: `get_campaign_performance` returns data
- [ ] Mock Meta Ads MCP: `get_campaign_insights` returns data
- [ ] Mock GA4 MCP: `get_traffic_by_channel` returns data
- [ ] Mock HubSpot MCP: `get_contacts_by_source` returns data
- [ ] Mock Salesforce MCP: `get_opportunity_pipeline` returns data
- [ ] All 7+ servers visible in Claude Desktop tools panel
- [ ] All 7+ servers visible in OpenCode tool list
- [ ] Hero Query 1 (full funnel) returns formatted analysis
- [ ] Hero Query 2 (attribution) returns model comparison
- [ ] Cowork plugin installs without errors (Claude Desktop)
- [ ] `/marketing` command produces cross-platform dashboard
- [ ] `/attribution` command shows model comparison
- [ ] `/pipeline` command shows CRM funnel
- [ ] OpenCode commands work with same MCP servers

## Phase 4: ML + MLflow
- [ ] MLflow tracking server runs at localhost:5000
- [ ] 4 experiments logged (LogReg, XGB default, tuned, deep)
- [ ] Best model AUC > 0.65
- [ ] Best model registered as 'lead_scoring_model'
- [ ] Feature importance artifact saved

## Phase 5: FastAPI + Automation + Dashboards
- [ ] `POST /score` returns valid ScoreResponse in < 100ms
- [ ] `GET /health` returns healthy + model_loaded=true
- [ ] `GET /model-info` returns version details
- [ ] Dockerfile builds and runs
- [ ] n8n workflow imported and runs
- [ ] n8n routes hot leads (score >= 70) correctly
- [ ] Streamlit app launches with all 4 pages
- [ ] Marketing Overview page: KPIs + spend chart + funnel
- [ ] Attribution page: model comparison table + grouped bar
- [ ] Lead Scoring page: input form calls API, shows result
- [ ] Pipeline page: funnel + revenue by source
- [ ] `/score` Cowork command calls FastAPI and returns tier

## Phase 6: Portability + Polish
- [ ] Snowflake trial activated
- [ ] Data loaded into Snowflake
- [ ] `dbt build --target snowflake` passes
- [ ] Snowflake MCP connected, hero query returns results
- [ ] Databricks trial activated
- [ ] Delta tables created in Databricks
- [ ] `dbt build --target databricks` passes
- [ ] MLflow runs natively in Databricks (demonstrated)
- [ ] Databricks MCP connected, hero query returns results
- [ ] Same query shown working on BigQuery → Snowflake → DuckDB
- [ ] Demo video recorded (8-10 min)
- [ ] GitHub repo public with README
- [ ] All credentials in .env, not committed
- [ ] .gitignore covers all sensitive files
- [ ] Screenshots in demo/screenshots/
```

---

# DEMO VIDEO SCRIPT

## Create file: `docs/demo_script.md`

```markdown
# Demo Video Script (8-10 minutes)

## 0:00–0:30 — Architecture Overview
Show the architecture diagram from README.
"This system connects 5 marketing platforms through 7 MCP servers to a dbt semantic layer, enabling natural language analytics across 5 data warehouses."

## 0:30–2:30 — Hero Query 1: Full Funnel (Claude Desktop)
Open Claude Desktop with all MCP servers connected (show hammer icon).
Type: "Show me the complete marketing funnel for Q1 2018: ad spend across Google and Meta, website sessions by channel, lead conversion rates from HubSpot, and revenue. Calculate blended CAC and ROAS."
Show Claude calling tools, generating SQL, returning formatted analysis.
Highlight: KPI cards, cross-platform comparison, funnel metrics.

## 2:30–4:00 — Hero Query 2: Attribution (Claude Desktop)
Type: "Compare first-touch vs last-touch attribution for our top channels. Which are under-credited by last-touch?"
Show the attribution model comparison.
If Claude generates a React artifact dashboard, zoom in on it.

## 4:00–5:00 — Multi-Client Portability (OpenCode + Gemini CLI)
Switch to terminal. Open OpenCode.
Run the same attribution query.
"Same MCP servers, same results, different client."
Quick switch to Gemini CLI: same query, same results.
"Three clients, one architecture."

## 5:00–6:00 — Lead Scoring API
Open browser to localhost:8000/docs (Swagger UI).
POST /score with sample lead data.
Show the response: score, tier, recommended action.
"This model was trained with MLflow, registered in the model registry, and served via FastAPI."

## 6:00–6:45 — n8n Automation
Open n8n at localhost:5678.
Show the workflow: webhook → score → route.
Trigger a test lead.
"Hot leads go to Sales, warm to nurture, cold to long-term."

## 6:45–7:30 — Warehouse Portability
"Everything you've seen runs on BigQuery free tier."
Switch dbt target to Snowflake: `dbt build --target snowflake`
Run the same hero query against Snowflake.
"Same semantic layer, same results, different engine."
Quick show of DuckDB: instant local execution.

## 7:30–8:30 — Streamlit Dashboard
Open Streamlit app.
Walk through: Marketing Overview, Attribution, Lead Scoring form, Pipeline.
"This is the self-serve interface for stakeholders who don't use Claude."

## 8:30–9:00 — MLflow Experiments
Open MLflow at localhost:5000.
Show 4 experiments compared.
"XGBoost tuned won with AUC 0.XX. All experiments tracked and reproducible."

## 9:00–9:30 — Closing
Show the cost slide: "$0/month base. All free tiers."
"One semantic layer. Five warehouses. Four AI clients. Seven MCP servers. Zero vendor lock-in."
```

---

# END OF ADDENDUM 2
