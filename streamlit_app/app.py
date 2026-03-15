import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import random
import duckdb
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Analytics Platform", 
    page_icon=":material/analytics:", 
    layout="wide"
)

# Paths
DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DATA_DIR / "olist_analytics.duckdb"

# Helper to load data from DuckDB
@st.cache_data
def get_db_data(query):
    con = duckdb.connect(str(DB_PATH))
    df = con.execute(query).df()
    con.close()
    return df

st.title(":material/rocket_launch: Full-funnel AI analytics")
st.caption("Interactive insights governed by dbt + DuckDB")

# Sidebar
with st.sidebar:
    st.header(":material/settings: Configuration")
    
    # Real Date Filtering
    # Set default range to last 365 days of known data (data seems to be around 2017-2018)
    default_start = datetime(2017, 1, 1)
    default_end = datetime(2018, 12, 31)
    
    date_range = st.date_input(
        "Select date range", 
        value=(default_start, default_end),
        min_value=datetime(2016, 1, 1),
        max_value=datetime(2019, 1, 1)
    )
    
    env = st.segmented_control("Environment", ["Production", "Staging", "Dev"], default="Production")
    
    # Explicit UI Toggle for Dark Mode
    is_dark = st.toggle("Dark mode", value=False, help="Toggle between light and dark visualization modes")
    
    if is_dark:
        st.markdown("""
            <style>
                /* Main Backgrounds */
                [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
                    background-color: #0d1117 !important;
                    color: #e6edf3 !important;
                }
                [data-testid="stSidebar"] {
                    background-color: #161b22 !important;
                }
                
                /* Cards & Borders */
                .st-emotion-cache-1vt76ie, [data-testid="stMetric"], [data-testid="stMetricChart"] {
                    background-color: #161b22 !important;
                    border-color: #30363d !important;
                }
                
                /* Global Typography */
                .stMarkdown, p, h1, h2, h3, h4, h5, h6, span, label, .stMetric label {
                    color: #e6edf3 !important;
                }
                
                /* Precision Widget Overrides (Segmented Control, Pills, Buttons) */
                div[data-testid="stSegmentedControl"] button, 
                div[data-testid="stPills"] button,
                div[data-baseweb="input"],
                div[data-baseweb="select"] > div,
                .stNumberInput input,
                .stDateInput input {
                    background-color: #262730 !important;
                    color: #ffffff !important;
                    border-color: #30363d !important;
                    -webkit-text-fill-color: #ffffff !important;
                }
                
                /* Force all children to be transparent so the button background shows */
                div[data-testid="stSegmentedControl"] button *, 
                div[data-testid="stPills"] button * {
                    background-color: transparent !important;
                }
                
                /* Unselected State Visibility */
                div[data-testid="stSegmentedControl"] button p, 
                div[data-testid="stPills"] button p {
                    color: #e6edf3 !important;
                    -webkit-text-fill-color: #e6edf3 !important;
                }
                
                /* Selected State (Primary) */
                div[data-testid="stSegmentedControl"] button[aria-checked="true"],
                div[data-testid="stPills"] button[aria-checked="true"] {
                    background-color: #0078d4 !important;
                    color: white !important;
                }
                
                /* Chat Input Fix */
                div[data-testid="stChatInput"] {
                    background-color: #161b22 !important;
                    border-top: 1px solid #30363d !important;
                }
                [data-testid="stChatInputTextArea"] {
                    background-color: #262730 !important;
                    color: #ffffff !important;
                }

                /* Number Input +/- Controls */
                .stNumberInput button {
                    background-color: #262730 !important;
                    color: white !important;
                    border-color: #30363d !important;
                }

                /* Metric Chart (Sparklines) Transparency */
                [data-testid="stMetricChart"] svg {
                    background-color: transparent !important;
                }
            </style>
        """, unsafe_allow_html=True)

# Process date range
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = default_start, default_end

# Database Querying Logic
try:
    # Filtered Daily Marketing Data
    marketing_daily = get_db_data(f"""
        SELECT * FROM fct_marketing_daily 
        WHERE date BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY date ASC
    """)
    
    # Pipeline Summary
    pipeline_summary = get_db_data("SELECT * FROM fct_pipeline")
    
    # Channel Performance
    channel_perf = get_db_data("SELECT * FROM fct_channel_performance")
    
except Exception as e:
    st.error(f"Error connecting to DuckDB: {e}")
    marketing_daily = pd.DataFrame()
    pipeline_summary = pd.DataFrame()
    channel_perf = pd.DataFrame()

# Dashboard Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    ":material/dashboard: Marketing funnel", 
    ":material/psychology: Lead scoring", 
    ":material/compare_arrows: Channel attribution",
    ":material/chat: AI analyst",
    ":material/database: Data Explorer"
])

with tab1:
    st.subheader("Unified marketing funnel")
    
    if not marketing_daily.empty:
        total_sessions = marketing_daily['ga4_total_sessions'].sum()
        total_spend = marketing_daily['total_spend'].sum()
        total_leads = pipeline_summary['total_leads'].sum()
        
        # Color palette that adapts to theme
        chart_color = "#58a6ff" if is_dark else "#0078d4"
        plotly_template = "plotly_dark" if is_dark else "plotly_white"
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Total sessions", 
                f"{total_sessions:,}", 
                border=True,
                chart_data=marketing_daily['ga4_total_sessions'].tail(7).tolist()
            )
        with col2:
            st.metric(
                "Total spend", 
                f"${total_spend:,.0f}", 
                border=True,
                chart_data=marketing_daily['total_spend'].tail(7).tolist()
            )
        with col3:
            st.metric(
                "Blended CAC", 
                f"${(total_spend / total_leads):.2f}" if total_leads > 0 else "$0.00", 
                border=True,
                chart_data=marketing_daily['blended_cac'].tail(7).tolist()
            )
        
        # Funnel Chart
        with st.container(border=True):
            st.markdown("**Conversion journey (Consolidated)**")
            stages = ["Impressions", "Leads", "Opportunities", "Closed Won"]
            values = [
                pipeline_summary['total_touches'].sum(),
                pipeline_summary['total_leads'].sum(),
                pipeline_summary['total_opportunities'].sum(),
                pipeline_summary['closed_won'].sum()
            ]
            
            fig = go.Figure(go.Funnel(
                y=stages,
                x=values,
                textinfo="value+percent initial",
                marker={"color": [chart_color, "#29b5e8", "#71c8e5", "#a5ddf2"]}
            ))
            fig.update_layout(
                margin=dict(l=0, r=0, t=20, b=0), 
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)',
                template=plotly_template,
                height=350
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data found for the selected date range.")

with tab2:
    st.subheader("Lead scoring (API demo)")
    st.caption("Predict conversion probability based on customer behavior patterns.")
    
    # Load feature stats for realistic scaling
    feat_stats = get_db_data("SELECT AVG(total_orders) as avg_orders, AVG(total_revenue) as avg_rev FROM fct_lead_scoring_features")
    
    with st.container(border=True):
        with st.form("score_form", border=False):
            col1, col2 = st.columns(2)
            past_orders = col1.number_input("Past orders", min_value=0, max_value=50, value=2)
            revenue_to_date = col2.number_input("Revenue to date ($)", min_value=0.0, max_value=5000.0, value=150.0)
            state = col1.selectbox("Customer state", ["SP", "RJ", "MG", "RS", "PR", "Other"])
            segment = col2.segmented_control("Segment", ["Economy", "Standard", "Premium"], default="Standard")
            
            submitted = st.form_submit_button("Predict conversion score", type="primary")
            
            if submitted:
                # Real-ish logic based on features
                base = 0.3
                order_boost = min(past_orders * 0.1, 0.4)
                rev_boost = min(revenue_to_date * 0.0001, 0.2)
                prob = base + order_boost + rev_boost
                if segment == "Premium": prob += 0.1
                prob = min(prob, 0.98)
                
                st.metric("Probability of next purchase", f"{prob:.1%}", border=True)
                if prob > 0.7:
                    st.toast("High value potential!", icon=":material/stars:")
                    st.success("Recommendation: High-priority retention campaign.")
                else:
                    st.info("Recommendation: Standard nurture sequence.")

with tab3:
    st.subheader("Channel attribution & performance")
    
    if not channel_perf.empty:
        with st.container(border=True):
            main_color = "#58a6ff" if is_dark else "#0078d4"
            plotly_template = "plotly_dark" if is_dark else "plotly_white"
            
            fig = px.bar(channel_perf, x="channel", y=["attributed_revenue", "total_spend"], 
                        barmode="group", color_discrete_sequence=[main_color, "#29b5e8"],
                        title="Revenue vs Spend by Channel")
            fig.update_layout(
                margin=dict(l=0, r=0, t=40, b=0),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                template=plotly_template
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(channel_perf.style.format({"total_spend": "${:,.2f}", "attributed_revenue": "${:,.2f}", "roas": "{:.2f}x"}), use_container_width=True)

with tab4:
    st.subheader("Governed AI analyst")
    st.caption("Ask questions about your real DuckDB/dbt metrics.")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar=":material/robot:" if msg["role"] == "assistant" else None):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask about ROAS, CAC, or Lead trends..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar=":material/robot:"):
            query = prompt.lower()
            if "roas" in query:
                top_channel = channel_perf.sort_values("roas", ascending=False).iloc[0]
                response = f"Your average ROAS is **{channel_perf['roas'].mean():.2f}x**. The best performing channel is **{top_channel['channel']}** at **{top_channel['roas']:.2f}x**."
            elif "spend" in query or "cost" in query:
                total_cost = marketing_daily['total_spend'].sum()
                response = f"Total spend for the selected period is **${total_cost:,.2f}**. Meta Ads accounts for **${marketing_daily['total_meta_spend'].sum():,.2f}** of that."
            elif "lead" in query:
                leads = pipeline_summary['total_leads'].sum()
                response = f"We have identified **{leads:,} leads** in the database. Conversion to Opportunity is currently at **{(pipeline_summary['total_opportunities'].sum() / leads):.1%}**."
            else:
                response = "I've analyzed the warehouse. We are tracking performance across multiple channels. Would you like me to compare ROAS or drill down into spend trends?"
            
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

with tab5:
    st.subheader("Data Explorer")
    st.caption("Browse the underlying dbt models and raw datasets.")
    
    table_list = get_db_data("SELECT name FROM sqlite_master WHERE type='table'")['name'].tolist()
    selected_table = st.selectbox("Select table to inspect", table_list, index=table_list.index("fct_marketing_daily") if "fct_marketing_daily" in table_list else 0)
    
    if selected_table:
        data = get_db_data(f"SELECT * FROM {selected_table} LIMIT 100")
        st.markdown(f"**Showing first 100 rows of `{selected_table}`**")
        st.dataframe(data, use_container_width=True)
        
        col1, col2 = st.columns(2)
        col1.download_button("Download CSV", data.to_csv(index=False), f"{selected_table}.csv", "text/csv")
        if col2.button("Show schema"):
            schema = get_db_data(f"DESCRIBE {selected_table}")
            st.table(schema[['column_name', 'column_type']])

st.space(50)
st.caption(f"Connected to **olist_analytics.duckdb** | Environment: **{env}**")
