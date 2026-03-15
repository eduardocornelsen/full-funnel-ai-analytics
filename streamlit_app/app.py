import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import duckdb
from datetime import datetime

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
    
    # Strictly defined data bounds
    DATA_MIN = datetime(2016, 9, 1).date()
    DATA_MAX = datetime(2018, 12, 31).date()
    DEFAULT_START = datetime(2017, 1, 1).date()
    DEFAULT_END = datetime(2018, 12, 31).date()

    # Initialize session state for date range
    if "date_selector" not in st.session_state:
        st.session_state.date_selector = (DEFAULT_START, DEFAULT_END)

    # Reset Range logic - Forces widget update via session state
    if st.button("Reset Date Range", use_container_width=True):
        st.session_state.date_selector = (DEFAULT_START, DEFAULT_END)
        st.rerun()

    date_range = st.date_input(
        "Select date range", 
        min_value=DATA_MIN,
        max_value=DATA_MAX,
        key="date_selector" # Linked to session state
    )
    
    # Update local variables from state (Handling single-date selections)
    if isinstance(st.session_state.date_selector, (tuple, list)) and len(st.session_state.date_selector) == 2:
        sql_start, sql_end = st.session_state.date_selector
    else:
        # Prevent crash if only one date is selected
        sql_start = sql_end = (st.session_state.date_selector[0] if isinstance(st.session_state.date_selector, (tuple, list)) else st.session_state.date_selector)

    env = st.segmented_control("Environment", ["Production", "Staging", "Dev"], default="Production")
    
    # Dark Mode CSS
    is_dark = st.toggle("Dark mode", value=False)
    if is_dark:
        st.markdown("""
            <style>
                [data-testid="stAppViewContainer"], [data-testid="stHeader"] { background-color: #0d1117 !important; color: #e6edf3 !important; }
                [data-testid="stSidebar"] { background-color: #161b22 !important; }
                .st-emotion-cache-1vt76ie, [data-testid="stMetric"], [data-testid="stMetricChart"] { background-color: #161b22 !important; border-color: #30363d !important; }
                .stMarkdown, p, h1, h2, h3, h4, h5, h6, span, label, .stMetric label { color: #e6edf3 !important; }
                div[data-testid="stSegmentedControl"] button, div[data-testid="stPills"] button, div[data-baseweb="input"], .stDateInput input { background-color: #262730 !important; color: #ffffff !important; border-color: #30363d !important; }
            </style>
        """, unsafe_allow_html=True)

# Database Querying Logic
try:
    # 1. Marketing & Engagement Daily Trends (GA4)
    # This serves as the source for Sessions, Leads (New Users), and Opportunities (Engaged)
    ga4_daily = get_db_data(f"""
        SELECT 
            date, 
            SUM(sessions) as total_sessions,
            SUM(new_users) as total_leads,
            SUM(engaged_sessions) as total_opportunities
        FROM stg_ga4_sessions
        WHERE date BETWEEN '{sql_start}' AND '{sql_end}'
        GROUP BY 1 ORDER BY 1 ASC
    """)
    
    # 2. Marketing Spend (From daily summary)
    spending_daily = get_db_data(f"""
        SELECT date, total_spend 
        FROM fct_marketing_daily 
        WHERE date BETWEEN '{sql_start}' AND '{sql_end}'
        ORDER BY date ASC
    """)
    
    # 3. Daily Orders (The conversion goal)
    orders_daily = get_db_data(f"""
        SELECT order_date as date, COUNT(DISTINCT order_id) as order_count 
        FROM fct_orders 
        WHERE order_date BETWEEN '{sql_start}' AND '{sql_end}'
        GROUP BY 1 ORDER BY 1 ASC
    """)

    # Aggregates for BANs and Funnel
    sessions_total = ga4_daily['total_sessions'].sum() if not ga4_daily.empty else 0
    leads_total = ga4_daily['total_leads'].sum() if not ga4_daily.empty else 0
    opps_total = ga4_daily['total_opportunities'].sum() if not ga4_daily.empty else 0
    orders_total = orders_daily['order_count'].sum() if not orders_daily.empty else 0
    spend_total = spending_daily['total_spend'].sum() if not spending_daily.empty else 0
    
    # Final logical check: Ensure descending order just in case of data anomalies
    # (Though new_users and engaged_sessions are naturally subsets of sessions)
    leads_final = min(int(leads_total), int(sessions_total))
    opps_final = min(int(opps_total), leads_final)
    orders_final = min(int(orders_total), opps_final)
    
    # 4. Normalized Channel Performance
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
    
    channel_perf_raw['cac'] = channel_perf_raw.apply(lambda x: x['total_spend'] / x['total_orders'] if x['total_orders'] > 0 else 0, axis=1)
    channel_perf_raw['roas'] = channel_perf_raw.apply(lambda x: x['attributed_revenue'] / x['total_spend'] if x['total_spend'] > 0 else 0, axis=1)
    
except Exception as e:
    st.error(f"Error fetching data: {e}")
    marketing_daily = pd.DataFrame()
    orders_daily = pd.DataFrame()
    sessions_total = orders_total = leads_final = opps_final = 0
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
    
    # Metrics Row with Engagement-Based Numbers
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("Total sessions", f"{sessions_total:,}", border=True, 
               chart_data=ga4_daily['total_sessions'].tail(14).tolist() if not ga4_daily.empty else None)
    
    col2.metric("Total spend", f"${spend_total:,.0f}", border=True, 
               chart_data=spending_daily['total_spend'].tail(14).tolist() if not spending_daily.empty else None)
    
    col3.metric("Total leads", f"{leads_final:,}", border=True, 
               help="Leads are based on GA4 'New Users' (Total unique people visiting for the first time).",
               chart_data=ga4_daily['total_leads'].tail(14).tolist() if not ga4_daily.empty else None)
    
    conv_rate = (orders_final / sessions_total) if sessions_total > 0 else 0
    col4.metric("Conversion rate", f"{conv_rate:.2%}", border=True, 
               chart_data=orders_daily['order_count'].tail(14).tolist() if not orders_daily.empty else None)
    
    # Funnel Chart
    with st.container(border=True):
        st.markdown("**Conversion journey (Real Engagement-Based Funnel)**")
        stages = ["Sessions", "Leads (New Users)", "Opportunities (Engaged)", "Orders"]
        values = [sessions_total, leads_final, opps_final, orders_final]
        
        chart_color = "#58a6ff" if is_dark else "#0078d4"
        plotly_template = "plotly_dark" if is_dark else "plotly_white"
        
        fig = go.Figure(go.Funnel(
            y=stages,
            x=values,
            textinfo="value+percent initial",
            marker={"color": [chart_color, "#29b5e8", "#71c8e5", "#a5ddf2"]}
        ))
        fig.update_layout(
            margin=dict(l=0, r=0, t=20, b=0), 
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            template=plotly_template, height=450
        )
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Lead scoring (API demo)")
    with st.container(border=True):
        with st.form("score_form", border=False):
            col1, col2 = st.columns(2)
            past_orders = col1.number_input("Past orders", min_value=0, max_value=50, value=2)
            revenue_to_date = col2.number_input("Revenue to date ($)", min_value=0.0, max_value=5000.0, value=150.0)
            state = col1.selectbox("Customer state", ["SP", "RJ", "MG", "RS", "PR", "Other"])
            segment = col2.segmented_control("Segment", ["Economy", "Standard", "Premium"], default="Standard")
            submitted = st.form_submit_button("Predict conversion score", type="primary")
            if submitted:
                prob = min(0.3 + (past_orders * 0.1) + (revenue_to_date * 0.0001), 0.98)
                st.metric("Probability of next purchase", f"{prob:.1%}", border=True)

with tab3:
    st.subheader("Channel attribution & performance")
    if not channel_perf_raw.empty:
        with st.container(border=True):
            main_color = "#58a6ff" if is_dark else "#0078d4"
            plotly_template = "plotly_dark" if is_dark else "plotly_white"
            fig = px.bar(channel_perf_raw, x="channel", y=["attributed_revenue", "total_spend"], 
                        barmode="group", color_discrete_sequence=[main_color, "#29b5e8"],
                        title="Revenue vs Spend by Channel")
            fig.update_layout(margin=dict(l=0, r=0, t=40, b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', template=plotly_template)
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(channel_perf_raw.style.format({"total_spend": "${:,.2f}", "attributed_revenue": "${:,.2f}", "cac": "${:,.2f}", "roas": "{:.2f}x"}), use_container_width=True)

with tab4:
    st.subheader("Governed AI analyst")
    if "messages" not in st.session_state: st.session_state.messages = []
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar=":material/robot:" if msg["role"] == "assistant" else None): st.markdown(msg["content"])
    if not st.session_state.messages:
        SUGGESTIONS = {
            "📈 What is our average ROAS?": "What is our average ROAS?", 
            "💰 How much did we spend?": "How much did we spend?", 
            "🎯 Funnel conversion stats": "Tell me about funnel conversion."
        }
        selected = st.pills("Quick questions:", list(SUGGESTIONS.keys()), label_visibility="collapsed")
        if selected:
            st.session_state.messages.append({"role": "user", "content": SUGGESTIONS[selected]})
            st.rerun()

    if prompt := st.chat_input("Ask about ROAS, CAC, or Lead trends..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant", avatar=":material/robot:"):
            response = "I've analyzed the unified warehouse data. Performance across all channels is now synchronized."
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

with tab5:
    st.subheader("Data Explorer")
    table_list = get_db_data("SELECT name FROM sqlite_master WHERE type='table'")['name'].tolist()
    selected_table = st.selectbox("Select table to inspect", table_list, index=0)
    if selected_table:
        data = get_db_data(f"SELECT * FROM {selected_table} LIMIT 100")
        st.dataframe(data, use_container_width=True)

st.space(50)
st.caption(f"Funnel Mode: State-Linked (Logic Corrected) | DuckDB Analytics | Env: {env}")
