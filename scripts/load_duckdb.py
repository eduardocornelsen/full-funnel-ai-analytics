"""Set up local DuckDB database with all Olist + mock marketing data."""
import duckdb
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "olist_analytics.duckdb"
DATA_DIR = Path(__file__).parent.parent / "data"

def setup():
    print("=== Setting up DuckDB ===\n")
    con = duckdb.connect(str(DB_PATH))

    # Load Olist CSVs
    olist_dir = DATA_DIR / "olist"
    print("Olist tables:")
    if olist_dir.exists():
        for csv_file in sorted(olist_dir.glob("*.csv")):
            table_name = csv_file.stem.replace("olist_", "").replace("_dataset", "")
            con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM read_csv_auto('{csv_file}')")
            count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            print(f"  {table_name}: {count:,} rows")
    else:
        print("  SKIP: olist directory not found")

    # Load mock marketing CSVs
    mock_dir = DATA_DIR / "mock_marketing"
    print("\nMarketing tables:")
    if mock_dir.exists():
        for csv_file in sorted(mock_dir.glob("*.csv")):
            table_name = csv_file.stem
            con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM read_csv_auto('{csv_file}')")
            count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            print(f"  {table_name}: {count:,} rows")
    else:
        print("  SKIP: mock_marketing directory not found")

    con.close()
    print(f"\nDatabase saved: {DB_PATH}")
    print("=== DuckDB setup complete ===")

if __name__ == "__main__":
    setup()
