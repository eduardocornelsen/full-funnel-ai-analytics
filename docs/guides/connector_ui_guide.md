# 🔌 Connector UI & Live Dashboards Guide

How the Data Sources page works, what "live dashboards" means in each environment,
and how to get the most out of the Streamlit connector interface.

---

## Starting the App

```bash
streamlit run streamlit_app/app.py
```

The sidebar now shows a **connection status badge**:

| Badge | Meaning |
|-------|---------|
| 🟡 DuckDB local | Running against the local `data/olist_analytics.duckdb` file |
| 🟢 BigQuery | Active connection saved to a BigQuery project |
| 🟢 Snowflake | Active connection saved to a Snowflake account |

The badge reads `~/.full_funnel_connectors.json` — a config file that lives outside
the repo so credentials are never committed to git.

---

## Data Sources Page

Click **Data Sources** in the Streamlit sidebar to open the three-tab interface.

---

### Tab 1 — File Upload

**What it does:** Lets you replace any of the mock marketing CSVs by uploading a
CSV or Excel file from your computer.

**How to use it:**

1. Drag and drop (or click to browse) a `.csv`, `.xlsx`, or `.xls` file
2. The app shows the first 20 rows as a preview table
3. Choose which table to replace from the dropdown:
   - Google Ads daily performance
   - Meta Ads daily performance
   - GA4 daily sessions
   - HubSpot contacts / deals
   - Salesforce opportunities
4. Click **Save to mock data**

The file is written to `data/mock_marketing/<table_name>.csv`.

**After saving**, rebuild the pipeline from the terminal:

```bash
python scripts/load_duckdb.py
cd dbt_project && dbt run --target duckdb && cd ..
python scripts/generate_golden_metrics.py
```

Your data will then appear in all dashboards and in Claude.

---

### Tab 2 — Warehouse Connection

**What it does:** Lets you configure and test a connection to DuckDB, BigQuery,
or Snowflake — and save it as the active default.

#### DuckDB

- Enter the path to your `.duckdb` file (defaults to the project's local file)
- Click **Test Connection** — runs a `SELECT 1` and confirms the file exists
- Click **Save connection** — writes the path to `~/.full_funnel_connectors.json`

#### BigQuery

- Enter your GCP Project ID
- Make sure `GOOGLE_APPLICATION_CREDENTIALS` points to a service account JSON key,
  or run `gcloud auth application-default login` first
- Click **Test Connection** — runs a `SELECT 1` against your project
- Click **Save connection**

#### Snowflake

- Fill in Account, User, Password, Warehouse, Database, Schema
- Click **Test Connection** — opens a Snowflake session and runs `SELECT 1`
- Click **Save connection** — credentials are stored locally, never in git

#### Table Preview

At the bottom of Tab 2, enter any mart table name (e.g. `fct_marketing_daily`)
and click **Preview** to see the first 20 rows from your active connection.
This is the fastest way to confirm dbt has populated the tables correctly.

---

### Tab 3 — MCP Server Status

**What it does:** Lists all six MCP servers configured in `.mcp.json` and shows
their current data state.

For mock servers (Google Ads, Meta Ads, GA4, HubSpot, Salesforce), it shows:
- The source CSV file path
- Row count
- Latest date in the data

For the `dbt-semantic-layer` server, it shows the command used to start it.

Use this tab to confirm:
- Data is present after an import or daily append
- All servers are pointing to the correct files
- The latest date in the data is what you expect

---

## Live Dashboards — What Works Where

This is a common point of confusion. Here is the precise breakdown:

### Claude Code (this project's primary AI layer)

Claude Code renders **HTML artifacts** — fully interactive charts built with
Chart.js or D3.js. These run entirely in the browser with no server.

- ✅ Interactive charts (hover, tooltips, zoom)
- ✅ Consistent numbers (reads `golden_metrics.json` snapshot)
- ❌ No live database connection (snapshot must be regenerated to update)
- ❌ No user input / filters that query the warehouse in real time

**To make Claude show your latest data:** regenerate `golden_metrics.json` then
either push to the repo (web sessions) or the file is already updated locally
(CLI / desktop sessions).

### Streamlit (this project's live app)

The Streamlit app at `streamlit_app/app.py` is a **true live dashboard**:

- ✅ Queries DuckDB (or BigQuery/Snowflake) on every interaction
- ✅ Date range slider updates charts in real time
- ✅ Can reflect data from multiple warehouses
- ✅ The connector UI (Data Sources page) is part of this app

Run it with: `streamlit run streamlit_app/app.py`

### HTML Dashboards in a browser

The HTML files in `dashboards/` read `golden_metrics.json` via a relative path.
Open them locally with a web server:

```bash
cd dashboards && python -m http.server 8080
# Open http://localhost:8080/full_funnel_marketing_dashboard.html
```

These are static snapshots — the same as what Claude renders, but in a browser tab.

### Perplexity

Perplexity has no code execution environment. It cannot run Python, query databases,
or render interactive HTML. It is not suitable for live or snapshot dashboards.

---

## Connector Config File

Connection settings are saved to `~/.full_funnel_connectors.json` on your local
machine. This file is **outside the repository** and is never committed to git.

Example contents after saving a BigQuery connection:

```json
{
  "active": "bigquery",
  "connections": {
    "duckdb": {
      "path": "/home/user/full-funnel-ai-analytics/data/olist_analytics.duckdb"
    },
    "bigquery": {
      "project": "my-gcp-project"
    }
  }
}
```

To reset to DuckDB locally, either edit this file or use the Warehouse Connection
tab to save a DuckDB connection and tick "Set as default active connection".

---

## Daily Synthetic Data — Making the Dataset Feel Live

The `daily_synthetic_append.py` script adds one new day of data each time it runs.
GitHub Actions runs it automatically at 05:00 UTC every day.

To run it manually:

```bash
# Add today's data (next day after the last date in the CSV)
python scripts/daily_synthetic_append.py

# Add the last 7 days at once
python scripts/daily_synthetic_append.py --days 7

# Regenerate everything from scratch
python scripts/daily_synthetic_append.py --reset
```

Then rebuild to see the new data:

```bash
python scripts/load_duckdb.py
cd dbt_project && dbt run --target duckdb && cd ..
python scripts/generate_golden_metrics.py --live
```

The `--live` flag tells the generator to read `MAX(date)` from
`fct_marketing_daily` instead of the hardcoded `2026-03-15` anchor — so
the 90-day window automatically moves forward with each new day.

---

## Quick Reference: End-to-End Data Update

```
1. Import your file (UI or CLI)         → data/mock_marketing/<table>.csv
2. python scripts/load_duckdb.py        → data/olist_analytics.duckdb
3. cd dbt_project && dbt run && cd ..   → mart tables built
4. python scripts/generate_golden_metrics.py → dashboards/golden_metrics.json
5. python scripts/validate_metrics.py   → confirms 0 drift
6. Open Claude / Streamlit / HTML       → your data, guaranteed accurate
```
