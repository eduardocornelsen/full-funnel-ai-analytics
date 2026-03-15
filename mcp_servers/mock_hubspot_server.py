from fastmcp import FastMCP
import pandas as pd
from pathlib import Path

# Initialize FastMCP server
mcp = FastMCP("HubSpot")

# Path to the data directory
DATA_DIR = Path(__file__).parent.parent / "data"

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
def get_deal_pipeline_summary():
    """Get summarized deal pipeline from HubSpot."""
    df = pd.read_csv(DATA_DIR / "hubspot_deals.csv")
    
    summary = df.groupby(['deal_stage']).agg({
        'deal_id': 'count',
        'amount': 'sum'
    }).rename(columns={'deal_id': 'deal_count', 'amount': 'total_value'}).reset_index()
    
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
