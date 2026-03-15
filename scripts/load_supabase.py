"""Load subset of data into Supabase Postgres (500MB free tier)."""
import os
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv
from pathlib import Path
from tqdm import tqdm

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
DATA_DIR = Path(__file__).parent.parent / "data"

SQL_SETUP = """
-- Run this in Supabase SQL Editor FIRST:

CREATE TABLE IF NOT EXISTS orders (
    order_id VARCHAR PRIMARY KEY,
    customer_id VARCHAR,
    order_status VARCHAR,
    order_purchase_timestamp TIMESTAMPTZ,
    order_approved_at TIMESTAMPTZ,
    order_delivered_carrier_date TIMESTAMPTZ,
    order_delivered_customer_date TIMESTAMPTZ,
    order_estimated_delivery_date TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS order_items (
    order_id VARCHAR,
    order_item_id INTEGER,
    product_id VARCHAR,
    seller_id VARCHAR,
    shipping_limit_date TIMESTAMPTZ,
    price NUMERIC(10,2),
    freight_value NUMERIC(10,2)
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR PRIMARY KEY,
    customer_unique_id VARCHAR,
    customer_zip_code_prefix VARCHAR,
    customer_city VARCHAR,
    customer_state VARCHAR
);

CREATE TABLE IF NOT EXISTS hubspot_contacts (
    contact_id VARCHAR PRIMARY KEY,
    customer_id VARCHAR,
    email VARCHAR,
    first_name VARCHAR,
    last_name VARCHAR,
    city VARCHAR,
    state VARCHAR,
    create_date DATE,
    lifecycle_stage VARCHAR,
    lead_source VARCHAR,
    num_orders INTEGER,
    total_revenue NUMERIC(10,2),
    first_order_date DATE,
    last_activity_date DATE
);

CREATE TABLE IF NOT EXISTS marketing_attribution (
    order_id VARCHAR,
    touchpoint_position INTEGER,
    total_touchpoints INTEGER,
    channel VARCHAR,
    platform VARCHAR,
    touchpoint_date DATE,
    order_date DATE,
    order_revenue NUMERIC(10,2),
    first_touch_credit NUMERIC(6,4),
    last_touch_credit NUMERIC(6,4),
    linear_credit NUMERIC(6,4)
);
"""

def main():
    print("=== Loading Data into Supabase ===\n")
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERROR: SUPABASE_URL or SUPABASE_KEY not set in .env")
        return
        
    print("IMPORTANT: First run this SQL in Supabase SQL Editor:")
    print(SQL_SETUP)
    # Removing input blocking for non-interactive execution, assuming user handles tables
    # input("\nPress Enter after creating tables in Supabase...")

    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    batch_size = 500

    # Load orders (sample for free tier)
    olist_orders_path = DATA_DIR / "olist" / "olist_orders_dataset.csv"
    if olist_orders_path.exists():
        print("Loading orders...")
        df = pd.read_csv(olist_orders_path)
        df = df.head(50000)  # Sample for 500MB limit
        df = df.where(df.notna(), None)
        for i in tqdm(range(0, len(df), batch_size)):
            batch = df.iloc[i:i+batch_size].to_dict(orient="records")
            try:
                client.table("orders").upsert(batch).execute()
            except Exception as e:
                print(f"  Error at row {i}: {e}")
    else:
        print("  SKIP: olist_orders_dataset.csv not found")

    # Load customers
    olist_customers_path = DATA_DIR / "olist" / "olist_customers_dataset.csv"
    if olist_customers_path.exists():
        print("Loading customers...")
        df = pd.read_csv(olist_customers_path)
        df = df.where(df.notna(), None)
        for i in tqdm(range(0, len(df), batch_size)):
            batch = df.iloc[i:i+batch_size].to_dict(orient="records")
            try:
                client.table("customers").upsert(batch).execute()
            except Exception as e:
                pass
    else:
        print("  SKIP: olist_customers_dataset.csv not found")

    # Load hubspot contacts
    hubspot_contacts_path = DATA_DIR / "mock_marketing" / "hubspot_contacts.csv"
    if hubspot_contacts_path.exists():
        print("Loading HubSpot contacts...")
        df = pd.read_csv(hubspot_contacts_path)
        df = df.head(50000)
        df = df.where(df.notna(), None)
        for i in tqdm(range(0, len(df), batch_size)):
            batch = df.iloc[i:i+batch_size].to_dict(orient="records")
            try:
                client.table("hubspot_contacts").upsert(batch).execute()
            except Exception as e:
                pass
    else:
        print("  SKIP: hubspot_contacts.csv not found")

    # Load attribution
    attribution_path = DATA_DIR / "mock_marketing" / "marketing_attribution.csv"
    if attribution_path.exists():
        print("Loading attribution...")
        df = pd.read_csv(attribution_path)
        df = df.head(100000)
        df = df.where(df.notna(), None)
        for i in tqdm(range(0, len(df), batch_size)):
            batch = df.iloc[i:i+batch_size].to_dict(orient="records")
            try:
                client.table("marketing_attribution").insert(batch).execute()
            except Exception as e:
                pass
    else:
        print("  SKIP: marketing_attribution.csv not found")

    print("\n=== Supabase loading complete ===")

if __name__ == "__main__":
    main()
