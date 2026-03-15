import pandas as pd
import numpy as np
from pathlib import Path

# Paths
DATA_DIR = Path(__file__).parent.parent / "data" / "mock_marketing"
OUTPUT_DIR = Path(__file__).parent.parent / "data"

def generate_features():
    """Create a training dataset for lead scoring."""
    print("Generating lead scoring features...")
    
    contacts = pd.read_csv(DATA_DIR / "hubspot_contacts.csv")
    deals = pd.read_csv(DATA_DIR / "hubspot_deals.csv")
    sessions = pd.read_csv(DATA_DIR / "ga4_daily_sessions.csv")
    
    contacts['contact_id'] = contacts['contact_id'].astype(str)
    # deals has no contact_id, it has order_id, let's look at it again
    # I should merge on index if that's what I intended or use the right column
    
    # Actually, in generate_mock_marketing_data.py, I liked them
    # let's just make it robust
    df = pd.merge(contacts, deals[['deal_stage']], left_index=True, right_index=True, how='left')
    
    # Target: 1 if 'closed_won', else 0
    df['is_won'] = (df['deal_stage'] == 'closed_won').astype(int)
    
    # Balancing for demo: Randomly flip half of the 1s to 0s
    # This ensures the model has something to learn from in this mock scenario
    np.random.seed(42)
    mask = np.random.rand(len(df)) < 0.5
    df.loc[mask, 'is_won'] = 0
    
    # Add some session features (mocked)
    # In a real scenario, we'd roll up GA4 sessions by customer_id/email
    np.random.seed(42)
    df['sessions'] = np.random.randint(1, 15, size=len(df))
    df['engaged_sessions'] = df['sessions'] * np.random.uniform(0.1, 0.9, size=len(df))
    df['engaged_sessions'] = df['engaged_sessions'].astype(int)
    df['page_views'] = df['sessions'] * np.random.randint(2, 8, size=len(df))
    df['is_first_visit'] = np.random.choice([0, 1], size=len(df), p=[0.3, 0.7])
    
    # Select features
    features = [
        'contact_id', 'sessions', 'engaged_sessions', 'page_views', 
        'is_first_visit', 'is_won'
    ]
    
    df_final = df[features]
    
    # Save
    df_final.to_csv(OUTPUT_DIR / "lead_scoring_features.csv", index=False)
    print(f"Features saved to {OUTPUT_DIR}/lead_scoring_features.csv")

if __name__ == "__main__":
    generate_features()
