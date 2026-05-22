# 📥 Data Import Guide

How to bring your own data into the platform — from Excel files, CSVs, or a live
warehouse — and have it appear instantly in Claude dashboards, the Streamlit app,
and the dbt golden layer.

---

## What Data Lives Where (and What Goes in Git)

This project has three distinct data layers. Understanding them prevents confusion about
what to commit, what to download, and what gets rebuilt automatically.

| Layer | Location | In git? | Size | How it's created |
|-------|----------|---------|------|-----------------|
| **Olist raw dataset** | `data/olist/*.csv` | ❌ Never | ~400MB | `python scripts/download_olist_data.py` (once, locally) |
| **Mock marketing CSVs** | `data/mock_marketing/*.csv` | ✅ Yes | ~5–15MB | Generated once; CI uses `--standalone` to recreate without Olist |
| **DuckDB warehouse** | `data/olist_analytics.duckdb` | ❌ Never | ~50–200MB | Built locally: `load_duckdb.py` + `dbt run` |
| **Golden metrics snapshot** | `dashboards/golden_metrics.json` | ✅ Yes | ~50KB | `generate_golden_metrics.py`; CI commits it automatically |

**Rules of thumb:**
- Never commit anything in `data/olist/` or `*.duckdb` — they're too large and are always reproducible.
- The mock marketing CSVs **are** committed — they're the seed data every contributor needs without running a download.
- `golden_metrics.json` **is** committed — it's how Claude and the HTML dashboards read pre-computed metrics without a live DB connection.

---

## How to Update Your Local Database

The DuckDB file lives only on your machine. After pulling new commits (e.g., after the
daily CI appends new synthetic data), you need to rebuild it:

```bash
# 1. Pull the latest mock CSVs and golden_metrics.json that CI committed
git pull

# 2. Rebuild the local DuckDB from the updated CSVs
python scripts/load_duckdb.py

# 3. Re-run dbt to rebuild mart tables
cd dbt_project && dbt run --target duckdb && cd ..

# 4. (Optional) Verify zero drift — should exit 0 if you just pulled CI-generated data
python scripts/validate_metrics.py
```

After step 1 alone, **Claude dashboards** already show updated data because CI
committed the new `golden_metrics.json`. Steps 2–3 are only needed for
**Streamlit** or any tool that queries DuckDB directly.

---

## This Project vs. a Real Production Pipeline

This project is a portfolio demo that mimics a production data stack with lightweight
substitutes. Here is the mapping:

```
DEMO (this project)                    PRODUCTION (real company)
─────────────────────────────────────  ─────────────────────────────────────────────
data/olist/*.csv                  ←→   Raw tables already in BigQuery / Snowflake
  downloaded once, never in git         populated by Fivetran, Airbyte, or custom ETL

data/mock_marketing/*.csv         ←→   Real platform data in the warehouse
  hand-crafted synthetic seed data      loaded by Google Ads / Meta / GA4 connectors
  committed to git (small)              no CSV files needed — data goes straight to DW

data/olist_analytics.duckdb       ←→   The production warehouse itself
  local file, rebuilt from CSVs         BigQuery / Snowflake — cloud-managed, always live

daily_synthetic_append.py         ←→   Fivetran / Airbyte daily syncs
  GitHub Action adds rows to CSVs       appends real platform data to the warehouse
  commits them, simulating a live feed  fully automatic, no code to maintain

generate_golden_metrics.py        ←→   dbt Cloud job / Airflow DAG
  reads DuckDB → writes JSON            reads warehouse → BI tool reads it directly

golden_metrics.json in git        ←→   BI tool queries the warehouse live
  lets Claude read pre-computed values  (Looker, Tableau connect to DW directly)
  avoids needing a live DB in CI        no JSON file needed in production
```

**The core pattern never changes:**

```
Raw data source (warehouse or CSV)
  → dbt transforms it into clean mart tables
  → AI / BI layer reads the results
```

What changes between demo and production is only:
1. Where raw data comes from (Fivetran vs. local CSVs)
2. Who reads the results (Looker vs. Claude via a JSON snapshot)

---

## How Data Flows into Dashboards

Understanding this chain makes every import step obvious:

```
Your data (Excel / CSV / warehouse)
  ↓  import
data/mock_marketing/*.csv   (or warehouse tables directly)
  ↓  python scripts/load_duckdb.py
data/olist_analytics.duckdb
  ↓  dbt run
mart tables: fct_marketing_daily, stg_marketing_attribution, ...
  ↓  python scripts/generate_golden_metrics.py
dashboards/golden_metrics.json   ← single source of truth
  ↓  read by
HTML dashboards + Claude skills + Streamlit app
```

Every step is deterministic: once `golden_metrics.json` is regenerated after your
import, every dashboard — including Claude's — will show your numbers exactly.

---

## Method 1 — Streamlit Data Sources UI (easiest)

1. Start the app:
   ```bash
   streamlit run streamlit_app/app.py
   ```

2. Click **Data Sources** in the sidebar.

3. **File Upload tab** — drag and drop any CSV or Excel file.
   - The app shows a 20-row preview.
   - Choose which table to replace from the dropdown (e.g. `google_ads_daily_performance`).
   - Click **Save to mock data** → the file is written to `data/mock_marketing/`.

4. Return to your terminal and rebuild:
   ```bash
   python scripts/load_duckdb.py
   cd dbt_project && dbt run --target duckdb && cd ..
   python scripts/generate_golden_metrics.py
   ```

5. Reload any dashboard — your data is live.

---

## Method 2 — Direct CSV replacement (command line)

Drop your file into `data/mock_marketing/` with the correct name:

| Table | File name | Required columns (minimum) |
|-------|-----------|---------------------------|
| Google Ads daily | `google_ads_daily_performance.csv` | `date`, `campaign_id`, `campaign_name`, `impressions`, `clicks`, `cost`, `conversions` |
| Meta Ads daily | `meta_ads_daily_performance.csv` | `date`, `campaign_id`, `campaign_name`, `impressions`, `spend`, `link_clicks`, `purchases` |
| GA4 sessions | `ga4_daily_sessions.csv` | `date`, `channel_group`, `device_category`, `sessions`, `engaged_sessions`, `conversions` |
| HubSpot contacts | `hubspot_contacts.csv` | `contact_id`, `create_date`, `lifecycle_stage`, `lead_source` |
| HubSpot deals | `hubspot_deals.csv` | `deal_id`, `deal_stage`, `amount`, `create_date`, `lead_source` |
| Salesforce opps | `salesforce_opportunities.csv` | `opportunity_id`, `stage`, `amount`, `created_date`, `is_won`, `lead_source` |

Then rebuild:

```bash
python scripts/load_duckdb.py
cd dbt_project
dbt run --target duckdb
dbt test --target duckdb    # optional but recommended
cd ..
python scripts/generate_golden_metrics.py
python scripts/validate_metrics.py   # confirms no drift
```

---

## Method 3 — Connect a live warehouse

If your real data already lives in BigQuery or Snowflake, you can point dbt directly
at it and bypass the CSV layer entirely.

### BigQuery

```bash
# 1. Authenticate locally
gcloud auth application-default login

# 2. Edit dbt_project/profiles.yml (copy from profiles.yml.example first)
#    Set GCP_PROJECT_ID to your project and dataset to your schema

# 3. Run dbt against your live tables
dbt run --target bigquery

# 4. Generate golden metrics from BigQuery
python scripts/generate_golden_metrics.py --target bigquery

# 5. Validate
python scripts/validate_metrics.py --target bigquery
```

### Snowflake

```bash
# 1. Set env vars (or fill profiles.yml)
export SNOWFLAKE_ACCOUNT=xy12345.us-east-1
export SNOWFLAKE_USER=myuser
export SNOWFLAKE_PASSWORD=mypassword
export SNOWFLAKE_WAREHOUSE=ANALYTICS_WH
export SNOWFLAKE_DATABASE=OLIST_ANALYTICS
export SNOWFLAKE_SCHEMA=PUBLIC

# 2. Run dbt
dbt run --target snowflake

# 3. Generate + validate
python scripts/generate_golden_metrics.py --target snowflake
python scripts/validate_metrics.py --target snowflake
```

Once `golden_metrics.json` is regenerated from your live warehouse, all dashboards
automatically reflect your production data.

---

## Seeing Your Data in Claude

After any import, Claude reads the updated `golden_metrics.json` when you use the
project skills. Here is what each skill shows and what data it reads:

| Skill | What it shows | Data source in golden_metrics.json |
|-------|--------------|-------------------------------------|
| `/marketing` | Full funnel: spend, ROAS, sessions, pipeline | `windowed_90d` — all sections |
| `/attribution` | Revenue by channel (first/last/linear) | `windowed_90d.attribution_by_channel` |
| `/campaign` | Google + Meta campaign performance | `windowed_90d.campaigns` |
| `/traffic` | GA4 sessions by channel, CVR | `windowed_90d.ga4_by_channel` |
| `/pipeline` | CRM pipeline, win rates | `all_time.crm` |

### Step-by-step: import data → see it in Claude

1. Import your file (any method above)
2. Run the rebuild pipeline:
   ```bash
   python scripts/load_duckdb.py          # if using CSV
   cd dbt_project && dbt run && cd ..
   python scripts/generate_golden_metrics.py
   ```
3. The updated `golden_metrics.json` is now on disk
4. Open Claude Code in this project directory (or push to the repo if using Claude on the web)
5. Type `/marketing` — Claude reads `golden_metrics.json` and generates the dashboard with your numbers

> **Key rule from CLAUDE.md §14:** Claude reads `golden_metrics.json` directly and
> copies values verbatim. It does not recalculate from raw data. This guarantees the
> dashboard matches the warehouse to the cent.

### Forcing live MCP data (bypassing golden layer)

If you want Claude to query the MCP servers in real time instead:

```
/marketing-mcp
/campaign-mcp
/attribution-mcp
```

The `-mcp` suffix tells Claude to hit the mock MCP servers directly and add an
`⚡ Live MCP` badge. Use this to spot-check raw platform data before a golden
layer refresh.

---

## Column Mapping Reference

If your source file has different column names, rename them before saving.
The dbt staging models expect these exact names:

### Google Ads (`stg_google_ads_performance`)

| Your column | dbt staging name | Type |
|-------------|-----------------|------|
| Report date | `date` | DATE |
| Campaign ID | `campaign_id` | STRING |
| Campaign name | `campaign_name` | STRING |
| Campaign type | `campaign_type` | STRING |
| Impressions | `impressions` | INT64 |
| Clicks | `clicks` | INT64 |
| Cost / Spend | `cost` | FLOAT64 |
| Conversions | `conversions` | INT64 |

### Meta Ads (`stg_meta_ads_performance`)

| Your column | dbt staging name | Type |
|-------------|-----------------|------|
| Report date | `date` | DATE |
| Campaign ID | `campaign_id` | STRING |
| Campaign name | `campaign_name` | STRING |
| Objective | `objective` | STRING |
| Impressions | `impressions` | INT64 |
| Amount spent | `spend` | FLOAT64 |
| Link clicks | `link_clicks` | INT64 |
| Purchases | `purchases` | INT64 |

### GA4 (`stg_ga4_sessions`)

| Your column | dbt staging name | Type |
|-------------|-----------------|------|
| Date | `date` | DATE |
| Default channel grouping | `channel_group` | STRING |
| Device category | `device_category` | STRING |
| Sessions | `sessions` | INT64 |
| Engaged sessions | `engaged_sessions` | INT64 |
| Conversions | `conversions` | INT64 |

---

## Troubleshooting

**dbt test fails after import**
The staging models have `not_null` and `unique` tests. Check for:
- Missing `date` values in any row
- Duplicate `campaign_id + date` combinations
- NULL in `cost` or `spend` columns

Run `dbt test --select staging` to see exactly which test failed.

**validate_metrics.py reports drift after import**
This is expected — the JSON was generated from the old data. Re-run:
```bash
python scripts/generate_golden_metrics.py
python scripts/validate_metrics.py   # should now exit 0
```

**Claude shows old numbers after import**
The skill reads `golden_metrics.json` from disk. Make sure you ran
`generate_golden_metrics.py` after your `dbt run`. In Claude Code on the web,
you also need to push the updated JSON to the repo so the container has the
latest file.
