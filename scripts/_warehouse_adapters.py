"""
_warehouse_adapters.py
──────────────────────────────────────────────────────────────────────────────
Thin connection adapters that present a uniform `.execute(sql, params)` API
for DuckDB, BigQuery, and Snowflake.

Used by generate_golden_metrics.py and validate_metrics.py.
Not meant to be run directly.
"""

import os
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "olist_analytics.duckdb"

# All dbt model names that need schema-prefixing in cloud warehouses
_DBT_TABLES = [
    "fct_marketing_daily", "fct_channel_performance", "fct_marketing_attribution",
    "fct_pipeline", "fct_daily_revenue", "fct_orders",
    "stg_google_ads_performance", "stg_meta_ads_performance", "stg_ga4_sessions",
    "stg_marketing_attribution", "stg_hubspot_contacts", "stg_hubspot_deals",
    "stg_salesforce_opportunities",
]


class _ResultProxy:
    """Mimics DuckDB result object so all callers can use .fetchone()/.fetchall()."""

    def __init__(self, rows):
        self._rows = rows

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return self._rows


class _BigQueryAdapter:
    def __init__(self):
        from google.cloud import bigquery  # noqa: PLC0415
        project = os.environ["GCP_PROJECT_ID"]
        self._client = bigquery.Client(project=project)
        self._prefix = f"`{project}.olist_analytics`"

    def _prep(self, sql: str, params) -> str:
        if params:
            for p in params:
                sql = sql.replace("?", f"'{p}'", 1)
        for t in _DBT_TABLES:
            sql = re.sub(rf"(?<![.`])\b{t}\b", f"{self._prefix}.{t}", sql)
        return sql

    def execute(self, sql: str, params=None) -> _ResultProxy:
        rows = list(self._client.query(self._prep(sql, params)).result())
        return _ResultProxy([tuple(v for v in r.values()) for r in rows])

    def close(self):
        pass


class _SnowflakeAdapter:
    def __init__(self):
        import snowflake.connector  # noqa: PLC0415
        self._con = snowflake.connector.connect(
            account=os.environ["SNOWFLAKE_ACCOUNT"],
            user=os.environ["SNOWFLAKE_USER"],
            password=os.environ["SNOWFLAKE_PASSWORD"],
            warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE", "ANALYTICS_WH"),
            database=os.environ.get("SNOWFLAKE_DATABASE", "OLIST_ANALYTICS"),
            schema=os.environ.get("SNOWFLAKE_SCHEMA", "PUBLIC"),
        )
        self._cur = self._con.cursor()

    def execute(self, sql: str, params=None) -> _ResultProxy:
        self._cur.execute(sql, params or [])
        return _ResultProxy(self._cur.fetchall())

    def close(self):
        self._cur.close()
        self._con.close()


def get_connection(target: str = "duckdb"):
    """Return a connection adapter for the given dbt target.

    DuckDB returns a native duckdb connection (already has .execute().fetchone()).
    BigQuery and Snowflake return adapter wrappers with the same interface.
    """
    if target == "duckdb":
        import duckdb  # noqa: PLC0415
        return duckdb.connect(str(DB_PATH), read_only=True)
    if target == "bigquery":
        return _BigQueryAdapter()
    if target == "snowflake":
        return _SnowflakeAdapter()
    raise ValueError(f"Unknown target: {target!r}. Valid: duckdb, bigquery, snowflake")
