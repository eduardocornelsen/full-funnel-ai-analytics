from fastmcp import FastMCP
import pandas as pd
from pathlib import Path

# Initialize FastMCP server
mcp = FastMCP("Salesforce")

# Path to the data directory
DATA_DIR = Path(__file__).parent.parent / "data" / "mock_marketing"

@mcp.tool()
def get_opportunity_pipeline():
    """Get summarized opportunity pipeline from Salesforce by stage."""
    df = pd.read_csv(DATA_DIR / "salesforce_opportunities.csv")

    agg_cols = {'opportunity_id': 'count', 'amount': 'sum'}
    if 'expected_revenue' in df.columns:
        agg_cols['expected_revenue'] = 'sum'

    summary = df.groupby(['stage']).agg(agg_cols).rename(
        columns={'opportunity_id': 'opp_count'}
    ).reset_index()

    return summary.to_dict(orient="records")

@mcp.tool()
def get_revenue_by_source():
    """Get closed-won revenue broken down by lead source."""
    df = pd.read_csv(DATA_DIR / "salesforce_opportunities.csv")

    won_df = df[df['stage'] == 'Closed Won']

    summary = won_df.groupby(['lead_source']).agg({
        'amount': 'sum',
        'opportunity_id': 'count'
    }).rename(columns={'amount': 'total_revenue', 'opportunity_id': 'won_count'}).reset_index()

    return summary.to_dict(orient="records")

if __name__ == "__main__":
    mcp.run()
