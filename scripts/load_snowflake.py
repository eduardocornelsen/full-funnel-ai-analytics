"""Load all Olist + mock marketing CSVs into Snowflake (raw schema).

Same tables and names as load_duckdb.py, so the dbt sources resolve on both
engines. Every table is replaced on each run (overwrite), so a rerun after a
failure is safe and the warehouse always holds exactly the committed CSVs.
That matters for the parity check: Snowflake must see the same universe the
golden layer was generated from on DuckDB.

Credentials come only from the environment:
    SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD (or
    SNOWFLAKE_PRIVATE_KEY_PATH), SNOWFLAKE_ROLE, SNOWFLAKE_WAREHOUSE,
    SNOWFLAKE_DATABASE, SNOWFLAKE_RAW_SCHEMA (default RAW)

Usage:
    python scripts/load_snowflake.py            # load everything
    python scripts/load_snowflake.py --dry-run  # list what would load
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path(__file__).parent.parent / "data"
DEFAULT_RAW_SCHEMA = "RAW"


def table_name_for(csv_file: Path) -> str:
    """Mirror load_duckdb.py naming: olist_orders_dataset.csv -> orders."""
    stem = csv_file.stem
    if csv_file.parent.name == "olist":
        stem = stem.replace("olist_", "").replace("_dataset", "")
    return stem


def discover_csvs(data_dir: Path | None = None) -> list[tuple[Path, str]]:
    """Every CSV the dbt sources read, paired with its target table name."""
    data_dir = data_dir or DATA_DIR
    found: list[tuple[Path, str]] = []
    for sub in ("olist", "mock_marketing"):
        folder = data_dir / sub
        if not folder.exists():
            print(f"  SKIP: {folder} not found")
            continue
        for csv_file in sorted(folder.glob("*.csv")):
            found.append((csv_file, table_name_for(csv_file)))
    return found


def connect():
    """Open a Snowflake connection from env vars; fail with the missing names."""
    import snowflake.connector  # noqa: PLC0415

    required = ["SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_WAREHOUSE", "SNOWFLAKE_DATABASE"]
    missing = [k for k in required if not os.environ.get(k)]
    if not (os.environ.get("SNOWFLAKE_PASSWORD") or os.environ.get("SNOWFLAKE_PRIVATE_KEY_PATH")):
        missing.append("SNOWFLAKE_PASSWORD or SNOWFLAKE_PRIVATE_KEY_PATH")
    if missing:
        sys.exit(f"ERROR: missing environment variables: {', '.join(missing)}")

    kwargs = {
        "account": os.environ["SNOWFLAKE_ACCOUNT"],
        "user": os.environ["SNOWFLAKE_USER"],
        "warehouse": os.environ["SNOWFLAKE_WAREHOUSE"],
        "database": os.environ["SNOWFLAKE_DATABASE"],
        "schema": (os.environ.get("SNOWFLAKE_RAW_SCHEMA") or DEFAULT_RAW_SCHEMA),
    }
    if os.environ.get("SNOWFLAKE_ROLE"):
        kwargs["role"] = os.environ["SNOWFLAKE_ROLE"]
    if os.environ.get("SNOWFLAKE_PRIVATE_KEY_PATH"):
        kwargs["private_key_file"] = os.environ["SNOWFLAKE_PRIVATE_KEY_PATH"]
    else:
        kwargs["password"] = os.environ["SNOWFLAKE_PASSWORD"]
    return snowflake.connector.connect(**kwargs)


def load_table(con, csv_file: Path, table: str, schema: str) -> int:
    """Replace one table with the CSV's contents and return its row count."""
    from snowflake.connector.pandas_tools import write_pandas  # noqa: PLC0415

    # Read everything the CSV has; dates stay as strings and dbt staging casts
    # them, exactly as it does on DuckDB.
    df = pd.read_csv(csv_file, low_memory=False)
    # Unquoted upper-case identifiers, so dbt's lower-case unquoted SQL resolves.
    df.columns = [c.upper() for c in df.columns]
    ok, _, nrows, _ = write_pandas(
        con, df, table_name=table.upper(), schema=schema.upper(),
        auto_create_table=True, overwrite=True, quote_identifiers=False,
    )
    if not ok:
        raise RuntimeError(f"write_pandas reported failure for {table}")
    return int(nrows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true", help="list what would load and exit")
    args = parser.parse_args(argv)

    csvs = discover_csvs()
    schema = (os.environ.get("SNOWFLAKE_RAW_SCHEMA") or DEFAULT_RAW_SCHEMA)
    print(f"=== Loading {len(csvs)} CSVs into Snowflake schema {schema} ===\n")

    if args.dry_run:
        for csv_file, table in csvs:
            print(f"  {csv_file.relative_to(DATA_DIR)} -> {schema}.{table.upper()}")
        return 0

    con = connect()
    try:
        con.cursor().execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
        for csv_file, table in csvs:
            try:
                n = load_table(con, csv_file, table, schema)
            except Exception as exc:  # fail loudly, naming the table
                print(f"  ❌ {table}: {exc}")
                return 1
            print(f"  {table}: {n:,} rows")
    finally:
        con.close()
    print("\n=== Snowflake loading complete ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
