# Plan 1: Production Readiness — BigQuery & Snowflake, CI/CD, Automated Tests

## Context

The project has a solid dbt medallion architecture, multi-warehouse profile configuration, a golden layer validation script, and a working metric-enforcement pipeline. However it is not production-ready in automated form: there is no CI/CD, no scheduled data refresh, no pytest suite, and `generate_golden_metrics.py` / `validate_metrics.py` are hardcoded to DuckDB. This plan makes the pipeline run unattended on real warehouses and ensures dashboards are verifiably in sync with raw warehouse data.

---

## What Was Built

### 1. GitHub Actions Workflows (`.github/workflows/`)

| File | Trigger | Purpose |
|------|---------|---------|
| `ci.yml` | PR to `main` | Fast gate: dbt compile + test on DuckDB, validate golden layer |
| `warehouse-deploy.yml` | Push to `main` or manual dispatch | Deploy dbt to BigQuery + Snowflake in parallel; regenerate golden metrics |
| `scheduled-refresh.yml` | Daily 6 AM UTC | Re-run dbt on warehouses; regenerate and commit `golden_metrics.json` |
| `daily-synthetic-data.yml` | Daily 5 AM UTC | Append one new day of synthetic data; re-run dbt; commit golden metrics |

### 2. BigQuery CI Auth Fix

`profiles.yml.example` gains a `bigquery-ci` output block using `service-account-json` method (no interactive OAuth) reading from `GCP_SERVICE_ACCOUNT_KEY_JSON` env var.

### 3. Warehouse-Aware Scripts

Both `scripts/generate_golden_metrics.py` and `scripts/validate_metrics.py` gain a `--target` CLI flag:
- `--target duckdb` (default) — existing behavior, no breaking change
- `--target bigquery` — queries BigQuery mart tables via google-cloud-bigquery
- `--target snowflake` — queries Snowflake mart tables via snowflake-connector-python

### 4. Daily Synthetic Data Append

`scripts/daily_synthetic_append.py` — new script that:
- Reads the last date in existing data
- Generates one new day with realistic patterns (seasonality, day-of-week factors, ±10% noise)
- Appends to all `data/mock_marketing/*.csv` files
- Supports `--days N` for backfilling and `--reset` to regenerate all from scratch

### 5. pytest Test Suite (`tests/`)

| File | Tests |
|------|-------|
| `tests/conftest.py` | Shared fixtures (golden data loader, project paths) |
| `tests/test_golden_metrics.py` | Structure, no nulls, attribution sums to 100%, funnel ordering, ROAS plausibility |
| `tests/test_api.py` | FastAPI `/score` endpoint with valid + invalid payloads |

---

## How to Verify Dashboard == Warehouse

The chain: **Raw data → dbt mart tables → golden_metrics.json → dashboards**

```bash
# Step 1: Run dbt on your warehouse
dbt run --target bigquery

# Step 2: Generate golden snapshot from that warehouse
python scripts/generate_golden_metrics.py --target bigquery

# Step 3: Re-query warehouse and compare to snapshot (exits 0 = in sync)
python scripts/validate_metrics.py --target bigquery

# Step 4: Dashboard reads the committed golden_metrics.json
# If step 3 passed → dashboard == warehouse. Guaranteed.
```

CI enforces this automatically on every push to `main`.

---

## GitHub Secrets Required

| Secret | Purpose |
|--------|---------|
| `GCP_PROJECT_ID` | BigQuery project |
| `GCP_SERVICE_ACCOUNT_KEY_JSON` | Full JSON key for BigQuery service account |
| `SNOWFLAKE_ACCOUNT` | Snowflake account identifier |
| `SNOWFLAKE_USER` | Snowflake username |
| `SNOWFLAKE_PASSWORD` | Snowflake password |
| `SNOWFLAKE_WAREHOUSE` | Snowflake virtual warehouse name |
| `SNOWFLAKE_DATABASE` | Snowflake database name |
| `SNOWFLAKE_SCHEMA` | Snowflake schema (default: PUBLIC) |

---

## Running Tests

```bash
# Install test dependencies
pip install pytest pytest-httpx

# Run full test suite
pytest tests/ -v

# Validate golden layer (DuckDB)
python scripts/validate_metrics.py --target duckdb

# Append one day of synthetic data
python scripts/daily_synthetic_append.py

# Backfill 30 days of synthetic data
python scripts/daily_synthetic_append.py --days 30
```
