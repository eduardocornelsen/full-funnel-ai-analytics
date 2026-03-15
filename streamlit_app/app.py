import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import httpx
import asyncio

st.set_page_config(page_title="Full-Funnel AI Analytics", layout="wide")

# Paths
DATA_DIR = Path(__file__).parent.parent / "data"

st.title("🚀 Full-Funnel AI Marketing Analytics")
st.markdown("### Interactive Insights Powered by dbt + ML Scoring")

# Sidebar
st.sidebar.header("Configuration")
date_range = st.sidebar.date_input("Select Date Range", [])

# Dashboard Tabs
tab1, tab2, tab3 = st.tabs(["📊 Marketing Funnel", "🧠 Lead Scoring", "🔍 Channel Attribution"])

with tab1:
    st.header("Unified Marketing Funnel")
    
    # Load GA4 and CRM data
    ga4_df = pd.read_csv(DATA_DIR / "mock_marketing" / "ga4_daily_sessions.csv")
    hubspot_df = pd.read_csv(DATA_DIR / "mock_marketing" / "hubspot_contacts.csv")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Sessions", f"{ga4_df['sessions'].sum():,}")
    col2.metric("New Leads", f"{len(hubspot_df):,}")
    col3.metric("Conv. Rate", f"{(len(hubspot_df) / ga4_df['sessions'].sum()):.2%}")
    
    # Funnel Chart
    stages = ["Sessions", "Leads", "Opportunities", "Closed Won"]
    values = [ga4_df['sessions'].sum(), len(hubspot_df), int(len(hubspot_df)*0.4), int(len(hubspot_df)*0.15)]
    
    fig = go.Figure(go.Funnel(
        y=stages,
        x=values,
        textinfo="value+percent initial"
    ))
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.header("ML Lead Scoring (API Demo)")
    st.markdown("Test the production lead scoring model in real-time.")
    
    with st.form("score_form"):
        col1, col2 = st.columns(2)
        sessions = col1.number_input("Sessions", min_value=1, max_value=50, value=5)
        page_views = col2.number_input("Page Views", min_value=1, max_value=200, value=12)
        engaged = col1.number_input("Engaged Sessions", min_value=0, max_value=sessions, value=2)
        channel = col2.selectbox("Channel", ["Direct", "Organic Search", "Paid Search", "Paid Social"])
        
        submitted = st.form_submit_with_button("Predict Conversion Score")
        
        if submitted:
            # Mocking the API call for the dashboard
            # In a real app, we'd use: response = httpx.post("http://localhost:8000/score", ...)
            prob = (sessions * 0.05 + engaged * 0.1 + page_views * 0.01) / 5
            prob = min(prob, 0.95)
            
            st.metric("Conversion Probability", f"{prob:.1%}")
            if prob > 0.7:
                st.success("High Priority Lead: Route to instant sales follow-up.")
            else:
                st.info("Nurture Candidate: Add to marketing automation.")

with tab3:
    st.header("Channel Attribution Comparisons")
    
    # Mock attribution data
    attr_df = pd.DataFrame({
        "Channel": ["Google Ads", "Meta Ads", "Organic Search", "Direct", "Referral"],
        "First-Touch": [12000, 8000, 15000, 5000, 2000],
        "Last-Touch": [9000, 11000, 10000, 8000, 4000],
        "Linear": [10500, 9500, 12500, 6500, 3000]
    })
    
    fig = px.bar(attr_df, x="Channel", y=["First-Touch", "Last-Touch", "Linear"], 
                 title="Revenue by Attribution Model", barmode="group")
    st.plotly_chart(fig, use_container_width=True)
    
st.divider()
st.caption("Built with Streamlit + Plotly. Data governed by dbt Semantic Layer.")
