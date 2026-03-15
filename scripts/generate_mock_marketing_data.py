"""
Generate realistic synthetic marketing data anchored to real Olist orders.
Creates: Google Ads, Meta Ads, GA4, HubSpot, Salesforce, and Attribution data.

Run AFTER downloading Olist data: python scripts/download_olist_data.py
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import json
import csv

DATA_DIR = Path(__file__).parent.parent / "data"
OLIST_DIR = DATA_DIR / "olist"
MOCK_DIR = DATA_DIR / "mock_marketing"
MOCK_DIR.mkdir(parents=True, exist_ok=True)

np.random.seed(42)


def load_orders():
    """Load delivered Olist orders with revenue."""
    orders = pd.read_csv(OLIST_DIR / "olist_orders_dataset.csv")
    orders["order_purchase_timestamp"] = pd.to_datetime(orders["order_purchase_timestamp"])
    payments = pd.read_csv(OLIST_DIR / "olist_order_payments_dataset.csv")
    order_revenue = payments.groupby("order_id")["payment_value"].sum().reset_index()
    order_revenue.columns = ["order_id", "revenue"]
    orders = orders.merge(order_revenue, on="order_id", how="left")
    orders = orders[orders["order_status"] == "delivered"].copy()
    orders = orders.sort_values("order_purchase_timestamp").reset_index(drop=True)
    print(f"Loaded {len(orders):,} delivered orders")
    return orders


def generate_google_ads(orders):
    """Google Ads: campaigns, ad groups, keywords, daily performance."""
    print("\nGenerating Google Ads data...")

    campaigns = [
        {"campaign_id": "C001", "campaign_name": "Brand - Olist", "campaign_type": "SEARCH", "daily_budget": 150.0},
        {"campaign_id": "C002", "campaign_name": "Generic - Electronics", "campaign_type": "SEARCH", "daily_budget": 300.0},
        {"campaign_id": "C003", "campaign_name": "Generic - Home & Garden", "campaign_type": "SEARCH", "daily_budget": 250.0},
        {"campaign_id": "C004", "campaign_name": "Shopping - All Products", "campaign_type": "SHOPPING", "daily_budget": 400.0},
        {"campaign_id": "C005", "campaign_name": "Display - Retargeting", "campaign_type": "DISPLAY", "daily_budget": 200.0},
        {"campaign_id": "C006", "campaign_name": "YouTube - Brand Awareness", "campaign_type": "VIDEO", "daily_budget": 100.0},
    ]

    ad_groups = [
        {"ad_group_id": "AG001", "campaign_id": "C001", "ad_group_name": "Olist Exact Match"},
        {"ad_group_id": "AG002", "campaign_id": "C001", "ad_group_name": "Olist Broad Match"},
        {"ad_group_id": "AG003", "campaign_id": "C002", "ad_group_name": "Electronics - General"},
        {"ad_group_id": "AG004", "campaign_id": "C002", "ad_group_name": "Electronics - Smartphones"},
        {"ad_group_id": "AG005", "campaign_id": "C003", "ad_group_name": "Home Decor"},
        {"ad_group_id": "AG006", "campaign_id": "C003", "ad_group_name": "Kitchen Appliances"},
        {"ad_group_id": "AG007", "campaign_id": "C004", "ad_group_name": "Shopping - Best Sellers"},
        {"ad_group_id": "AG008", "campaign_id": "C005", "ad_group_name": "Cart Abandoners"},
        {"ad_group_id": "AG009", "campaign_id": "C005", "ad_group_name": "Past Purchasers"},
        {"ad_group_id": "AG010", "campaign_id": "C006", "ad_group_name": "Brand Video - 30s"},
    ]

    keywords = [
        {"keyword_id": "KW001", "ad_group_id": "AG001", "keyword": "olist", "match_type": "EXACT"},
        {"keyword_id": "KW002", "ad_group_id": "AG001", "keyword": "olist store", "match_type": "EXACT"},
        {"keyword_id": "KW003", "ad_group_id": "AG002", "keyword": "olist marketplace", "match_type": "BROAD"},
        {"keyword_id": "KW004", "ad_group_id": "AG003", "keyword": "buy electronics online brazil", "match_type": "PHRASE"},
        {"keyword_id": "KW005", "ad_group_id": "AG003", "keyword": "cheap electronics", "match_type": "BROAD"},
        {"keyword_id": "KW006", "ad_group_id": "AG004", "keyword": "smartphone deals", "match_type": "PHRASE"},
        {"keyword_id": "KW007", "ad_group_id": "AG005", "keyword": "home decor online", "match_type": "BROAD"},
        {"keyword_id": "KW008", "ad_group_id": "AG005", "keyword": "furniture online brazil", "match_type": "PHRASE"},
        {"keyword_id": "KW009", "ad_group_id": "AG006", "keyword": "kitchen appliances", "match_type": "BROAD"},
        {"keyword_id": "KW010", "ad_group_id": "AG006", "keyword": "small kitchen appliances", "match_type": "PHRASE"},
    ]

    date_range = pd.date_range("2017-01-01", "2018-08-31")
    daily_perf = []

    for date in date_range:
        month_factor = {1: 0.7, 2: 0.85, 3: 0.95, 4: 1.0, 5: 1.2, 6: 1.2, 
                        7: 1.0, 8: 0.95, 9: 1.0, 10: 1.1, 11: 1.8, 12: 1.4}.get(date.month, 1.0)
        dow_factor = 0.8 if date.weekday() >= 5 else 1.0

        for camp in campaigns:
            base_imp = {"SEARCH": 5000, "SHOPPING": 8000, "DISPLAY": 20000, "VIDEO": 15000}[camp["campaign_type"]]
            impressions = int(base_imp * month_factor * dow_factor * np.random.uniform(0.7, 1.3))

            ctr = {"SEARCH": 0.035, "SHOPPING": 0.02, "DISPLAY": 0.005, "VIDEO": 0.012}[camp["campaign_type"]] * np.random.uniform(0.8, 1.2)
            clicks = int(impressions * ctr)

            cpc = {"SEARCH": 0.85, "SHOPPING": 0.45, "DISPLAY": 0.25, "VIDEO": 0.15}[camp["campaign_type"]] * np.random.uniform(0.7, 1.4) * month_factor
            cost = round(min(clicks * cpc, camp["daily_budget"] * np.random.uniform(0.9, 1.1)), 2)

            conv_rate = {"SEARCH": 0.028, "SHOPPING": 0.022, "DISPLAY": 0.008, "VIDEO": 0.003}[camp["campaign_type"]] * np.random.uniform(0.6, 1.5)
            conversions = int(clicks * conv_rate)
            conv_value = round(conversions * np.random.uniform(80, 250), 2)

            daily_perf.append({
                "date": date.strftime("%Y-%m-%d"),
                "campaign_id": camp["campaign_id"],
                "campaign_name": camp["campaign_name"],
                "campaign_type": camp["campaign_type"],
                "impressions": impressions,
                "clicks": clicks,
                "cost": cost,
                "conversions": conversions,
                "conversion_value": conv_value,
                "ctr": round(ctr * 100, 2),
                "avg_cpc": round(cost / max(clicks, 1), 2),
                "cost_per_conversion": round(cost / max(conversions, 1), 2),
                "roas": round(conv_value / max(cost, 0.01), 2),
            })

    pd.DataFrame(campaigns).to_csv(MOCK_DIR / "google_ads_campaigns.csv", index=False)
    pd.DataFrame(ad_groups).to_csv(MOCK_DIR / "google_ads_ad_groups.csv", index=False)
    pd.DataFrame(keywords).to_csv(MOCK_DIR / "google_ads_keywords.csv", index=False)
    pd.DataFrame(daily_perf).to_csv(MOCK_DIR / "google_ads_daily_performance.csv", index=False)
    print(f"  {len(campaigns)} campaigns, {len(ad_groups)} ad groups, {len(keywords)} keywords, {len(daily_perf):,} daily rows")


def generate_meta_ads(orders):
    """Meta (Facebook/Instagram) Ads: campaigns, ad sets, daily performance."""
    print("\nGenerating Meta Ads data...")

    campaigns = [
        {"campaign_id": "META_C001", "campaign_name": "Prospecting - Lookalike Purchasers", "objective": "CONVERSIONS", "daily_budget": 250.0},
        {"campaign_id": "META_C002", "campaign_name": "Retargeting - Add to Cart", "objective": "CONVERSIONS", "daily_budget": 150.0},
        {"campaign_id": "META_C003", "campaign_name": "Brand Awareness - Video", "objective": "AWARENESS", "daily_budget": 100.0},
        {"campaign_id": "META_C004", "campaign_name": "Catalog Sales - Dynamic", "objective": "CATALOG_SALES", "daily_budget": 300.0},
        {"campaign_id": "META_C005", "campaign_name": "Instagram Stories - Flash Sales", "objective": "CONVERSIONS", "daily_budget": 200.0},
    ]

    ad_sets = [
        {"ad_set_id": "AS001", "campaign_id": "META_C001", "ad_set_name": "LAL 1% - Purchasers", "targeting": "lookalike_1pct", "placement": "facebook_feed"},
        {"ad_set_id": "AS002", "campaign_id": "META_C001", "ad_set_name": "LAL 3% - Purchasers", "targeting": "lookalike_3pct", "placement": "facebook_feed"},
        {"ad_set_id": "AS003", "campaign_id": "META_C001", "ad_set_name": "Interest - Electronics", "targeting": "interest_electronics", "placement": "instagram_feed"},
        {"ad_set_id": "AS004", "campaign_id": "META_C002", "ad_set_name": "Cart Abandoners 7d", "targeting": "retarget_cart_7d", "placement": "facebook_feed"},
        {"ad_set_id": "AS005", "campaign_id": "META_C002", "ad_set_name": "Viewed Product 14d", "targeting": "retarget_viewed_14d", "placement": "instagram_stories"},
        {"ad_set_id": "AS006", "campaign_id": "META_C003", "ad_set_name": "Broad - 18-45 Brazil", "targeting": "broad_18_45", "placement": "facebook_video"},
        {"ad_set_id": "AS007", "campaign_id": "META_C004", "ad_set_name": "Dynamic - All Products", "targeting": "catalog_dynamic", "placement": "facebook_feed"},
        {"ad_set_id": "AS008", "campaign_id": "META_C005", "ad_set_name": "Stories - Weekend Deals", "targeting": "interest_shopping", "placement": "instagram_stories"},
    ]

    date_range = pd.date_range("2017-01-01", "2018-08-31")
    daily_perf = []

    for date in date_range:
        month_factor = {1: 0.6, 5: 1.1, 6: 1.1, 11: 2.0, 12: 1.5}.get(date.month, 1.0)
        
        for camp in campaigns:
            impressions = int(np.random.uniform(8000, 30000) * month_factor)
            reach = int(impressions * np.random.uniform(0.6, 0.85))
            cpm = np.random.uniform(4.0, 12.0) * month_factor
            spend = round(min((impressions / 1000) * cpm, camp["daily_budget"] * np.random.uniform(0.85, 1.05)), 2)
            link_clicks = int(impressions * np.random.uniform(0.008, 0.025))
            purchases = int(link_clicks * np.random.uniform(0.01, 0.06))
            purchase_value = round(purchases * np.random.uniform(90, 200), 2)

            daily_perf.append({
                "date": date.strftime("%Y-%m-%d"),
                "campaign_id": camp["campaign_id"],
                "campaign_name": camp["campaign_name"],
                "objective": camp["objective"],
                "impressions": impressions, "reach": reach, "spend": spend,
                "link_clicks": link_clicks, 
                "ctr": round((link_clicks / max(impressions, 1)) * 100, 2),
                "cpc": round(spend / max(link_clicks, 1), 2),
                "cpm": round(cpm, 2),
                "purchases": purchases, "purchase_value": purchase_value,
                "cost_per_purchase": round(spend / max(purchases, 1), 2),
                "roas": round(purchase_value / max(spend, 0.01), 2),
            })

    pd.DataFrame(campaigns).to_csv(MOCK_DIR / "meta_ads_campaigns.csv", index=False)
    pd.DataFrame(ad_sets).to_csv(MOCK_DIR / "meta_ads_ad_sets.csv", index=False)
    pd.DataFrame(daily_perf).to_csv(MOCK_DIR / "meta_ads_daily_performance.csv", index=False)
    print(f"  {len(campaigns)} campaigns, {len(ad_sets)} ad sets, {len(daily_perf):,} daily rows")


def generate_ga4(orders):
    """GA4 website sessions by channel, device, and day."""
    print("\nGenerating GA4 data...")

    channels = ["organic_search", "paid_search", "paid_social", "direct", "email", "referral", "organic_social"]
    channel_weights = [0.25, 0.20, 0.18, 0.15, 0.10, 0.07, 0.05]
    devices = ["mobile", "desktop", "tablet"]
    device_weights = [0.55, 0.35, 0.10]

    bounce_rates = {"organic_search": 0.45, "paid_search": 0.38, "paid_social": 0.55, 
                    "direct": 0.30, "email": 0.25, "referral": 0.50, "organic_social": 0.60}
    conv_rates = {"organic_search": 0.025, "paid_search": 0.032, "paid_social": 0.018, 
                  "direct": 0.035, "email": 0.042, "referral": 0.020, "organic_social": 0.012}

    date_range = pd.date_range("2017-01-01", "2018-08-31")
    rows = []

    for date in date_range:
        month_factor = {1: 0.7, 5: 1.1, 6: 1.1, 11: 1.9, 12: 1.4}.get(date.month, 1.0)
        dow_factor = 0.75 if date.weekday() >= 5 else 1.0

        for ch, cw in zip(channels, channel_weights):
            for dev, dw in zip(devices, device_weights):
                sessions = int(500 * cw * dw * month_factor * dow_factor * np.random.uniform(0.7, 1.3) * 10)
                br = bounce_rates[ch] * np.random.uniform(0.85, 1.15)
                engaged = int(sessions * (1 - br))
                conversions = int(sessions * conv_rates[ch] * np.random.uniform(0.7, 1.3))
                revenue = round(conversions * np.random.uniform(80, 220), 2)

                rows.append({
                    "date": date.strftime("%Y-%m-%d"), "channel_group": ch, "device_category": dev,
                    "sessions": sessions, "engaged_sessions": engaged,
                    "bounce_rate": round(br * 100, 1),
                    "avg_session_duration_sec": round(np.random.uniform(60, 300) * (1 - br * 0.5), 0),
                    "pages_per_session": round(np.random.uniform(1.5, 6.0) * (1 - br * 0.3), 1),
                    "new_users": int(sessions * np.random.uniform(0.5, 0.8)),
                    "conversions": conversions, "revenue": revenue,
                    "conversion_rate": round((conversions / max(sessions, 1)) * 100, 2),
                })

    pd.DataFrame(rows).to_csv(MOCK_DIR / "ga4_daily_sessions.csv", index=False)
    print(f"  {len(rows):,} daily session rows")


def generate_hubspot(orders):
    """HubSpot contacts and deals linked to Olist customers/orders."""
    print("\nGenerating HubSpot data...")

    customers = pd.read_csv(OLIST_DIR / "olist_customers_dataset.csv")
    unique_customers = customers.drop_duplicates(subset="customer_unique_id")
    sources = ["organic_search", "paid_search", "paid_social", "direct", "email", "referral"]
    source_weights = [0.25, 0.22, 0.20, 0.15, 0.10, 0.08]
    first_names = ["ana", "bruno", "carla", "daniel", "elena", "fabio", "gabriela", "henrique", "isabela", "joao", 
                   "karen", "lucas", "maria", "nelson", "olivia", "pedro", "raquel", "sergio", "tatiana", "vitor"]
    last_names = ["silva", "santos", "oliveira", "souza", "lima", "pereira", "costa", "rodrigues", "almeida", "nascimento"]

    # Pre-group orders by customer_id for efficiency
    orders_by_customer = {k: v for k, v in orders.groupby("customer_id")}

    contacts = []
    for i, (_, cust) in enumerate(unique_customers.iterrows()):
        cust_id = cust["customer_id"]
        if cust_id not in orders_by_customer:
            continue
            
        cust_orders = orders_by_customer[cust_id]
        first_order = cust_orders.iloc[0]
        order_date = first_order["order_purchase_timestamp"]
        create_date = order_date - timedelta(days=np.random.randint(0, 31))
        source = np.random.choice(sources, p=source_weights)
        fname = np.random.choice(first_names)
        lname = np.random.choice(last_names)

        contacts.append({
            "contact_id": f"HS_{i+1:06d}",
            "customer_id": cust["customer_unique_id"],
            "email": f"{fname}.{lname}{np.random.randint(1,999)}@example.com",
            "first_name": fname.capitalize(), "last_name": lname.capitalize(),
            "city": cust["customer_city"], "state": cust["customer_state"],
            "create_date": create_date.strftime("%Y-%m-%d"),
            "lifecycle_stage": "customer",
            "lead_source": source,
            "num_orders": len(cust_orders),
            "total_revenue": round(cust_orders["revenue"].sum(), 2),
            "first_order_date": order_date.strftime("%Y-%m-%d"),
            "last_activity_date": cust_orders.iloc[-1]["order_purchase_timestamp"].strftime("%Y-%m-%d"),
        })

    print(f"  Generated {len(contacts):,} contacts")
    
    deals = []
    # Vectorized deal generation where possible
    for i, (_, order) in enumerate(orders.iterrows()):
        is_won = order["order_status"] == "delivered"
        deals.append({
            "deal_id": f"DEAL_{i+1:06d}", "order_id": order["order_id"],
            "deal_name": f"Order {order['order_id'][:8]}",
            "deal_stage": "closed_won" if is_won else np.random.choice(["qualified_to_buy", "presentation_scheduled", "negotiation"]),
            "pipeline": "default",
            "amount": round(order.get("revenue", 0), 2),
            "create_date": order["order_purchase_timestamp"].strftime("%Y-%m-%d"),
            "close_date": order["order_purchase_timestamp"].strftime("%Y-%m-%d") if is_won else "",
            "deal_type": "new_business",
            "lead_source": np.random.choice(sources, p=source_weights),
        })

    pd.DataFrame(contacts).to_csv(MOCK_DIR / "hubspot_contacts.csv", index=False)
    pd.DataFrame(deals).to_csv(MOCK_DIR / "hubspot_deals.csv", index=False)
    print(f"  {len(contacts):,} contacts, {len(deals):,} deals")


def generate_salesforce(orders):
    """Salesforce accounts (from sellers) and opportunities (from orders)."""
    print("\nGenerating Salesforce data...")

    sellers = pd.read_csv(OLIST_DIR / "olist_sellers_dataset.csv")
    accounts = []
    for i, (_, seller) in enumerate(sellers.iterrows()):
        accounts.append({
            "account_id": f"ACC_{i+1:05d}", "seller_id": seller["seller_id"],
            "account_name": f"Seller {seller['seller_id'][:8]}",
            "city": seller["seller_city"], "state": seller["seller_state"],
            "account_type": np.random.choice(["Standard", "Premium", "Enterprise"], p=[0.6, 0.3, 0.1]),
            "industry": np.random.choice(["Retail", "Electronics", "Fashion", "Home & Garden", "Sports", "Health & Beauty"]),
            "annual_revenue": round(np.random.uniform(50000, 2000000), 2),
            "num_employees": np.random.randint(1, 50),
        })

    stages = ["Prospecting", "Qualification", "Needs Analysis", "Value Proposition", "Negotiation", "Closed Won", "Closed Lost"]
    probability = {"Prospecting": 10, "Qualification": 25, "Needs Analysis": 40, "Value Proposition": 60, "Negotiation": 80, "Closed Won": 100, "Closed Lost": 0}
    opportunities = []
    for i, (_, order) in enumerate(orders.head(50000).iterrows()):
        is_won = order["order_status"] == "delivered"
        stage = "Closed Won" if is_won else np.random.choice(stages[:5])
        od = order["order_purchase_timestamp"]
        opportunities.append({
            "opportunity_id": f"OPP_{i+1:06d}", "order_id": order["order_id"],
            "opportunity_name": f"Deal {order['order_id'][:8]}",
            "stage": stage, "probability": probability[stage],
            "amount": round(order.get("revenue", 0), 2),
            "created_date": (od - timedelta(days=np.random.randint(0, 14))).strftime("%Y-%m-%d"),
            "close_date": od.strftime("%Y-%m-%d"),
            "lead_source": np.random.choice(["Web", "Paid Search", "Social Media", "Email", "Referral", "Direct"], p=[0.25, 0.20, 0.18, 0.15, 0.12, 0.10]),
            "type": "New Business",
            "fiscal_quarter": f"Q{(od.month - 1) // 3 + 1} {od.year}",
        })

    pd.DataFrame(accounts).to_csv(MOCK_DIR / "salesforce_accounts.csv", index=False)
    pd.DataFrame(opportunities).to_csv(MOCK_DIR / "salesforce_opportunities.csv", index=False)
    print(f"  {len(accounts):,} accounts, {len(opportunities):,} opportunities")


def generate_attribution(orders):
    """Multi-touch attribution table linking orders to marketing touchpoints."""
    print("\nGenerating attribution data...")

    channels = [
        {"channel": "google_ads_search", "platform": "google_ads", "weight": 0.25},
        {"channel": "google_ads_shopping", "platform": "google_ads", "weight": 0.15},
        {"channel": "meta_prospecting", "platform": "meta_ads", "weight": 0.18},
        {"channel": "meta_retargeting", "platform": "meta_ads", "weight": 0.10},
        {"channel": "organic_search", "platform": "ga4", "weight": 0.15},
        {"channel": "email_marketing", "platform": "hubspot", "weight": 0.08},
        {"channel": "direct", "platform": "ga4", "weight": 0.09},
    ]
    weights = [c["weight"] for c in channels]

    rows = []
    for _, order in orders.iterrows():
        num_touches = np.random.choice([1, 2, 3, 4], p=[0.3, 0.35, 0.25, 0.1])
        selected = np.random.choice(len(channels), size=min(num_touches, len(channels)), replace=False, p=weights)
        od = order["order_purchase_timestamp"]

        for touch_idx, ch_idx in enumerate(selected):
            ch = channels[ch_idx]
            touch_date = od - timedelta(days=np.random.randint(0, 14))
            rows.append({
                "order_id": order["order_id"],
                "touchpoint_position": touch_idx + 1,
                "total_touchpoints": len(selected),
                "channel": ch["channel"], "platform": ch["platform"],
                "touchpoint_date": touch_date.strftime("%Y-%m-%d"),
                "order_date": od.strftime("%Y-%m-%d"),
                "order_revenue": round(order.get("revenue", 0), 2),
                "first_touch_credit": 1.0 if touch_idx == 0 else 0.0,
                "last_touch_credit": 1.0 if touch_idx == len(selected) - 1 else 0.0,
                "linear_credit": round(1.0 / len(selected), 4),
            })

    pd.DataFrame(rows).to_csv(MOCK_DIR / "marketing_attribution.csv", index=False)
    print(f"  {len(rows):,} attribution rows")


def main():
    print("=" * 60)
    print("GENERATING MOCK MARKETING DATA")
    print("Anchored to real Olist e-commerce transactions")
    print("=" * 60)

    orders = load_orders()
    generate_google_ads(orders)
    generate_meta_ads(orders)
    generate_ga4(orders)
    generate_hubspot(orders)
    generate_salesforce(orders)
    generate_attribution(orders)

    print("\n" + "=" * 60)
    print(f"All mock data saved to: {MOCK_DIR}")
    for f in sorted(MOCK_DIR.glob("*.csv")):
        rows = sum(1 for _ in open(f)) - 1
        size = f.stat().st_size / 1e6
        print(f"  {f.name}: {rows:,} rows ({size:.1f} MB)")
    print("=" * 60)


if __name__ == "__main__":
    main()
