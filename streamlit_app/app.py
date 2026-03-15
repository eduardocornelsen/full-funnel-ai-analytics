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
    default_start = datetime(2017, 1, 1)
    default_end = datetime(2018, 12, 31)
    
    # Initialize session state for date range if not present
    if "df_start" not in st.session_state:
        st.session_state.df_start = default_start
    if "df_end" not in st.session_state:
        st.session_state.df_end = default_end

    # Reset Range logic
    if st.button("Reset Date Range", use_container_width=True):
        st.session_state.df_start = default_start
        st.session_state.df_end = default_end
        st.rerun()

    date_range = st.date_input(
        "Select date range", 
        value=(st.session_state.df_start, st.session_state.df_end),
        min_value=datetime(2016, 1, 1),
        max_value=datetime(2019, 1, 1),
        key="date_input_widget"
    )
    
    # Update state from widget
    if isinstance(date_range, tuple) and len(date_range) == 2:
        st.session_state.df_start, st.session_state.df_end = date_range

    env = st.segmented_control("Environment", ["Production", "Staging", "Dev"], default="Production")
    
    # Explicit UI Toggle for Dark Mode
    is_dark = st.toggle("Dark mode", value=False, help="Toggle between light and dark visualization modes")
    
    if is_dark:
        st.markdown("""
            <style>
                [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
                    background-color: #0d1117 !important;
                    color: #e6edf3 !important;
                }
                [data-testid="stSidebar"] {
                    background-color: #161b22 !important;
                }
                .st-emotion-cache-1vt76ie, [data-testid="stMetric"], [data-testid="stMetricChart"] {
                    background-color: #161b22 !important;
                    border-color: #30363d !important;
                }
                .stMarkdown, p, h1, h2, h3, h4, h5, h6, span, label, .stMetric label {
                    color: #e6edf3 !important;
                }
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
                div[data-testid="stSegmentedControl"] button *, 
                div[data-testid="stPills"] button * {
                    background-color: transparent !important;
                }
                div[data-testid="stSegmentedControl"] button p, 
                div[data-testid="stPills"] button p {
                    color: #e6edf3 !important;
                    -webkit-text-fill-color: #e6edf3 !important;
                }
                div[data-testid="stSegmentedControl"] button[aria-checked="true"],
                div[data-testid="stPills"] button[aria-checked="true"] {
                    background-color: #0078d4 !important;
                    color: white !important;
                }
                div[data-testid="stChatInput"] {
                    background-color: #161b22 !important;
                    border-top: 1px solid #30363d !important;
                }
                [data-testid="stChatInputTextArea"] {
                    background-color: #262730 !important;
                    color: #ffffff !important;
                }
                .stNumberInput button {
                    background-color: #262730 !important;
                    color: white !important;
                    border-color: #30363d !important;
                }
                [data-testid="stMetricChart"] svg {
                    background-color: transparent !important;
                }
            </style>
        """, unsafe_allow_html=True)

# Process date range
sql_start = st.session_state.df_start
sql_end = st.session_state.df_end

# Database Querying Logic
try:
    # 1. Marketing Daily (Sessions & Spend)
    marketing_daily = get_db_data(f"""
        SELECT * FROM fct_marketing_daily 
        WHERE date BETWEEN '{sql_start}' AND '{sql_end}'
        ORDER BY date ASC
    """)
    
    # 2. Funnel Stats (Date-partitioned sources)
    sessions_count = marketing_daily['ga4_total_sessions'].sum() if not marketing_daily.empty else 0
    
    leads_count = get_db_data(f"""
        SELECT COUNT(DISTINCT contact_id) as count 
        FROM hubspot_contacts 
        WHERE create_date BETWEEN '{sql_start}' AND '{sql_end}'
    """)['count'][0]
    
    opps_count = get_db_data(f"""
        SELECT COUNT(DISTINCT opportunity_id) as count 
        FROM salesforce_opportunities 
        WHERE created_date BETWEEN '{sql_start}' AND '{sql_end}'
    """)['count'][0]
    
    orders_count = get_db_data(f"""
        SELECT COUNT(DISTINCT order_id) as count 
        FROM fct_orders 
        WHERE order_date BETWEEN '{sql_start}' AND '{sql_end}'
    """)['count'][0]
    
    # 3. Channel Performance with Normalization Mapping
    channel_perf_raw = get_db_data(f"""
        WITH revenue_by_channel AS (
            SELECT 
                CASE 
                    WHEN last_touch_channel LIKE 'google_ads%' THEN 'google_ads'
                    WHEN last_touch_channel LIKE 'meta_%' THEN 'meta_ads'
                    ELSE last_touch_channel 
                END as channel,
                SUM(revenue) as attributed_revenue,
                COUNT(DISTINCT order_id) as total_orders
            FROM fct_orders
            WHERE order_date BETWEEN '{sql_start}' AND '{sql_end}'
            GROUP BY 1
        ),
        spend_by_channel AS (
            SELECT 
                channel,
                SUM(total_spend) as total_spend
            FROM fct_channel_performance
            GROUP BY 1
        )
        SELECT 
            COALESCE(s.channel, r.channel) as channel,
            COALESCE(s.total_spend, 0) as total_spend,
            COALESCE(r.attributed_revenue, 0) as attributed_revenue,
            COALESCE(r.total_orders, 0) as total_orders
        FROM spend_by_channel s
        FULL OUTER JOIN revenue_by_channel r ON s.channel = r.channel
        WHERE COALESCE(s.channel, r.channel) IS NOT NULL
          AND COALESCE(s.channel, r.channel) != 'None'
    """)
    
    # Calculate CAC/ROAS
    channel_perf_raw['cac'] = channel_perf_raw.apply(lambda x: x['total_spend'] / x['total_orders'] if x['total_orders'] > 0 else 0, axis=1)
    channel_perf_raw['roas'] = channel_perf_raw.apply(lambda x: x['attributed_revenue'] / x['total_spend'] if x['total_spend'] > 0 else 0, axis=1)
    
except Exception as e:
    st.error(f"Error connecting to DuckDB: {e}")
    marketing_daily = pd.DataFrame()
    sessions_count = 0
    leads_count = 0
    opps_count = 0
    orders_count = 0
    channel_perf_raw = pd.DataFrame()

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
    
    if not marketing_daily.empty or leads_count > 0:
        total_spend = marketing_daily['total_spend'].sum()
        conv_rate = (leads_count / sessions_count) if sessions_count > 0 else 0
        
        chart_color = "#58a6ff" if is_dark else "#0078d4"
        plotly_template = "plotly_dark" if is_dark else "plotly_white"
        
        # BAN Row
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total sessions", f"{sessions_count:,}", border=True, 
                   chart_data=marketing_daily['ga4_total_sessions'].tail(7).tolist() if not marketing_daily.empty else [])
        col2.metric("Total spend", f"${total_spend:,.0f}", border=True, 
                   chart_data=marketing_daily['total_spend'].tail(7).tolist() if not marketing_daily.empty else [])
        col3.metric("Total leads", f"{leads_count:,}", border=True)
        col4.metric("Conversion rate", f"{conv_rate:.2%}", border=True)
        
        # Funnel Chart
        with st.container(border=True):
            st.markdown("**Conversion journey (Date Filtered)**")
            stages = ["Sessions", "Leads", "Opportunities", "Orders"]
            values = [sessions_count, leads_count, opps_count, orders_count]
            
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
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data found for the selected date range.")

with tab2:
    st.subheader("Lead scoring (API demo)")
    st.caption("Predict conversion probability based on customer behavior patterns.")
    
    with st.container(border=True):
        with st.form("score_form", border=False):
            col1, col2 = st.columns(2)
            past_orders = col1.number_input("Past orders", min_value=0, max_value=50, value=2)
            revenue_to_date = col2.number_input("Revenue to date ($)", min_value=0.0, max_value=5000.0, value=150.0)
            state = col1.selectbox("Customer state", ["SP", "RJ", "MG", "RS", "PR", "Other"])
            segment = col2.segmented_control("Segment", ["Economy", "Standard", "Premium"], default="Standard")
            
            submitted = st.form_submit_button("Predict conversion score", type="primary")
            
            if submitted:
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
    
    if not channel_perf_raw.empty:
        with st.container(border=True):
            main_color = "#58a6ff" if is_dark else "#0078d4"
            plotly_template = "plotly_dark" if is_dark else "plotly_white"
            
            fig = px.bar(channel_perf_raw, x="channel", y=["attributed_revenue", "total_spend"], 
                        barmode="group", color_discrete_sequence=[main_color, "#29b5e8"],
                        title="Revenue vs Spend by Channel (Synced)")
            fig.update_layout(
                margin=dict(l=0, r=0, t=40, b=0),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                template=plotly_template
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(
                channel_perf_raw.style.format({
                    "total_spend": "${:,.2f}", 
                    "attributed_revenue": "${:,.2f}", 
                    "cac": "${:,.2f}",
                    "roas": "{:.2f}x"
                }), 
                use_container_width=True
            )
    else:
        st.info("No attribution data for this period.")

with tab4:
    st.subheader("Governed AI analyst")
    st.caption("Ask questions about your real DuckDB/dbt metrics.")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar=":material/robot:" if msg["role"] == "assistant" else None):
            st.markdown(msg["content"])

    if not st.session_state.messages:
        SUGGESTIONS = {
            "📈 What's our average ROAS?": "What is our average ROAS across all channels?",
            "💰 How much did we spend?": "Total marketing spend for this period.",
            "🎯 Funnel conversion stats": "Tell me about lead conversion and order rates."
        }
        selected = st.pills("Quick questions:", list(SUGGESTIONS.keys()), label_visibility="collapsed")
        if selected:
            st.session_state.messages.append({"role": "user", "content": SUGGESTIONS[selected]})
            st.rerun()

    if prompt := st.chat_input("Ask about ROAS, CAC, or Lead trends..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar=":material/robot:"):
            query = prompt.lower()
            if "roas" in query:
                top_channel = channel_perf_raw.sort_values("roas", ascending=False).iloc[0] if not channel_perf_raw.empty else None
                if top_channel is not None:
                    response = f"Your average ROAS is **{channel_perf_raw['roas'].mean():.2f}x**. The best performing channel is **{top_channel['channel']}** at **{top_channel['roas']:.2f}x**."
                else: response = "I don't have enough ROAS data for this period."
            elif "spend" in query or "cost" in query:
                total_cost = marketing_daily['total_spend'].sum() if not marketing_daily.empty else 0
                response = f"Total spend for the selected period is **${total_cost:,.2f}**."
            elif "lead" in query or "funnel" in query:
                response = f"We tracked **{leads_count:,} leads** and **{orders_count:,} orders** during this period. Overall lead-to-order conversion is **{(orders_count / leads_count):.1%}**." if leads_count > 0 else "No leads tracked in this range."
            else:
                response = "I've analyzed the warehouse. Performance data is synchronized with DuckDB. Would you like to compare channel metrics?"
            
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
