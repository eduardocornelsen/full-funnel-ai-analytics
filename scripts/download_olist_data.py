"""
Download the Olist Brazilian E-Commerce dataset from Kaggle.
Requires: pip install kaggle
Set KAGGLE_USERNAME and KAGGLE_KEY in ~/.kaggle/kaggle.json
"""
import os
import subprocess
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "olist"
DATA_DIR.mkdir(parents=True, exist_ok=True)

EXPECTED_FILES = [
    "olist_customers_dataset.csv",
    "olist_orders_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_products_dataset.csv",
    "olist_sellers_dataset.csv",
    "olist_geolocation_dataset.csv",
    "product_category_name_translation.csv",
]

def download():
    print("=== Downloading Olist E-Commerce Dataset ===\n")

    existing = [f.name for f in DATA_DIR.glob("*.csv")]
    if all(f in existing for f in EXPECTED_FILES):
        print("All files already present. Skipping download.")
    else:
        try:
            subprocess.run(
                ["kaggle", "datasets", "download", "-d", "olistbr/brazilian-ecommerce",
                 "-p", str(DATA_DIR), "--unzip"],
                check=True,
            )
            print("Downloaded via Kaggle CLI")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Kaggle CLI failed. Download manually from:")
            print("  https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce")
            print(f"  Extract all CSVs to: {DATA_DIR}")
            return

    # Verify and report
    files = sorted(DATA_DIR.glob("*.csv"))
    print(f"\n{len(files)} files in {DATA_DIR}:")
    for f in files:
        import csv
        with open(f) as fh:
            rows = sum(1 for _ in fh) - 1
        size_mb = f.stat().st_size / 1e6
        print(f"  {f.name}: {rows:,} rows ({size_mb:.1f} MB)")

    missing = [f for f in EXPECTED_FILES if f not in [x.name for x in files]]
    if missing:
        print(f"\nWARNING: Missing files: {missing}")
    else:
        print("\n=== All 9 Olist files present ===")

if __name__ == "__main__":
    download()
