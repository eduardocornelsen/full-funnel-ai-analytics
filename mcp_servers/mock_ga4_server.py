from fastmcp import FastMCP
import pandas as pd
from pathlib import Path

# Initialize FastMCP server
mcp = FastMCP("GA4")

# Path to the data directory
DATA_DIR = Path(__file__).parent.parent / "data" / "mock_marketing"

@mcp.tool()
def get_traffic_by_channel(start_date: str = None, end_date: str = None):
    """Get summarized traffic insights from GA4 by channel group.
    
    Args:
        start_date: YYYY-MM-DD (optional filter)
        end_date: YYYY-MM-DD (optional filter)
    """
    df = pd.read_csv(DATA_DIR / "ga4_daily_sessions.csv")
    df['date'] = pd.to_datetime(df['date'])
    
    if start_date:
        df = df[df['date'] >= start_date]
    if end_date:
        df = df[df['date'] <= end_date]
        
    summary = df.groupby(['channel_group']).agg({
        'sessions': 'sum',
        'engaged_sessions': 'sum',
        'conversions': 'sum'
    }).reset_index()
    
    summary['engagement_rate'] = summary['engaged_sessions'] / summary['sessions']
    summary['conversion_rate'] = summary['conversions'] / summary['sessions']
    
    return summary.to_dict(orient="records")

@mcp.tool()
def get_daily_trends(channel: str = None):
    """Get daily session trends, optionally filtered by channel."""
    df = pd.read_csv(DATA_DIR / "ga4_daily_sessions.csv")
    
    if channel:
        df = df[df['channel_group'] == channel]
        
    summary = df.groupby('date').agg({'sessions': 'sum', 'conversions': 'sum'}).reset_index()
    return summary.to_dict(orient="records")

if __name__ == "__main__":
    mcp.run()
