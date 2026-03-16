# 🌍 Multi-Warehouse Portability Guide

This project is designed to be warehouse-agnostic. While it defaults to BigQuery and DuckDB, it can be deployed to Snowflake or Databricks with minimal changes.

## ❄️ Snowflake Deployment
1. **Setup:** Create a Snowflake account (30-day trial available).
2. **Configuration:** Use `warehouse_configs/snowflake/profiles.yml`.
3. **Data Loading:** Use the provided Snowflake loading script (coming soon) or use Snowflake's S3/GCS integration.
4. **dbt:** Run `dbt build --profile snowflake_profile`.

## 🧱 Databricks Deployment
1. **Setup:** Create a Databricks workspace.
2. **Configuration:** Use `warehouse_configs/databricks/profiles.yml`.
3. **Data Loading:** Upload CSVs to DBFS or Unity Catalog.
4. **dbt:** Run `dbt build --profile databricks_profile`.

## 🐘 Supabase (Postgres)
1. **Setup:** Create a Supabase project.
2. **Loading:** Run `python scripts/load_supabase.py`.
3. **dbt:** Run `dbt build --target supabase`.
