# 🚀 Production Readiness Guide

How to deploy this project to BigQuery or Snowflake, automate daily data refreshes,
run the test suite, and verify that every dashboard number matches your warehouse exactly.

---

## Promoting v0.9 → v1.0 — Pre-Release Checklist

Before flipping the GitHub release tag from `v0.9.0` pre-release to `v1.0.0`, walk through this checklist. Each item is small but catches a different class of failure.

### 1. CI/CD must be green on `main`

- [ ] `ci.yml` — last run on `main` exits 0 (validates real Olist-anchored data after PR #5)
- [ ] `warehouse-deploy.yml` — both BigQuery and Snowflake jobs pass, OR the Snowflake job is intentionally marked `continue-on-error: true` if you don't have credits
- [ ] `scheduled-refresh.yml` — at least one successful daily run in the Actions tab
- [ ] `daily-synthetic-data.yml` — at least one successful daily run; check that the auto-commit lands on `main`

### 2. Required GitHub secrets are configured

Go to **Settings → Secrets and variables → Actions** and confirm each:

- [ ] `GCP_PROJECT_ID`
- [ ] `GCP_SERVICE_ACCOUNT_KEY_JSON` (full JSON contents, not a path)
- [ ] `SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`, `SNOWFLAKE_PASSWORD`, `SNOWFLAKE_WAREHOUSE`, `SNOWFLAKE_DATABASE`, `SNOWFLAKE_SCHEMA`

The DuckDB PR-gate workflow needs no secrets — it runs entirely on the GitHub Actions runner.

### 3. Local end-to-end run passes

From a fresh clone (or after `rm -rf data/olist_analytics.duckdb`):

```bash
python scripts/load_duckdb.py
cd dbt_project && dbt run --target duckdb && dbt test --target duckdb && cd ..
python scripts/generate_golden_metrics.py
python scripts/validate_metrics.py     # must exit 0
pytest tests/ -v                       # must pass
```

- [ ] dbt run completes with no errors
- [ ] dbt test passes (no `not_null`, `unique`, or `relationships` test failures)
- [ ] `validate_metrics.py` exits 0
- [ ] `pytest` passes (skipping `test_api.py` if the ML model isn't trained is acceptable)

### 4. Dashboards render with correct data

- [ ] `streamlit run streamlit_app/app.py` — check that the sidebar shows the correct connection badge and the Data Sources page loads
- [ ] Open `dashboards/full_funnel_marketing_dashboard.html` locally and verify the KPI values match `dashboards/golden_metrics.json`
- [ ] In Claude Code, type `/marketing` — values should match the HTML dashboard exactly

### 5. Documentation links resolve

- [ ] Every link in `README.md` Documentation table opens the right file
- [ ] `docs/architecture.md` renders correctly (no broken anchors)
- [ ] The architecture v2 image displays at the top of the README

### 6. dbt Fusion compatibility (if applicable)

dbt Fusion is stricter than dbt Core. If you use it locally, verify:

- [ ] `metricflow_time_spine.sql` — SQL comments are OUTSIDE the `{{ config() }}` Jinja block
- [ ] `metrics.yml` and `sem_marketing.yml` — start with `version: 2` (legacy YAML without it triggers warning `dbt1157`)
- [ ] `dbt parse` runs clean with no `dbt1502` errors

These three points are now enforced in the codebase as of PR #5.

### 7. Release hygiene

- [ ] PR #5 (or its successor) is merged to `main`
- [ ] All stale feature branches are deleted (`claude/*`, `feat/*`)
- [ ] The `v0.9.0` GitHub release has been live for at least 24 hours with no surprises
- [ ] Edit the existing release: uncheck "Pre-release", change tag to `v1.0.0`, click Update — OR draft a fresh `v1.0.0` release referencing the v0.9 testing period in the notes

### 8. LinkedIn post readiness

- [ ] Repo description on GitHub reflects v1.0 scope (currently mentions $0/mo, 5 warehouses)
- [ ] README hero gif / video loads on a fresh browser session (no auth)
- [ ] Architecture v2 image renders correctly when opened from the GitHub-hosted README

---

## What Was Built

| Component | File(s) | Purpose |
|-----------|---------|---------|
| PR gate | `.github/workflows/ci.yml` | Compile + test every pull request on DuckDB (fast, no cloud creds) |
| Warehouse deploy | `.github/workflows/warehouse-deploy.yml` | Deploy to BigQuery **and** Snowflake on every push to `main` |
| Scheduled refresh | `.github/workflows/scheduled-refresh.yml` | Daily 6 AM UTC — re-run dbt, regenerate golden metrics |
| Daily synthetic data | `.github/workflows/daily-synthetic-data.yml` | Daily 5 AM UTC — append one new day to the mock dataset |
| Warehouse adapters | `scripts/_warehouse_adapters.py` | Uniform connection layer for DuckDB / BigQuery / Snowflake |
| Multi-target generate | `scripts/generate_golden_metrics.py` | `--target` and `--live` flags added; default (DuckDB) unchanged |
| Multi-target validate | `scripts/validate_metrics.py` | `--target` flag; compares warehouse mart tables to golden JSON |
| Daily append script | `scripts/daily_synthetic_append.py` | Appends N realistic days to mock CSVs |
| Test suite | `tests/` | 20+ pytest assertions on golden metrics structure + API endpoint |
| Connector UI | `streamlit_app/pages/connectors.py` | Streamlit Data Sources page (file upload, warehouse config, MCP status) |

---

## 1. CI/CD — GitHub Actions Setup

### 1.1 Required GitHub Secrets

Go to your repository → **Settings → Secrets and variables → Actions → New repository secret**.

#### BigQuery

| Secret name | Value | Where to get it |
|-------------|-------|-----------------|
| `GCP_PROJECT_ID` | Your GCP project ID, e.g. `my-project-123` | [GCP Console](https://console.cloud.google.com) → project selector |
| `GCP_SERVICE_ACCOUNT_KEY_JSON` | Full contents of a service account JSON key file | See §1.2 below |

#### Snowflake

| Secret name | Value | Where to get it |
|-------------|-------|-----------------|
| `SNOWFLAKE_ACCOUNT` | Account identifier, e.g. `xy12345.us-east-1` | Snowflake UI → bottom-left profile → Account details |
| `SNOWFLAKE_USER` | Your Snowflake username | Snowflake admin |
| `SNOWFLAKE_PASSWORD` | Your Snowflake password | Snowflake admin |
| `SNOWFLAKE_WAREHOUSE` | Virtual warehouse name, e.g. `ANALYTICS_WH` | Snowflake → Warehouses |
| `SNOWFLAKE_DATABASE` | Database name, e.g. `OLIST_ANALYTICS` | Snowflake → Databases |
| `SNOWFLAKE_SCHEMA` | Schema name, e.g. `PUBLIC` | Default: `PUBLIC` |

> **None of the DuckDB / local workflows need secrets** — the `ci.yml` PR gate runs
> entirely on DuckDB with no cloud credentials.

### 1.2 Creating a BigQuery Service Account Key

```bash
# 1. Create a service account
gcloud iam service-accounts create dbt-ci \
  --display-name="dbt CI service account" \
  --project=YOUR_PROJECT_ID

# 2. Grant required roles
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:dbt-ci@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:dbt-ci@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/bigquery.jobUser"

# 3. Download the key
gcloud iam service-accounts keys create /tmp/dbt-ci-key.json \
  --iam-account=dbt-ci@YOUR_PROJECT_ID.iam.gserviceaccount.com

# 4. Copy the ENTIRE contents of the JSON file into the GitHub Secret
cat /tmp/dbt-ci-key.json
```

Paste the entire JSON output (including the `{ }` braces) as the value of `GCP_SERVICE_ACCOUNT_KEY_JSON`.

### 1.3 What Each Workflow Does

#### `ci.yml` — runs on every PR

```
checkout → pip install → dbt deps → generate mock data → load DuckDB
→ dbt run (DuckDB) → dbt test → generate golden metrics → validate drift
→ pytest tests/
```

If **any step fails, the PR is blocked**. The validate step prints exactly which
metric drifted, what the golden value was, and what the live warehouse returned.

#### `warehouse-deploy.yml` — runs on push to `main`

Two jobs run **in parallel** — one for BigQuery, one for Snowflake:

```
load raw data into warehouse → dbt run --target <warehouse>
→ dbt test → generate golden metrics from warehouse
→ validate (must exit 0) → commit updated golden_metrics.json
```

The BigQuery job commits the updated `golden_metrics.json` back to the repo.
This means every merge to `main` automatically refreshes the dashboards.

#### `scheduled-refresh.yml` — runs daily at 06:00 UTC

```
append today's synthetic data → load DuckDB → dbt run → dbt test
→ generate golden metrics (--live) → validate → commit golden_metrics.json
```

#### `daily-synthetic-data.yml` — runs daily at 05:00 UTC (before the refresh)

Appends one new day of synthetic data to the mock marketing CSVs.
Can be triggered manually with a custom `--days` count via `workflow_dispatch`.

---

## 2. Verify Dashboard == Warehouse (The Guarantee)

The data chain is:

```
Raw data
  → dbt staging models (type casting, renaming)
  → dbt intermediate models (joins)
  → dbt mart tables (fct_marketing_daily, stg_marketing_attribution, ...)
  → generate_golden_metrics.py reads mart tables
  → dashboards/golden_metrics.json  ← all HTML dashboards read this
  → validate_metrics.py re-queries the warehouse and diffs vs JSON
```

To run the full verification locally:

```bash
# Step 1: run dbt on your warehouse of choice
dbt run --target bigquery    # or snowflake, or duckdb

# Step 2: generate the golden snapshot from that warehouse
python scripts/generate_golden_metrics.py --target bigquery

# Step 3: re-query the warehouse and compare to the snapshot
python scripts/validate_metrics.py --target bigquery
# exits 0 = in sync | exits 1 = drift (lists exactly which metrics)

# Step 4: open any HTML dashboard
# It reads golden_metrics.json — if step 3 passed, dashboard == warehouse
```

The validate script checks ~20 metrics including:
- Total spend (Google, Meta, combined) — $1 tolerance
- All-time and 90-day session counts — ±1 row
- Blended ROAS — ±0.5% relative tolerance
- Session CVR — ±0.5%
- Per-channel ROAS (Google Ads, Meta Ads)
- HubSpot total contacts
- Salesforce closed-won revenue

---

## 3. Daily Synthetic Data

The synthetic dataset originally ended on 2026-03-15. The daily append script
adds one new day each run so the dataset grows continuously — making dashboards
feel like a live production system.

```bash
# Append 1 day (next day after the latest date in the CSV)
python scripts/daily_synthetic_append.py

# Backfill 30 days at once
python scripts/daily_synthetic_append.py --days 30

# Full reset (regenerates everything from scratch)
python scripts/daily_synthetic_append.py --reset
```

After appending, use `--live` to auto-detect the new latest date:

```bash
dbt run --target duckdb
python scripts/generate_golden_metrics.py --live   # uses max(date) from fct_marketing_daily
python scripts/validate_metrics.py --target duckdb
```

**How the data is generated:**
Each new day's values are seeded by the calendar date (same date always produces
identical numbers — reproducible), then scaled by:
- Monthly seasonality (November = 1.8×, January = 0.7×)
- Day-of-week factor (weekends = 0.8×)
- ±10–30% random noise per metric

The same 6 Google campaigns and 5 Meta campaigns appear every day with consistent
IDs, so dbt joins and attribution models continue to work correctly.

---

## 4. Running the Test Suite

```bash
# Install test dependencies (already in requirements.txt)
pip install pytest pytest-httpx

# Run all tests
pytest tests/ -v

# Run only golden metrics tests (no warehouse needed)
pytest tests/test_golden_metrics.py -v

# Run only API tests (requires ml/lead_scoring_model.json)
pytest tests/test_api.py -v
```

The golden metrics tests run against the committed `dashboards/golden_metrics.json`
and require no database connection. They will be skipped automatically if the file
does not exist.

The API tests require the trained XGBoost model. To generate it:

```bash
python ml/src/train.py
```

---

## 5. Local Development with BigQuery or Snowflake

### 5.1 Copy and fill the profile

```bash
cp dbt_project/profiles.yml.example dbt_project/profiles.yml
# Edit profiles.yml and fill in your credentials
# profiles.yml is in .gitignore — it will never be committed
```

### 5.2 Run dbt against your warehouse

```bash
# BigQuery (uses OAuth — run `gcloud auth application-default login` first)
dbt run --target bigquery

# Snowflake
dbt run --target snowflake

# Generate golden metrics from your warehouse
python scripts/generate_golden_metrics.py --target bigquery
python scripts/validate_metrics.py --target bigquery
```

### 5.3 Switching back to DuckDB

```bash
dbt run --target duckdb           # default — no credentials needed
python scripts/generate_golden_metrics.py   # reads DuckDB
```
