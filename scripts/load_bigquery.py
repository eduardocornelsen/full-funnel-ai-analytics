"""Load all Olist + mock marketing data into BigQuery free tier."""
import os
from pathlib import Path
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
DATASET_ID = "olist_analytics"
DATA_DIR = Path(__file__).parent.parent / "data"

def get_client():
    return bigquery.Client(project=PROJECT_ID)

def create_dataset(client):
    dataset = bigquery.Dataset(f"{PROJECT_ID}.{DATASET_ID}")
    dataset.location = "US"
    client.create_dataset(dataset, exists_ok=True)
    print(f"Dataset {PROJECT_ID}.{DATASET_ID} ready")

def load_csv(client, filepath, table_name, schema=None):
    """Load a CSV file into BigQuery."""
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=True if schema is None else False,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    if schema:
        job_config.schema = schema

    with open(filepath, "rb") as f:
        job = client.load_table_from_file(f, table_id, job_config=job_config)
        job.result()
    table = client.get_table(table_id)
    print(f"  {table_name}: {table.num_rows:,} rows")

def main():
    print("=== Loading All Data into BigQuery ===\n")
    if not PROJECT_ID:
        print("ERROR: GCP_PROJECT_ID not set in .env")
        return
        
    client = get_client()
    create_dataset(client)

    # Olist tables
    olist_dir = DATA_DIR / "olist"
    olist_tables = {
        "olist_customers_dataset.csv": "customers",
        "olist_orders_dataset.csv": "orders",
        "olist_order_items_dataset.csv": "order_items",
        "olist_order_payments_dataset.csv": "order_payments",
        "olist_order_reviews_dataset.csv": "order_reviews",
        "olist_products_dataset.csv": "products",
        "olist_sellers_dataset.csv": "sellers",
        "olist_geolocation_dataset.csv": "geolocation",
        "product_category_name_translation.csv": "category_translation",
    }
    print("Olist tables:")
    for filename, table_name in olist_tables.items():
        filepath = olist_dir / filename
        if filepath.exists():
            load_csv(client, filepath, table_name)
        else:
            print(f"  SKIP: {filename} not found")

    # Mock marketing tables
    mock_dir = DATA_DIR / "mock_marketing"
    print("\nMarketing tables:")
    if mock_dir.exists():
        for csv_file in sorted(mock_dir.glob("*.csv")):
            table_name = csv_file.stem  # filename without extension
            load_csv(client, csv_file, table_name)
    else:
        print("  SKIP: mock_marketing directory not found")

    print("\n=== BigQuery loading complete ===")

if __name__ == "__main__":
    main()
