"""
connector_registry.py
──────────────────────────────────────────────────────────────────────────────
Lightweight connection factory used by the Streamlit connector UI and CLI scripts.
Persists connection config to ~/.full_funnel_connectors.json (never inside the repo).
"""

import json
import os
from pathlib import Path
from typing import Any

import pandas as pd

_CONFIG_PATH = Path.home() / ".full_funnel_connectors.json"
_PROJECT_ROOT = Path(__file__).parent.parent.parent

# Default DuckDB path for local dev
_DUCKDB_DEFAULT = str(_PROJECT_ROOT / "data" / "olist_analytics.duckdb")


def load_config() -> dict:
    if _CONFIG_PATH.exists():
        return json.loads(_CONFIG_PATH.read_text())
    return {"active": "duckdb", "connections": {}}


def save_config(cfg: dict) -> None:
    _CONFIG_PATH.write_text(json.dumps(cfg, indent=2))


def get_active_target() -> str:
    return load_config().get("active", "duckdb")


def test_connection(target: str, params: dict) -> tuple[bool, str]:
    """
    Try a lightweight SELECT 1 against the given target.
    Returns (success: bool, message: str).
    """
    try:
        if target == "duckdb":
            import duckdb
            db_path = params.get("path", _DUCKDB_DEFAULT)
            con = duckdb.connect(db_path, read_only=True)
            con.execute("SELECT 1").fetchone()
            con.close()
            return True, f"Connected to DuckDB: {db_path}"

        if target == "bigquery":
            from google.cloud import bigquery
            project = params["project"]
            client = bigquery.Client(project=project)
            list(client.query("SELECT 1").result())
            return True, f"Connected to BigQuery project: {project}"

        if target == "snowflake":
            import snowflake.connector
            con = snowflake.connector.connect(
                account=params["account"],
                user=params["user"],
                password=params["password"],
                warehouse=params.get("warehouse", ""),
                database=params.get("database", ""),
                schema=params.get("schema", "PUBLIC"),
            )
            cur = con.cursor()
            cur.execute("SELECT 1")
            cur.close()
            con.close()
            return True, f"Connected to Snowflake account: {params['account']}"

        return False, f"Unknown target: {target}"
    except Exception as exc:
        return False, f"Connection failed: {exc}"


def save_connection(target: str, params: dict, set_active: bool = False) -> None:
    cfg = load_config()
    cfg.setdefault("connections", {})[target] = params
    if set_active:
        cfg["active"] = target
    save_config(cfg)


def preview_table(target: str, table: str, limit: int = 20) -> pd.DataFrame:
    """Return the first `limit` rows of a table from the active connection."""
    cfg = load_config()
    params = cfg.get("connections", {}).get(target, {})

    if target == "duckdb":
        import duckdb
        db_path = params.get("path", _DUCKDB_DEFAULT)
        con = duckdb.connect(db_path, read_only=True)
        df = con.execute(f"SELECT * FROM {table} LIMIT {limit}").df()
        con.close()
        return df

    if target == "bigquery":
        from google.cloud import bigquery
        project = params.get("project", os.environ.get("GCP_PROJECT_ID", ""))
        client = bigquery.Client(project=project)
        return client.query(
            f"SELECT * FROM `{project}.olist_analytics.{table}` LIMIT {limit}"
        ).to_dataframe()

    if target == "snowflake":
        import snowflake.connector
        con = snowflake.connector.connect(**{
            "account": params.get("account", ""),
            "user": params.get("user", ""),
            "password": params.get("password", ""),
            "warehouse": params.get("warehouse", ""),
            "database": params.get("database", ""),
            "schema": params.get("schema", "PUBLIC"),
        })
        cur = con.cursor()
        cur.execute(f"SELECT * FROM {table} LIMIT {limit}")
        cols = [d[0] for d in cur.description]
        df = pd.DataFrame(cur.fetchall(), columns=cols)
        cur.close()
        con.close()
        return df

    raise ValueError(f"Unknown target: {target}")
