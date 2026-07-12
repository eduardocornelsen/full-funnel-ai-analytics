# 🌍 Multi-Warehouse Portability Guide

This project is designed to be warehouse-agnostic. While it defaults to BigQuery and DuckDB, it can be deployed to Snowflake or Databricks with minimal changes.

## ❄️ Snowflake Deployment
1. **Setup:** Create a Snowflake account (30-day trial available).
2. **Configuration:** Copy the `snowflake` target from `dbt_project/profiles.yml.example` into your `profiles.yml` and fill in your account credentials.
3. **Data Loading:** Use Snowflake's S3/GCS integration, or adapt `scripts/load_bigquery.py`.
4. **dbt:** Run `dbt build --target snowflake`.

## 🧱 Databricks Deployment
1. **Setup:** Create a Databricks workspace.
2. **Configuration:** Copy the `databricks` target from `dbt_project/profiles.yml.example` into your `profiles.yml`.
3. **Data Loading:** Upload CSVs to DBFS or Unity Catalog.
4. **dbt:** Run `dbt build --target databricks`.

## 🐘 Supabase (Postgres)
1. **Setup:** Create a Supabase project.
2. **Loading:** Run `python scripts/load_supabase.py`.
3. **dbt:** Run `dbt build --target supabase`.
