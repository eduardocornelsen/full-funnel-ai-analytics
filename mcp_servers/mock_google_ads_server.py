from fastmcp import FastMCP
import pandas as pd
from pathlib import Path

# Initialize FastMCP server
mcp = FastMCP("Google Ads")

# Path to the data directory
DATA_DIR = Path(__file__).parent.parent / "data"

@mcp.tool()
def get_campaign_performance(start_date: str = None, end_date: str = None):
    """Get summarized performance for all Google Ads campaigns.
    
    Args:
        start_date: YYYY-MM-DD (optional filter)
        end_date: YYYY-MM-DD (optional filter)
    """
    df = pd.read_csv(DATA_DIR / "google_ads_daily_performance.csv")
    df['date'] = pd.to_datetime(df['date'])
    
    if start_date:
        df = df[df['date'] >= start_date]
    if end_date:
        df = df[df['date'] <= end_date]
        
    summary = df.groupby(['campaign_id', 'campaign_name', 'campaign_type']).agg({
        'impressions': 'sum',
        'clicks': 'sum',
        'cost': 'sum',
        'conversions': 'sum'
    }).reset_index()
    
    summary['ctr'] = summary['clicks'] / summary['impressions']
    summary['cpc'] = summary['cost'] / summary['clicks']
    summary['cvr'] = summary['conversions'] / summary['clicks']
    
    return summary.to_dict(orient="records")

@mcp.tool()
def list_campaigns():
    """List all available Google Ads campaigns."""
    df = pd.read_csv(DATA_DIR / "google_ads_daily_performance.csv")
    campaigns = df[['campaign_id', 'campaign_name', 'campaign_type']].drop_duplicates()
    return campaigns.to_dict(orient="records")

if __name__ == "__main__":
    mcp.run()
