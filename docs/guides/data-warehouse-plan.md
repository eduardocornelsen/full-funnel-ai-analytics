# BigQuery Data Warehouse — Implementation Plan

## Context

The project currently queries platform APIs live via MCP servers on every request.
This plan adds a real data warehouse layer so that:
- Historical data is persisted and queryable across sessions
- dbt models actually execute (they exist but currently run against DuckDB with no live data loaded)
- MCP servers can optionally query BigQuery instead of platform APIs directly
- Trend charts and cross-platform joins use SQL, not AI inference

**Good news:** most of the infrastructure is already stubbed out.
- `dbt_project/profiles.yml` already has a `bigquery` target configured
- All staging models exist: `stg_google_ads_performance.sql`, `stg_meta_ads_performance.sql`, `stg_ga4_sessions.sql`, `stg_hubspot_*`, `stg_salesforce_*`
- Marts, intermediates, and metrics are fully written
- Sources are declared in `sources.yml`

---

## Architecture Overview

```
Platform APIs
  ├── Google Ads API  ──────────────────────┐
  ├── Meta Marketing API ───────────────────┤
  ├── Google Analytics 4 API ───────────────┤  ETL (Fivetran / custom)
  ├── HubSpot API ──────────────────────────┤
  └── Salesforce API ────────────────────────┘
                                             ↓
                                    BigQuery (raw schema)
                                             ↓
                                    dbt (transform)
                                             ↓
                                    BigQuery (marts schema)
                                         ↙       ↘
                               MCP servers      Dashboards
                               (query BQ)       (direct SQL)
```

---

## Step-by-Step Implementation

---

### Phase 1 — GCP Project Setup

**1.1 Create GCP project**
- Go to console.cloud.google.com → New Project
- Suggested name: `full-funnel-analytics`
- Note the Project ID (e.g. `full-funnel-analytics-123456`) — this goes into `GCP_PROJECT_ID`

**1.2 Enable APIs**
Enable all of these in GCP Console → APIs & Services:
- BigQuery API
- BigQuery Data Transfer Service API
- Google Analytics Data API (for GA4)
- Google Ads API

**1.3 Create BigQuery datasets**
In BigQuery Console, create three datasets in the same region (recommend `US`):
```
full_funnel_raw       ← raw tables loaded by ETL
olist_analytics       ← dbt output (matches profiles.yml dataset name)
olist_analytics_dev   ← dbt dev target (per-developer sandbox)
```

**1.4 Create service account**
- IAM & Admin → Service Accounts → Create
- Name: `dbt-pipeline`
- Roles: `BigQuery Data Editor`, `BigQuery Job User`
- Download JSON key → save as `dbt_service_account.json` (never commit this)
- Add to `.gitignore`: `dbt_service_account.json`, `*.json` credentials

---

### Phase 2 — ETL: Load Raw Platform Data into BigQuery

Choose one of two approaches depending on budget and timeline:

#### Option A — Fivetran (recommended, zero maintenance)
Fivetran has native connectors for all 5 platforms. Setup per connector:

| Connector | Destination dataset | Key tables loaded |
|-----------|-------------------|-------------------|
| Google Ads | `full_funnel_raw.google_ads_*` | campaigns, ad_groups, keywords, performance |
| Meta Ads | `full_funnel_raw.meta_ads_*` | campaigns, adsets, ads, insights |
| Google Analytics 4 | `full_funnel_raw.ga4_*` | events, sessions (via BQ export) |
| HubSpot | `full_funnel_raw.hubspot_*` | contacts, deals, pipelines |
| Salesforce | `full_funnel_raw.salesforce_*` | opportunities, accounts, leads |

Steps:
1. Sign up at fivetran.com → connect BigQuery as destination
2. Add each connector, authenticate with platform credentials
3. Set sync frequency: every 6 hours for ads platforms, daily for CRM
4. Run initial historical sync

#### Option B — GA4 Native BigQuery Export (free, GA4 only)
If you only want GA4 for now:
1. GA4 Admin → BigQuery Linking → Link to your GCP project
2. Tables land automatically in `full_funnel_raw.ga4_events_YYYYMMDD`
3. No cost beyond BigQuery storage/query fees

#### Option C — Custom scripts (for everything else without Fivetran)
Write Python scripts using each platform's SDK to pull data and load to BigQuery via `google-cloud-bigquery` client. Store scripts in `/etl/` directory. Schedule via Cloud Scheduler + Cloud Run.

---

### Phase 3 — Update dbt to Target BigQuery

**3.1 Set the environment variable**
```bash
export GCP_PROJECT_ID="full-funnel-analytics-123456"
```
Add to `.env` (already in `.gitignore`).

**3.2 Switch dbt profile target**
`dbt_project/profiles.yml` already has the BigQuery target defined:
```yaml
bigquery:
  type: bigquery
  method: oauth          # change to service-account for CI/CD
  project: "{{ env_var('GCP_PROJECT_ID') }}"
  dataset: olist_analytics
  threads: 4
  location: US
```

For service account auth (recommended over oauth for automation):
```yaml
bigquery:
  type: bigquery
  method: service-account
  project: "{{ env_var('GCP_PROJECT_ID') }}"
  keyfile: "{{ env_var('GOOGLE_APPLICATION_CREDENTIALS') }}"
  dataset: olist_analytics
  threads: 4
  location: US
```

**3.3 Update sources.yml to point to raw tables**
Change the schema references from `main` (DuckDB) to BigQuery raw dataset:
```yaml
# dbt_project/models/staging/sources.yml
sources:
  - name: marketing
    schema: full_funnel_raw      # ← was "main"
    database: full-funnel-analytics-123456
    tables:
      - name: google_ads_daily_performance
      - name: meta_ads_daily_performance
      - name: ga4_daily_sessions
      - name: hubspot_contacts
      - name: hubspot_deals
      - name: salesforce_opportunities
      ...
```

**3.4 Run dbt against BigQuery**
```bash
cd dbt_project

# Test connection
dbt debug --target bigquery

# Run all models
dbt run --target bigquery

# Run tests
dbt test --target bigquery

# Generate docs
dbt docs generate && dbt docs serve
```

Expected output: all staging views, intermediate ephemeral models, and marts tables materialised in `olist_analytics` dataset in BigQuery.

---

### Phase 4 — Update MCP Servers to Query BigQuery

Currently MCP servers call platform APIs directly. After the warehouse is live, they should query BigQuery marts instead for:
- Historical aggregates and trend lines
- Cross-platform joins (e.g. GA4 sessions + Google Ads spend on the same date)
- Anything beyond the API's default lookback window

Two approaches:

#### Option A — Add a BigQuery MCP server
Install or build an MCP server that executes SQL against BigQuery:
```json
// .claude/mcp_settings.json (or equivalent)
{
  "bigquery": {
    "command": "uvx",
    "args": ["mcp-server-bigquery"],
    "env": {
      "GOOGLE_APPLICATION_CREDENTIALS": "/path/to/dbt_service_account.json",
      "GCP_PROJECT_ID": "full-funnel-analytics-123456"
    }
  }
}
```
Then Claude can call `bigquery.query` with SQL targeting `olist_analytics.fct_marketing_attribution`, `fct_channel_performance`, etc.

#### Option B — Keep platform MCP servers, add BQ for analytics queries
Use platform MCPs for real-time campaign data (today's spend, active campaigns) and BigQuery MCP for historical analysis and cross-platform aggregates. Both can coexist.

---

### Phase 5 — Update Dashboard Commands

Once BigQuery is live, update command definitions to prefer warehouse queries for historical data:

```
# Example addition to /marketing command
For trend data (Spend vs Revenue by week), query BigQuery mart table
`olist_analytics.fct_marketing_daily` instead of platform APIs —
this gives consistent, pre-joined data across all channels.
```

Update `CLAUDE.md` to note which metrics come from BQ marts vs live platform APIs.

---

### Phase 6 — Schedule dbt Runs

To keep marts fresh after ETL loads new raw data:

**Option A — dbt Cloud (simplest)**
1. Sign up at cloud.getdbt.com (free tier available)
2. Connect to this repo and BigQuery
3. Create a job: `dbt run && dbt test`, schedule every 6 hours after ETL syncs

**Option B — Cloud Composer (Airflow on GCP)**
```python
# DAG: etl_to_dbt
# 1. Trigger Fivetran sync
# 2. Wait for completion
# 3. Run dbt build
# 4. Alert on test failures
```

**Option C — GitHub Actions**
```yaml
# .github/workflows/dbt.yml
on:
  schedule:
    - cron: '0 */6 * * *'
jobs:
  dbt:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: pip install dbt-bigquery
      - run: dbt run --target bigquery
        env:
          GCP_PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
          GOOGLE_APPLICATION_CREDENTIALS_JSON: ${{ secrets.GCP_SA_KEY }}
```

---

## Recommended Sequence (shortest path to working BQ)

| Step | Action | Time estimate |
|------|--------|---------------|
| 1 | Create GCP project + enable APIs + create datasets | 30 min |
| 2 | Set up GA4 → BigQuery native export (free) | 15 min |
| 3 | Update `sources.yml` schema to `full_funnel_raw` | 10 min |
| 4 | Set env vars, run `dbt debug --target bigquery` | 15 min |
| 5 | Run `dbt run --target bigquery` with GA4 data | 30 min |
| 6 | Add BigQuery MCP server to Claude config | 20 min |
| 7 | Add Fivetran connectors for Google Ads + Meta | 1–2 hours |
| 8 | Add Fivetran connectors for HubSpot + Salesforce | 1–2 hours |
| 9 | Schedule dbt via dbt Cloud | 20 min |

**Total: ~1 day to a fully working warehouse pipeline**

---

## Environment Variables Needed

Add all of these to a `.env` file at the project root (already in `.gitignore`):

```bash
# BigQuery / GCP
GCP_PROJECT_ID=full-funnel-analytics-123456
GOOGLE_APPLICATION_CREDENTIALS=/path/to/dbt_service_account.json

# Already in use by MCP servers (no change needed)
# GOOGLE_ADS_DEVELOPER_TOKEN, GOOGLE_ADS_CLIENT_ID, etc.
# META_ACCESS_TOKEN, META_AD_ACCOUNT_ID
# GA4_PROPERTY_ID
# HUBSPOT_ACCESS_TOKEN
# SALESFORCE_CLIENT_ID, SALESFORCE_CLIENT_SECRET
```

---

## Files to Create / Modify

| File | Action |
|------|--------|
| `dbt_project/models/staging/sources.yml` | Update schema from `main` → `full_funnel_raw` |
| `dbt_project/profiles.yml` | Switch method to `service-account`, add keyfile env var |
| `.env` | Add `GCP_PROJECT_ID` and `GOOGLE_APPLICATION_CREDENTIALS` |
| `.gitignore` | Ensure `*.json`, `.env`, `dbt_service_account.json` are ignored |
| `CLAUDE.md` | Add note on which metrics come from BQ marts vs live APIs |
| `.claude/mcp_settings.json` | Add BigQuery MCP server entry |
| `etl/` (new directory) | Optional custom Python ETL scripts if not using Fivetran |

---

## Key Decision Points

1. **ETL tool**: Fivetran (paid, zero maintenance) vs custom scripts (free, maintenance burden). For a demo/portfolio project, custom Python scripts are fine. For production, Fivetran.
2. **dbt auth**: OAuth works locally. Use service account JSON for any CI/CD or scheduled runs.
3. **BigQuery MCP**: Check if a community `mcp-server-bigquery` package exists before building one. As of early 2026 several exist on PyPI.
4. **Region**: Pick `US` and keep all datasets in the same region — cross-region queries in BigQuery fail.
