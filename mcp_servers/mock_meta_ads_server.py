from fastmcp import FastMCP
import pandas as pd
from pathlib import Path

# Initialize FastMCP server
mcp = FastMCP("Meta Ads")

# Path to the data directory
DATA_DIR = Path(__file__).parent.parent / "data"

@mcp.tool()
def get_campaign_insights(start_date: str = None, end_date: str = None):
    """Get summarized insights for all Meta Ads campaigns.
    
    Args:
        start_date: YYYY-MM-DD (optional filter)
        end_date: YYYY-MM-DD (optional filter)
    """
    df = pd.read_csv(DATA_DIR / "meta_ads_daily_performance.csv")
    df['date'] = pd.to_datetime(df['date'])
    
    if start_date:
        df = df[df['date'] >= start_date]
    if end_date:
        df = df[df['date'] <= end_date]
        
    summary = df.groupby(['campaign_id', 'campaign_name', 'objective']).agg({
        'impressions': 'sum',
        'reach': 'sum',
        'spend': 'sum',
        'link_clicks': 'sum',
        'purchases': 'sum'
    }).reset_index()
    
    summary['cpm'] = (summary['spend'] / summary['impressions']) * 1000
    summary['cpc'] = summary['spend'] / summary['link_clicks']
    summary['roas'] = (summary['purchases'] * 100) / summary['spend'] # Assumes avg $100 per purchase for mock
    
    return summary.to_dict(orient="records")

@mcp.tool()
def list_campaigns():
    """List all available Meta Ads campaigns."""
    df = pd.read_csv(DATA_DIR / "meta_ads_daily_performance.csv")
    campaigns = df[['campaign_id', 'campaign_name', 'objective']].drop_duplicates()
    return campaigns.to_dict(orient="records")

if __name__ == "__main__":
    mcp.run()
