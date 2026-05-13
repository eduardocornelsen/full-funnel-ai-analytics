from fastmcp import FastMCP
import pandas as pd
from pathlib import Path

# Initialize FastMCP server
mcp = FastMCP("HubSpot")

# Path to the data directory
DATA_DIR = Path(__file__).parent.parent / "data" / "mock_marketing"

@mcp.tool()
def get_contacts_summary():
    """Get a summary of CRM contacts by lifecycle stage and city."""
    df = pd.read_csv(DATA_DIR / "hubspot_contacts.csv")

    lifecycle_summary = df['lifecycle_stage'].value_counts().to_dict()
    city_summary = df['city'].value_counts().head(10).to_dict()

    return {
        "lifecycle_stages": lifecycle_summary,
        "top_cities": city_summary,
        "total_contacts": len(df)
    }

@mcp.tool()
def get_deal_pipeline_summary(start_date: str = None, end_date: str = None):
    """Get summarized deal pipeline from HubSpot, optionally filtered by create_date.

    Args:
        start_date: YYYY-MM-DD — filter deals created on or after this date (optional).
                    Defaults to all-time when omitted.
        end_date:   YYYY-MM-DD — filter deals created on or before this date (optional).
                    Defaults to all-time when omitted.

    Note:
        HubSpot contacts are all-time lifetime counts and are never date-filtered.
        Use start_date/end_date only when comparing pipeline to a specific ad spend window.
        Default (no dates) returns all-time pipeline — appropriate for CRM Contacts KPI.
    """
    df = pd.read_csv(DATA_DIR / "hubspot_deals.csv")
    df['create_date'] = pd.to_datetime(df['create_date'], errors='coerce')

    if start_date:
        df = df[df['create_date'] >= start_date]
    if end_date:
        df = df[df['create_date'] <= end_date]

    summary = df.groupby(['deal_stage']).agg(
        deal_count=('deal_id', 'count'),
        total_value=('amount', 'sum')
    ).reset_index()

    return summary.to_dict(orient="records")

@mcp.tool()
def search_contacts(query: str):
    """Search for contacts by email, first name, or last name."""
    df = pd.read_csv(DATA_DIR / "hubspot_contacts.csv")

    query = query.lower()
    results = df[
        df['email'].str.lower().str.contains(query, na=False) |
        df['first_name'].str.lower().str.contains(query, na=False) |
        df['last_name'].str.lower().str.contains(query, na=False)
    ]

    return results.head(10).to_dict(orient="records")

if __name__ == "__main__":
    mcp.run()
