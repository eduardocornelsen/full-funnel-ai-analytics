from fastmcp import FastMCP
import pandas as pd
from pathlib import Path

# Initialize FastMCP server
mcp = FastMCP("Salesforce")

# Path to the data directory
DATA_DIR = Path(__file__).parent.parent / "data" / "mock_marketing"

@mcp.tool()
def get_opportunity_pipeline(start_date: str = None, end_date: str = None):
    """Get summarized opportunity pipeline from Salesforce by stage.

    Args:
        start_date: YYYY-MM-DD — filter opportunities created on or after this date (optional).
        end_date:   YYYY-MM-DD — filter opportunities created on or before this date (optional).

    Note:
        Default (no dates) returns all-time pipeline.
        Pass window_start / window_end from golden_metrics.json _meta to align
        with the current 90-day ad spend window (rolls forward daily).
    """
    df = pd.read_csv(DATA_DIR / "salesforce_opportunities.csv")
    df['created_date'] = pd.to_datetime(df['created_date'], errors='coerce')

    if start_date:
        df = df[df['created_date'] >= start_date]
    if end_date:
        df = df[df['created_date'] <= end_date]

    agg_cols = {'opportunity_id': 'count', 'amount': 'sum'}
    if 'expected_revenue' in df.columns:
        agg_cols['expected_revenue'] = 'sum'

    summary = df.groupby(['stage']).agg(agg_cols).rename(
        columns={'opportunity_id': 'opp_count'}
    ).reset_index()

    return summary.to_dict(orient="records")

@mcp.tool()
def get_revenue_by_source(start_date: str = None, end_date: str = None):
    """Get closed-won revenue broken down by lead source.

    Args:
        start_date: YYYY-MM-DD — filter by close_date on or after this date (optional).
        end_date:   YYYY-MM-DD — filter by close_date on or before this date (optional).
    """
    df = pd.read_csv(DATA_DIR / "salesforce_opportunities.csv")
    df['close_date'] = pd.to_datetime(df['close_date'], errors='coerce')

    won_df = df[df['stage'] == 'Closed Won']

    if start_date:
        won_df = won_df[won_df['close_date'] >= start_date]
    if end_date:
        won_df = won_df[won_df['close_date'] <= end_date]

    summary = won_df.groupby(['lead_source']).agg(
        total_revenue=('amount', 'sum'),
        won_count=('opportunity_id', 'count')
    ).reset_index()

    return summary.to_dict(orient="records")

if __name__ == "__main__":
    mcp.run()
