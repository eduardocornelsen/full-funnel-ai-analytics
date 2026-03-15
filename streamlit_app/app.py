import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import random

st.set_page_config(
    page_title="Analytics Platform", 
    page_icon=":material/analytics:", 
    layout="wide"
)

# Paths
DATA_DIR = Path(__file__).parent.parent / "data"

st.title(":material/rocket_launch: Full-funnel AI analytics")
st.caption("Interactive insights governed by dbt + ML scoring")

# Sidebar
with st.sidebar:
    st.header(":material/settings: Configuration")
    date_range = st.date_input("Select date range", [])
    st.segmented_control("Environment", ["Production", "Staging", "Dev"], default="Production")
    
    # Explicit UI Toggle for Dark Mode with CSS Injection
    is_dark = st.toggle("Dark mode", value=False, help="Toggle between light and dark visualization modes")
    
    if is_dark:
        st.markdown("""
            <style>
                /* 1. Reset Global Backgrounds */
                [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stSidebar"] {
                    background-color: #0d1117 !important;
                    color: #e6edf3 !important;
                }
                
                /* 2. Nuclear Widget Overrides (Targets the internal white containers) */
                /* Segmented Controls, Pills, and standard Inputs */
                [data-testid="stSegmentedControl"] div,
                [data-testid="stPills"] div,
                [data-testid="stChatInput"] div,
                [data-baseweb="input"] div,
                [data-baseweb="select"] div {
                    background-color: #262730 !important;
                    color: #ffffff !important;
                    border-color: #30363d !important;
                }

                /* 3. Button/Segment/Pill Specifics */
                div[data-testid="stSegmentedControl"] button, 
                div[data-testid="stPills"] button {
                    background-color: #262730 !important;
                    color: #ffffff !important;
                    border: 1px solid #30363d !important;
                }
                
                /* Text invisibility fix for p tags inside buttons */
                div[data-testid="stSegmentedControl"] button p, 
                div[data-testid="stPills"] button p {
                    color: #ffffff !important;
                    -webkit-text-fill-color: #ffffff !important;
                }

                /* Active/Selected state */
                div[data-testid="stSegmentedControl"] button[aria-checked="true"],
                div[data-testid="stPills"] button[aria-checked="true"] {
                    background-color: #0078d4 !important;
                    color: #ffffff !important;
                }

                /* 4. Input Field Specifics */
                input, textarea {
                    background-color: #262730 !important;
                    color: #ffffff !important;
                    -webkit-text-fill-color: #ffffff !important;
                }

                /* 5. Metrics & Cards */
                .st-emotion-cache-1vt76ie, [data-testid="stMetric"], [data-testid="stMetricChart"] {
                    background-color: #161b22 !important;
                    border: 1px solid #30363d !important;
                }
                
                /* Sparkline Fix */
                [data-testid="stMetricChart"] svg {
                    background-color: transparent !important;
                }

                /* 6. Fix for unselected sidebar date input */
                [data-testid="stSidebar"] div[data-baseweb="input"] {
                    background-color: #262730 !important;
                }
                
                /* 7. Chat Input specific wrapper */
                [data-testid="stChatInput"] {
                    background-color: #161b22 !important;
                    border: 1px solid #30363d !important;
                    border-radius: 12px;
                    padding: 4px;
                }
            </style>
        """, unsafe_allow_html=True)

# Dashboard Tabs with Icons
tab1, tab2, tab3, tab4 = st.tabs([
    ":material/dashboard: Marketing funnel", 
    ":material/psychology: Lead scoring", 
    ":material/compare_arrows: Channel attribution",
    ":material/chat: AI analyst"
])

with tab1:
    st.subheader("Unified marketing funnel")
    
    # Load GA4 and CRM data
    try:
        ga4_df = pd.read_csv(DATA_DIR / "mock_marketing" / "ga4_daily_sessions.csv")
        hubspot_df = pd.read_csv(DATA_DIR / "mock_marketing" / "hubspot_contacts.csv")
        
        # Color palette that adapts to theme
        chart_color = "#58a6ff" if is_dark else "#0078d4"
        plotly_template = "plotly_dark" if is_dark else "plotly_white"
        
        # Metric row - Restored to 3 columns for desktop
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Total sessions", 
                f"{ga4_df['sessions'].sum():,}", 
                "+5.2%", 
                border=True,
                chart_data=[random.randint(400, 600) for _ in range(7)]
            )
        with col2:
            st.metric(
                "New leads", 
                f"{len(hubspot_df):,}", 
                "+12.4%", 
                border=True,
                chart_data=[random.randint(10, 30) for _ in range(7)]
            )
        with col3:
            st.metric(
                "Conversion rate", 
                f"{(len(hubspot_df) / ga4_df['sessions'].sum()):.2%}", 
                "+0.5%", 
                border=True,
                chart_data=[random.uniform(0.02, 0.04) for _ in range(7)]
            )
        
        # Funnel Chart in a card
        with st.container(border=True):
            st.markdown("**Conversion journey**")
            stages = ["Sessions", "Leads", "Opportunities", "Closed Won"]
            values = [ga4_df['sessions'].sum(), len(hubspot_df), int(len(hubspot_df)*0.4), int(len(hubspot_df)*0.15)]
            
            fig = go.Figure(go.Funnel(
                y=stages,
                x=values,
                textinfo="value+percent initial",
                marker={"color": [chart_color, "#29b5e8", "#71c8e5", "#a5ddf2"]}
            ))
            fig.update_layout(
                margin=dict(l=0, r=0, t=0, b=0), 
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)',
                template=plotly_template
            )
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error loading funnel data: {e}")

with tab2:
    st.subheader("Lead scoring (API demo)")
    st.caption("Predict conversion probability using the production XGBoost model.")
    
    with st.container(border=True):
        with st.form("score_form", border=False):
            col1, col2 = st.columns(2)
            sessions = col1.number_input("Sessions", min_value=1, max_value=50, value=5)
            page_views = col2.number_input("Page views", min_value=1, max_value=200, value=12)
            engaged = col1.number_input("Engaged sessions", min_value=0, max_value=sessions, value=2)
            channel = col2.segmented_control("Channel", ["Direct", "Paid Search", "Paid Social", "Organic"], default="Direct")
            
            submitted = st.form_submit_button("Predict conversion score", type="primary")
            
            if submitted:
                prob = (sessions * 0.05 + engaged * 0.1 + page_views * 0.01) / 5
                prob = min(prob, 0.95)
                
                st.metric("Conversion probability", f"{prob:.1%}", border=True)
                if prob > 0.7:
                    st.toast("High priority lead detected!", icon=":material/check_circle:")
                    st.success("Priority: Route to instant sales follow-up.")
                else:
                    st.info("Priority: Add to marketing nurture sequence.", icon=":material/info:")

with tab3:
    st.subheader("Channel attribution comparisons")
    
    with st.container(border=True):
        # Mock attribution data
        attr_df = pd.DataFrame({
            "Channel": ["Google Ads", "Meta Ads", "Organic Search", "Direct", "Referral"],
            "First-Touch": [12000, 8000, 15000, 5000, 2000],
            "Last-Touch": [9000, 11000, 10000, 8000, 4000],
            "Linear": [10500, 9500, 12500, 6500, 3000]
        })
        
        main_color = "#58a6ff" if is_dark else "#0078d4"
        plotly_template = "plotly_dark" if is_dark else "plotly_white"
        
        fig = px.bar(attr_df, x="Channel", y=["First-Touch", "Last-Touch", "Linear"], 
                    barmode="group", color_discrete_sequence=[main_color, "#29b5e8", "#a5ddf2"])
        fig.update_layout(
            legend_title_text="Model", 
            margin=dict(l=0, r=0, t=30, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            template=plotly_template
        )
        st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.subheader("Governed AI analyst")
    st.caption("Ask natural language questions about your marketing performance.")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar=":material/robot:" if msg["role"] == "assistant" else None):
            st.markdown(msg["content"])

    # Suggestion Chips (only on empty chat)
    if not st.session_state.messages:
        SUGGESTIONS = {
            "📈 What's our blended ROAS?": "Calculate the blended ROAS for last month across all channels.",
            "🎯 Compare attribution models": "Show me the difference between first-touch and last-touch revenue.",
            "🧬 Analyze funnel drops": "Where are leads dropping off in the HubSpot-to-Salesforce pipeline?"
        }
        selected = st.pills("Try asking:", list(SUGGESTIONS.keys()), label_visibility="collapsed")
        if selected:
            st.session_state.messages.append({"role": "user", "content": SUGGESTIONS[selected]})
            st.rerun()

    # Chat Input
    if prompt := st.chat_input("Ask a question about your data..."):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant", avatar=":material/robot:"):
            # Mocking the AI "brain" response based on the dbt logic
            if "roas" in prompt.lower():
                response = "Based on the dbt Semantic Layer, your **Blended ROAS is 4.2x**. \n\n*   **Google Ads:** 3.8x\n*   **Meta Ads:** 4.1x\n*   **Organic:** 5.5x"
            elif "attribution" in prompt.lower():
                response = "Our data shows that **Organic Search** is undervalued by 25% in last-touch models compared to first-touch credit. I recommend increasing top-of-funnel SEO spend."
            else:
                response = "I've analyzed your warehouse data. We've seen a **12% increase in Qualified Leads** from HubSpot this week, primarily driven by the 'Summer Campaign' on Paid Social."
            
            st.markdown(response)
            st.feedback("thumbs")
        st.session_state.messages.append({"role": "assistant", "content": response})

st.space(50)
st.caption("Built with :material/favorite: by AI. Data governed by **dbt Semantic Layer**.")
