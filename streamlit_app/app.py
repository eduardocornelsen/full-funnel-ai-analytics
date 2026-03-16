import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import duckdb
from datetime import datetime
import os
from dotenv import load_dotenv
import anthropic

load_dotenv(Path(__file__).parent.parent / ".env")

st.set_page_config(
    page_title="Full-funnel AI analytics",
    page_icon=":material/analytics:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Paths ──────────────────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DATA_DIR / "olist_analytics.duckdb"

# ── Color palette ──────────────────────────────────────────────────────────────
PALETTE = ["#60a5fa", "#f87171", "#34d399", "#fbbf24", "#a78bfa", "#fb923c", "#38bdf8"]
BG = "rgba(0,0,0,0)"


# ── DB helpers ─────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False, max_entries=200)
def q(sql: str) -> pd.DataFrame:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    df = con.execute(sql).df()
    con.close()
    return df

@st.cache_data(ttl=300, show_spinner=False)
def get_db_schema() -> str:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    tables = con.execute("SHOW TABLES").fetchdf()["name"].tolist()
    parts = []
    for t in tables:
        cols = con.execute(f"DESCRIBE {t}").fetchdf()
        col_str = ", ".join(f"{r['column_name']} ({r['column_type']})" for _, r in cols.iterrows())
        parts.append(f"  {t}: {col_str}")
    con.close()
    return "\n".join(parts)

def run_sql(sql: str):
    try:
        con = duckdb.connect(str(DB_PATH), read_only=True)
        df = con.execute(sql).df()
        con.close()
        return df, None
    except Exception as e:
        return None, str(e)

def fmt_m(v): return f"${v/1e6:.2f}M" if v >= 1e6 else f"${v/1e3:.1f}K"
def fmt_k(v): return f"{v/1e3:.1f}K" if v >= 1000 else str(int(v))

def spark(series: pd.Series, n: int = 14) -> list:
    """Return last n values of a series as a plain list for chart_data."""
    return series.dropna().tail(n).tolist()


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## :material/analytics: Full-funnel AI")
    st.space("small")

    DATA_MIN = datetime(2024, 3, 30).date()
    DATA_MAX = datetime(2026, 3, 15).date()
    DEFAULT_START = datetime(2024, 7, 16).date()
    DEFAULT_END = datetime(2026, 3, 15).date()

    if "date_selector" not in st.session_state:
        st.session_state.date_selector = (DEFAULT_START, DEFAULT_END)

    if st.button("Reset range", use_container_width=True, icon=":material/refresh:"):
        st.session_state.date_selector = (DEFAULT_START, DEFAULT_END)
        st.rerun()

    st.date_input(
        "Date range",
        min_value=DATA_MIN,
        max_value=DATA_MAX,
        key="date_selector",
    )

    if isinstance(st.session_state.date_selector, (tuple, list)) and len(st.session_state.date_selector) == 2:
        sql_start, sql_end = st.session_state.date_selector
    else:
        val = st.session_state.date_selector
        sql_start = sql_end = (val[0] if isinstance(val, (tuple, list)) else val)

    st.space("small")
    is_dark = st.toggle("Dark mode", value=False)
    tmpl = "plotly_dark" if is_dark else "plotly_white"

    if is_dark:
        st.markdown("""<style>
            [data-testid="stAppViewContainer"],[data-testid="stHeader"]{background:#0d1117!important;color:#e6edf3!important}
            [data-testid="stSidebar"]{background:#161b22!important}
            .stMarkdown,p,h1,h2,h3,h4,h5,h6,span,label{color:#e6edf3!important}
        </style>""", unsafe_allow_html=True)

    env = st.segmented_control("Environment", ["Production", "Staging", "Dev"], default="Production")
    st.space("small")
    st.caption(f"Data: Mar 2024 – Mar 2026")


# ── Load data ──────────────────────────────────────────────────────────────────
S, E = str(sql_start), str(sql_end)

# Revenue & orders
daily_rev = q(f"""
    SELECT order_date, order_count, total_revenue, avg_order_value, unique_customers
    FROM fct_daily_revenue
    WHERE order_date BETWEEN '{S}' AND '{E}'
    ORDER BY 1
""")
daily_rev["week"] = pd.to_datetime(daily_rev["order_date"]).dt.to_period("W").apply(lambda r: r.start_time)
weekly_rev = daily_rev.groupby("week").agg(
    total_revenue=("total_revenue", "sum"),
    order_count=("order_count", "sum"),
    avg_aov=("avg_order_value", "mean"),
).reset_index()

# Spend
spend_weekly = q(f"""
    SELECT DATE_TRUNC('week', date) as week,
        SUM(total_google_spend) as google_spend,
        SUM(total_meta_spend)   as meta_spend,
        SUM(total_spend)        as total_spend
    FROM fct_marketing_daily
    WHERE date BETWEEN '{S}' AND '{E}'
    GROUP BY 1 ORDER BY 1
""")

# GA4
ga4_channel = q(f"""
    SELECT channel_group,
        SUM(sessions)              as sessions,
        SUM(new_users)             as new_users,
        SUM(engaged_sessions)      as engaged_sessions,
        AVG(bounce_rate)           as avg_bounce_rate,
        AVG(avg_session_duration_sec) as avg_duration,
        AVG(pages_per_session)     as avg_pages,
        AVG(engagement_rate)       as engagement_rate
    FROM stg_ga4_sessions
    WHERE date BETWEEN '{S}' AND '{E}'
    GROUP BY 1 ORDER BY sessions DESC
""")

ga4_weekly = q(f"""
    SELECT DATE_TRUNC('week', date) as week, channel_group,
        SUM(sessions) as sessions
    FROM stg_ga4_sessions
    WHERE date BETWEEN '{S}' AND '{E}'
    GROUP BY 1, 2 ORDER BY 1
""")

ga4_weekly_totals = q(f"""
    SELECT DATE_TRUNC('week', date) as week,
        SUM(sessions)         as sessions,
        SUM(new_users)        as new_users,
        SUM(engaged_sessions) as engaged_sessions,
        AVG(engagement_rate)  as engagement_rate
    FROM stg_ga4_sessions
    WHERE date BETWEEN '{S}' AND '{E}'
    GROUP BY 1 ORDER BY 1
""")

ga4_device = q(f"""
    SELECT device_category,
        SUM(sessions)         as sessions,
        SUM(engaged_sessions) as engaged_sessions
    FROM stg_ga4_sessions
    WHERE date BETWEEN '{S}' AND '{E}'
    GROUP BY 1 ORDER BY sessions DESC
""")

# Campaigns
gads_perf = q(f"""
    SELECT campaign_name, campaign_type,
        SUM(impressions)      as impressions,
        SUM(clicks)           as clicks,
        SUM(cost)             as cost,
        SUM(conversions)      as conversions,
        SUM(conversion_value) as conversion_value,
        AVG(ctr)*100          as avg_ctr,
        AVG(avg_cpc)          as avg_cpc,
        CASE WHEN SUM(cost)>0 THEN SUM(conversion_value)/SUM(cost) ELSE 0 END as roas
    FROM stg_google_ads_performance
    WHERE date BETWEEN '{S}' AND '{E}'
    GROUP BY 1, 2 ORDER BY cost DESC
""")

meta_perf = q(f"""
    SELECT campaign_name, objective,
        SUM(impressions)    as impressions,
        SUM(reach)          as reach,
        SUM(spend)          as spend,
        SUM(link_clicks)    as link_clicks,
        SUM(purchases)      as purchases,
        SUM(purchase_value) as purchase_value,
        AVG(ctr)*100        as avg_ctr,
        AVG(cpm)            as avg_cpm,
        CASE WHEN SUM(spend)>0 THEN SUM(purchase_value)/SUM(spend) ELSE 0 END as roas
    FROM stg_meta_ads_performance
    WHERE date BETWEEN '{S}' AND '{E}'
    GROUP BY 1, 2 ORDER BY spend DESC
""")

# Weekly campaign sparklines
gads_weekly = q(f"""
    SELECT DATE_TRUNC('week', date) as week,
        SUM(cost)             as google_spend,
        SUM(conversions)      as google_conv,
        CASE WHEN SUM(cost)>0 THEN SUM(conversion_value)/SUM(cost) ELSE 0 END as google_roas
    FROM stg_google_ads_performance
    WHERE date BETWEEN '{S}' AND '{E}'
    GROUP BY 1 ORDER BY 1
""")

meta_weekly = q(f"""
    SELECT DATE_TRUNC('week', date) as week,
        SUM(spend)          as meta_spend,
        SUM(purchases)      as meta_purch,
        CASE WHEN SUM(spend)>0 THEN SUM(purchase_value)/SUM(spend) ELSE 0 END as meta_roas
    FROM stg_meta_ads_performance
    WHERE date BETWEEN '{S}' AND '{E}'
    GROUP BY 1 ORDER BY 1
""")

# Attribution & pipeline
attribution = q("SELECT * FROM fct_marketing_attribution ORDER BY linear_revenue DESC")
pipeline_ch = q("SELECT * FROM fct_pipeline ORDER BY total_conversions DESC")

# Products
top_cats = q(f"""
    SELECT p.product_category_name as category,
        SUM(i.price)           as revenue,
        COUNT(DISTINCT i.order_id) as orders
    FROM stg_order_items i
    JOIN stg_products p  ON i.product_id = p.product_id
    JOIN stg_orders o    ON i.order_id   = o.order_id
    WHERE o.order_date BETWEEN '{S}' AND '{E}'
      AND o.order_status = 'delivered'
      AND p.product_category_name IS NOT NULL
    GROUP BY 1 ORDER BY revenue DESC LIMIT 15
""")

rev_by_state = q(f"""
    SELECT customer_state as state,
        SUM(revenue)               as revenue,
        COUNT(DISTINCT order_id)   as orders
    FROM fct_orders
    WHERE order_date BETWEEN '{S}' AND '{E}'
    GROUP BY 1 ORDER BY revenue DESC
""")

payment_dist = q(f"""
    SELECT payment_type, COUNT(*) as cnt, SUM(payment_value) as total
    FROM stg_order_payments p
    JOIN stg_orders o ON p.order_id = o.order_id
    WHERE o.order_date BETWEEN '{S}' AND '{E}'
    GROUP BY 1 ORDER BY cnt DESC
""")

review_dist = q(f"""
    SELECT review_score, COUNT(*) as cnt
    FROM stg_order_reviews r
    JOIN stg_orders o ON r.order_id = o.order_id
    WHERE o.order_date BETWEEN '{S}' AND '{E}'
    GROUP BY 1 ORDER BY 1
""")

delivery_stats = q(f"""
    SELECT
        AVG(delivery_days)                                             as avg_days,
        SUM(CASE WHEN is_late_delivery THEN 1 ELSE 0 END)*100.0/COUNT(*) as late_pct
    FROM fct_orders
    WHERE order_date BETWEEN '{S}' AND '{E}'
""")

# Weekly delivery trend for sparkline
weekly_aov = q(f"""
    SELECT DATE_TRUNC('week', order_date) as week, AVG(avg_order_value) as aov
    FROM fct_daily_revenue
    WHERE order_date BETWEEN '{S}' AND '{E}'
    GROUP BY 1 ORDER BY 1
""")

# CRM
hubspot_stages = q("""
    SELECT deal_stage,
        COUNT(*)    as deals,
        SUM(amount) as pipeline_value
    FROM stg_hubspot_deals
    GROUP BY 1 ORDER BY pipeline_value DESC
""")

sf_stages = q("""
    SELECT stage,
        COUNT(*)          as opportunities,
        SUM(amount)       as pipeline_value,
        AVG(probability)  as avg_probability
    FROM stg_salesforce_opportunities
    GROUP BY 1 ORDER BY pipeline_value DESC
""")

hubspot_source = q("""
    SELECT lead_source, COUNT(*) as deals, SUM(amount) as value
    FROM stg_hubspot_deals
    GROUP BY 1 ORDER BY value DESC
""")

sf_source = q("""
    SELECT lead_source, COUNT(*) as opps, SUM(amount) as value
    FROM stg_salesforce_opportunities
    GROUP BY 1 ORDER BY value DESC
""")

# Hubspot weekly trend for sparkline
hs_weekly = q(f"""
    SELECT DATE_TRUNC('week', CAST(create_date AS DATE)) as week, SUM(amount) as value
    FROM stg_hubspot_deals
    WHERE CAST(create_date AS DATE) BETWEEN '{S}' AND '{E}'
    GROUP BY 1 ORDER BY 1
""")

# Lead intelligence
segments = q("""
    SELECT customer_segment,
        COUNT(*)    as customers,
        SUM(total_revenue)   as revenue,
        AVG(avg_order_value) as avg_aov,
        AVG(total_orders)    as avg_orders,
        SUM(CASE WHEN is_high_value THEN 1 ELSE 0 END) as high_value_count
    FROM fct_lead_scoring_features
    GROUP BY 1 ORDER BY revenue DESC
""")

lead_sources = q("""
    SELECT lead_source,
        COUNT(*)    as customers,
        SUM(total_revenue)   as revenue,
        AVG(total_orders)    as avg_orders,
        SUM(CASE WHEN is_high_value THEN 1 ELSE 0 END)*100.0/COUNT(*) as high_value_pct
    FROM fct_lead_scoring_features
    GROUP BY 1 ORDER BY revenue DESC
""")

rev_hist = q("""
    SELECT
        CASE
            WHEN total_revenue < 100   THEN '$0–100'
            WHEN total_revenue < 250   THEN '$100–250'
            WHEN total_revenue < 500   THEN '$250–500'
            WHEN total_revenue < 1000  THEN '$500–1K'
            WHEN total_revenue < 2500  THEN '$1K–2.5K'
            ELSE '$2.5K+'
        END as bucket,
        COUNT(*) as customers
    FROM fct_lead_scoring_features
    GROUP BY 1 ORDER BY MIN(total_revenue)
""")

# ── KPI aggregates ─────────────────────────────────────────────────────────────
total_revenue  = daily_rev["total_revenue"].sum()
total_orders   = daily_rev["order_count"].sum()
total_sessions = ga4_weekly_totals["sessions"].sum() if not ga4_weekly_totals.empty else 0
total_spend_g  = gads_perf["cost"].sum() if not gads_perf.empty else 0
total_spend_m  = meta_perf["spend"].sum() if not meta_perf.empty else 0
total_spend    = total_spend_g + total_spend_m
blended_roas   = total_revenue / total_spend if total_spend > 0 else 0
new_users      = ga4_weekly_totals["new_users"].sum() if not ga4_weekly_totals.empty else 0
engaged        = ga4_weekly_totals["engaged_sessions"].sum() if not ga4_weekly_totals.empty else 0

hs_open        = hubspot_stages[hubspot_stages["deal_stage"] != "closed_won"]["pipeline_value"].sum()
sf_open        = sf_stages[sf_stages["stage"] != "Closed Won"]["pipeline_value"].sum()
pipeline_total = hs_open + sf_open
hs_won         = hubspot_stages[hubspot_stages["deal_stage"] == "closed_won"]["pipeline_value"].sum()
sf_won         = sf_stages[sf_stages["stage"] == "Closed Won"]["pipeline_value"].sum()
avg_aov        = daily_rev["avg_order_value"].mean() if not daily_rev.empty else 0
avg_delivery   = delivery_stats["avg_days"].iloc[0] if not delivery_stats.empty else 0
late_pct       = delivery_stats["late_pct"].iloc[0] if not delivery_stats.empty else 0

# Sparkline series helpers (14 weekly data points each)
sp_rev     = spark(weekly_rev["total_revenue"])
sp_orders  = spark(weekly_rev["order_count"])
sp_spend   = spark(spend_weekly["total_spend"]) if not spend_weekly.empty else []
sp_roas_w  = spark(weekly_rev["total_revenue"] / spend_weekly["total_spend"].reindex(weekly_rev.index).fillna(1)) if not spend_weekly.empty else []
sp_sess    = spark(ga4_weekly_totals["sessions"]) if not ga4_weekly_totals.empty else []
sp_pipe    = spark(hs_weekly["value"]) if not hs_weekly.empty else []
sp_new_usr = spark(ga4_weekly_totals["new_users"]) if not ga4_weekly_totals.empty else []
sp_engaged = spark(ga4_weekly_totals["engaged_sessions"]) if not ga4_weekly_totals.empty else []
sp_eng_rt  = spark(ga4_weekly_totals["engagement_rate"]) if not ga4_weekly_totals.empty else []
sp_gspend  = spark(gads_weekly["google_spend"]) if not gads_weekly.empty else []
sp_mspend  = spark(meta_weekly["meta_spend"]) if not meta_weekly.empty else []
sp_gconv   = spark(gads_weekly["google_conv"]) if not gads_weekly.empty else []
sp_mpurch  = spark(meta_weekly["meta_purch"]) if not meta_weekly.empty else []
sp_groas   = spark(gads_weekly["google_roas"]) if not gads_weekly.empty else []
sp_mroas   = spark(meta_weekly["meta_roas"]) if not meta_weekly.empty else []
sp_aov     = spark(weekly_aov["aov"]) if not weekly_aov.empty else []

total_attr_rev = attribution["linear_revenue"].sum() if not attribution.empty else 0
top_channel    = attribution.iloc[0]["channel"] if not attribution.empty else "N/A"

total_customers = segments["customers"].sum() if not segments.empty else 0
high_value      = segments["high_value_count"].sum() if not segments.empty else 0
high_value_pct  = high_value / total_customers * 100 if total_customers > 0 else 0
avg_ltv         = segments["revenue"].sum() / total_customers if total_customers > 0 else 0

# ── App header ─────────────────────────────────────────────────────────────────
st.title(":material/rocket_launch: Full-funnel AI analytics")
st.caption(f"DuckDB · dbt · {env} · {S} → {E}")

# ── Tabs ───────────────────────────────────────────────────────────────────────
tabs = st.tabs([
    ":material/dashboard: Overview",
    ":material/trending_up: Traffic",
    ":material/campaign: Campaigns",
    ":material/hub: Attribution",
    ":material/shopping_cart: Revenue",
    ":material/handshake: CRM pipeline",
    ":material/psychology: Lead intelligence",
    ":material/chat: AI analyst",
    ":material/database: Data explorer",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
with tabs[0]:
    st.subheader("Executive overview")

    with st.container(horizontal=True):
        st.metric("Total revenue",   fmt_m(total_revenue),  border=True, chart_data=sp_rev,    chart_type="bar")
        st.metric("Total orders",    fmt_k(total_orders),   border=True, chart_data=sp_orders,  chart_type="bar")
        st.metric("Total spend",     fmt_m(total_spend),    border=True, chart_data=sp_spend,   chart_type="line")
        st.metric("Blended ROAS",    f"{blended_roas:.2f}x",border=True, chart_data=sp_roas_w,  chart_type="line")
        st.metric("Sessions",        fmt_k(int(total_sessions)), border=True, chart_data=sp_sess, chart_type="line")
        st.metric("Open pipeline",   fmt_m(pipeline_total), border=True, chart_data=sp_pipe,   chart_type="bar")

    col_a, col_b = st.columns([2, 1])

    with col_a:
        with st.container(border=True):
            st.markdown("**Weekly revenue & orders**")
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(go.Bar(x=weekly_rev["week"], y=weekly_rev["total_revenue"],
                                 name="Revenue", marker_color=PALETTE[0], opacity=0.85), secondary_y=False)
            fig.add_trace(go.Scatter(x=weekly_rev["week"], y=weekly_rev["order_count"],
                                     name="Orders", line=dict(color=PALETTE[1], width=2), mode="lines"), secondary_y=True)
            fig.update_layout(template=tmpl, paper_bgcolor=BG, plot_bgcolor=BG,
                              margin=dict(l=0, r=0, t=10, b=0), height=280,
                              legend=dict(orientation="h", y=1.1))
            fig.update_yaxes(title_text="Revenue ($)", secondary_y=False)
            fig.update_yaxes(title_text="Orders", secondary_y=True)
            st.plotly_chart(fig, use_container_width=True)

    with col_b:
        with st.container(border=True):
            st.markdown("**Sessions by channel**")
            if not ga4_channel.empty:
                fig = px.pie(ga4_channel, names="channel_group", values="sessions",
                             color_discrete_sequence=PALETTE, hole=0.45)
                fig.update_layout(template=tmpl, paper_bgcolor=BG, margin=dict(l=0, r=0, t=10, b=0), height=280,
                                  legend=dict(orientation="v", font=dict(size=10)))
                fig.update_traces(textinfo="percent", hovertemplate="%{label}<br>%{value:,.0f} sessions")
                st.plotly_chart(fig, use_container_width=True)

    col_c, col_d = st.columns(2)

    with col_c:
        with st.container(border=True, height="stretch"):
            st.markdown("**Top 10 categories by revenue**")
            fig = px.bar(top_cats.head(10), x="revenue", y="category", orientation="h",
                         color="revenue", color_continuous_scale="Blues",
                         labels={"revenue": "Revenue ($)", "category": ""})
            fig.update_layout(template=tmpl, paper_bgcolor=BG, plot_bgcolor=BG,
                              margin=dict(l=0, r=0, t=10, b=0), height=300,
                              coloraxis_showscale=False, yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig, use_container_width=True)

    with col_d:
        with st.container(border=True, height="stretch"):
            st.markdown("**Revenue by state (top 10)**")
            fig = px.bar(rev_by_state.head(10), x="state", y="revenue",
                         color="revenue", color_continuous_scale="Teal",
                         labels={"state": "State", "revenue": "Revenue ($)"})
            fig.update_layout(template=tmpl, paper_bgcolor=BG, plot_bgcolor=BG,
                              margin=dict(l=0, r=0, t=10, b=0), height=300,
                              coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

    with st.container(border=True):
        st.markdown("**Conversion funnel**")
        funnel_vals   = [int(total_sessions), int(new_users), int(engaged), int(total_orders)]
        funnel_labels = ["Sessions", "New users (leads)", "Engaged sessions (opps)", "Orders (converted)"]
        fig = go.Figure(go.Funnel(y=funnel_labels, x=funnel_vals,
                                  textinfo="value+percent initial",
                                  marker={"color": PALETTE[:4]}))
        fig.update_layout(template=tmpl, paper_bgcolor=BG,
                          margin=dict(l=0, r=0, t=10, b=0), height=300)
        st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — TRAFFIC
# ══════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    st.subheader("Web traffic — GA4")

    avg_engagement = (engaged / total_sessions * 100) if total_sessions > 0 else 0

    with st.container(horizontal=True):
        st.metric("Total sessions",    fmt_k(int(total_sessions)), border=True, chart_data=sp_sess,    chart_type="line")
        st.metric("New users",         fmt_k(int(new_users)),      border=True, chart_data=sp_new_usr, chart_type="bar")
        st.metric("Engaged sessions",  fmt_k(int(engaged)),        border=True, chart_data=sp_engaged, chart_type="line")
        st.metric("Avg engagement rate", f"{avg_engagement:.1f}%", border=True, chart_data=sp_eng_rt,  chart_type="line")

    with st.container(border=True):
        st.markdown("**Weekly sessions by channel (stacked area)**")
        if not ga4_weekly.empty:
            ga4_weekly_copy = ga4_weekly.copy()
            ga4_weekly_copy["week"] = pd.to_datetime(ga4_weekly_copy["week"])
            ga4_pivot = ga4_weekly_copy.pivot(index="week", columns="channel_group", values="sessions").fillna(0).reset_index()
            fig = go.Figure()
            channels = [c for c in ga4_pivot.columns if c != "week"]
            for i, ch in enumerate(channels):
                fig.add_trace(go.Scatter(x=ga4_pivot["week"], y=ga4_pivot[ch], name=ch,
                                         mode="lines", stackgroup="one",
                                         line=dict(color=PALETTE[i % len(PALETTE)], width=0),
                                         fillcolor=PALETTE[i % len(PALETTE)]))
            fig.update_layout(template=tmpl, paper_bgcolor=BG, plot_bgcolor=BG,
                              margin=dict(l=0, r=0, t=10, b=0), height=320,
                              legend=dict(orientation="h", y=-0.2))
            st.plotly_chart(fig, use_container_width=True)

    col_a, col_b = st.columns(2)

    with col_a:
        with st.container(border=True, height="stretch"):
            st.markdown("**Engagement rate by channel**")
            if not ga4_channel.empty:
                eng = ga4_channel.copy()
                eng["eng_rate"] = eng["engaged_sessions"] / eng["sessions"] * 100
                fig = px.bar(eng.sort_values("eng_rate"), x="eng_rate", y="channel_group",
                             orientation="h", color="eng_rate", color_continuous_scale="Greens",
                             labels={"eng_rate": "Engagement rate (%)", "channel_group": ""})
                fig.update_layout(template=tmpl, paper_bgcolor=BG, plot_bgcolor=BG,
                                  margin=dict(l=0, r=0, t=10, b=0), height=280,
                                  coloraxis_showscale=False)
                st.plotly_chart(fig, use_container_width=True)

    with col_b:
        with st.container(border=True, height="stretch"):
            st.markdown("**Sessions by device**")
            if not ga4_device.empty:
                fig = px.pie(ga4_device, names="device_category", values="sessions",
                             color_discrete_sequence=PALETTE, hole=0.4)
                fig.update_layout(template=tmpl, paper_bgcolor=BG,
                                  margin=dict(l=0, r=0, t=10, b=0), height=280)
                fig.update_traces(textinfo="label+percent")
                st.plotly_chart(fig, use_container_width=True)

    with st.container(border=True):
        st.markdown("**Channel performance summary**")
        if not ga4_channel.empty:
            disp = ga4_channel.copy()
            disp["engagement_rate"] = disp["engaged_sessions"] / disp["sessions"] * 100
            disp["avg_duration_min"] = disp["avg_duration"] / 60
            st.dataframe(
                disp[["channel_group","sessions","new_users","engaged_sessions",
                       "engagement_rate","avg_duration_min","avg_pages"]],
                column_config={
                    "channel_group":    st.column_config.TextColumn("Channel"),
                    "sessions":         st.column_config.NumberColumn("Sessions",      format="%d"),
                    "new_users":        st.column_config.NumberColumn("New users",     format="%d"),
                    "engaged_sessions": st.column_config.NumberColumn("Engaged",       format="%d"),
                    "engagement_rate":  st.column_config.ProgressColumn("Engagement %", min_value=0, max_value=100, format="%.1f%%"),
                    "avg_duration_min": st.column_config.NumberColumn("Avg duration",  format="%.1f min"),
                    "avg_pages":        st.column_config.NumberColumn("Pages/session", format="%.1f"),
                },
                hide_index=True, use_container_width=True,
            )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — CAMPAIGNS
# ══════════════════════════════════════════════════════════════════════════════
with tabs[2]:
    st.subheader("Paid campaign performance")

    total_conversions_g = gads_perf["conversions"].sum() if not gads_perf.empty else 0
    total_conversions_m = meta_perf["purchases"].sum() if not meta_perf.empty else 0
    avg_roas_g = (gads_perf["cost"].sum() and gads_perf["conversion_value"].sum() / gads_perf["cost"].sum()) if not gads_perf.empty else 0
    avg_roas_m = (meta_perf["spend"].sum() and meta_perf["purchase_value"].sum() / meta_perf["spend"].sum()) if not meta_perf.empty else 0

    col_g, col_m = st.columns(2)

    with col_g:
        st.markdown("**:material/ads_click: Google Ads**")
        with st.container(horizontal=True):
            st.metric("Spend",        fmt_m(total_spend_g),         border=True, chart_data=sp_gspend, chart_type="bar")
            st.metric("Conversions",  fmt_k(int(total_conversions_g)), border=True, chart_data=sp_gconv,  chart_type="bar")
            st.metric("ROAS",         f"{avg_roas_g:.2f}x",          border=True, chart_data=sp_groas,  chart_type="line")

    with col_m:
        st.markdown("**:material/groups: Meta Ads**")
        with st.container(horizontal=True):
            st.metric("Spend",     fmt_m(total_spend_m),          border=True, chart_data=sp_mspend, chart_type="bar")
            st.metric("Purchases", fmt_k(int(total_conversions_m)), border=True, chart_data=sp_mpurch, chart_type="bar")
            st.metric("ROAS",      f"{avg_roas_m:.2f}x",           border=True, chart_data=sp_mroas,  chart_type="line")

    with st.container(border=True):
        st.markdown("**Weekly spend — Google vs Meta**")
        if not spend_weekly.empty:
            spend_weekly_copy = spend_weekly.copy()
            spend_weekly_copy["week"] = pd.to_datetime(spend_weekly_copy["week"])
            fig = go.Figure()
            fig.add_trace(go.Bar(x=spend_weekly_copy["week"], y=spend_weekly_copy["google_spend"], name="Google Ads", marker_color=PALETTE[0]))
            fig.add_trace(go.Bar(x=spend_weekly_copy["week"], y=spend_weekly_copy["meta_spend"],   name="Meta Ads",   marker_color=PALETTE[1]))
            fig.update_layout(barmode="stack", template=tmpl, paper_bgcolor=BG, plot_bgcolor=BG,
                              margin=dict(l=0, r=0, t=10, b=0), height=280,
                              legend=dict(orientation="h", y=1.1))
            st.plotly_chart(fig, use_container_width=True)

    col_a, col_b = st.columns(2)

    with col_a:
        with st.container(border=True, height="stretch"):
            st.markdown("**Google Ads — ROAS by campaign**")
            if not gads_perf.empty:
                fig = px.bar(gads_perf.sort_values("roas"), x="roas", y="campaign_name",
                             orientation="h", color="campaign_type", color_discrete_sequence=PALETTE,
                             labels={"roas": "ROAS", "campaign_name": ""})
                fig.update_layout(template=tmpl, paper_bgcolor=BG, plot_bgcolor=BG,
                                  margin=dict(l=0, r=0, t=10, b=0), height=260)
                st.plotly_chart(fig, use_container_width=True)

            st.dataframe(
                gads_perf,
                column_config={
                    "campaign_name":     st.column_config.TextColumn("Campaign", pinned=True),
                    "campaign_type":     st.column_config.TextColumn("Type"),
                    "cost":              st.column_config.NumberColumn("Spend",       format="$%,.0f"),
                    "conversions":       st.column_config.NumberColumn("Conv.",       format="%,.0f"),
                    "conversion_value":  st.column_config.NumberColumn("Conv. value", format="$%,.0f"),
                    "roas":              st.column_config.NumberColumn("ROAS",         format="%.2fx"),
                    "avg_ctr":           st.column_config.NumberColumn("CTR",          format="%.2f%%"),
                    "avg_cpc":           st.column_config.NumberColumn("CPC",          format="$%.2f"),
                    "impressions":       None,
                    "clicks":            None,
                },
                hide_index=True, use_container_width=True, height=200,
            )

    with col_b:
        with st.container(border=True, height="stretch"):
            st.markdown("**Meta Ads — ROAS by campaign**")
            if not meta_perf.empty:
                fig = px.bar(meta_perf.sort_values("roas"), x="roas", y="campaign_name",
                             orientation="h", color="objective", color_discrete_sequence=PALETTE[1:],
                             labels={"roas": "ROAS", "campaign_name": ""})
                fig.update_layout(template=tmpl, paper_bgcolor=BG, plot_bgcolor=BG,
                                  margin=dict(l=0, r=0, t=10, b=0), height=260)
                st.plotly_chart(fig, use_container_width=True)

            st.dataframe(
                meta_perf,
                column_config={
                    "campaign_name":  st.column_config.TextColumn("Campaign", pinned=True),
                    "objective":      st.column_config.TextColumn("Objective"),
                    "spend":          st.column_config.NumberColumn("Spend",        format="$%,.0f"),
                    "purchases":      st.column_config.NumberColumn("Purchases",    format="%,.0f"),
                    "purchase_value": st.column_config.NumberColumn("Purch. value", format="$%,.0f"),
                    "roas":           st.column_config.NumberColumn("ROAS",          format="%.2fx"),
                    "avg_ctr":        st.column_config.NumberColumn("CTR",           format="%.2f%%"),
                    "avg_cpm":        st.column_config.NumberColumn("CPM",           format="$%.2f"),
                    "impressions":    None,
                    "reach":          None,
                    "link_clicks":    None,
                },
                hide_index=True, use_container_width=True, height=200,
            )

    col_e, col_f = st.columns(2)
    with col_e:
        with st.container(border=True):
            st.markdown("**Google spend by campaign type**")
            if not gads_perf.empty:
                type_spend = gads_perf.groupby("campaign_type")["cost"].sum().reset_index()
                fig = px.pie(type_spend, names="campaign_type", values="cost", hole=0.4,
                             color_discrete_sequence=PALETTE)
                fig.update_layout(template=tmpl, paper_bgcolor=BG, margin=dict(l=0, r=0, t=10, b=0), height=240)
                fig.update_traces(textinfo="label+percent")
                st.plotly_chart(fig, use_container_width=True)

    with col_f:
        with st.container(border=True):
            st.markdown("**Meta spend by objective**")
            if not meta_perf.empty:
                obj_spend = meta_perf.groupby("objective")["spend"].sum().reset_index()
                fig = px.pie(obj_spend, names="objective", values="spend", hole=0.4,
                             color_discrete_sequence=PALETTE[1:])
                fig.update_layout(template=tmpl, paper_bgcolor=BG, margin=dict(l=0, r=0, t=10, b=0), height=240)
                fig.update_traces(textinfo="label+percent")
                st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — ATTRIBUTION
# ══════════════════════════════════════════════════════════════════════════════
with tabs[3]:
    st.subheader("Multi-touch attribution")

    with st.container(horizontal=True):
        st.metric("Attributed revenue",  fmt_m(total_attr_rev), border=True, chart_data=sp_rev,    chart_type="bar")
        st.metric("Top channel (linear)", top_channel,           border=True)
        st.metric("Channels tracked",    str(len(attribution)), border=True)
        st.metric("Pipeline touchpoints", fmt_k(pipeline_ch["total_touches"].sum() if not pipeline_ch.empty else 0), border=True)

    with st.container(border=True):
        st.markdown("**Revenue by channel — 4 attribution models**")
        if not attribution.empty:
            attr_long = attribution.melt(
                id_vars="channel",
                value_vars=["first_touch_revenue","last_touch_revenue","linear_revenue","time_decay_revenue"],
                var_name="model", value_name="revenue",
            )
            model_labels = {
                "first_touch_revenue":  "First touch",
                "last_touch_revenue":   "Last touch",
                "linear_revenue":       "Linear",
                "time_decay_revenue":   "Time decay",
            }
            attr_long["model"] = attr_long["model"].map(model_labels)
            fig = px.bar(attr_long, x="channel", y="revenue", color="model",
                         barmode="group", color_discrete_sequence=PALETTE,
                         labels={"revenue": "Revenue ($)", "channel": "Channel", "model": "Model"})
            fig.update_layout(template=tmpl, paper_bgcolor=BG, plot_bgcolor=BG,
                              margin=dict(l=0, r=0, t=10, b=0), height=360,
                              legend=dict(orientation="h", y=1.08))
            st.plotly_chart(fig, use_container_width=True)

    col_a, col_b = st.columns([3, 2])

    with col_a:
        with st.container(border=True, height="stretch"):
            st.markdown("**Attribution model comparison**")
            if not attribution.empty:
                st.dataframe(
                    attribution,
                    column_config={
                        "channel":              st.column_config.TextColumn("Channel", pinned=True),
                        "first_touch_revenue":  st.column_config.NumberColumn("First touch",  format="$%,.0f"),
                        "last_touch_revenue":   st.column_config.NumberColumn("Last touch",   format="$%,.0f"),
                        "linear_revenue":       st.column_config.NumberColumn("Linear",       format="$%,.0f"),
                        "time_decay_revenue":   st.column_config.NumberColumn("Time decay",   format="$%,.0f"),
                        "total_orders":         st.column_config.NumberColumn("Orders",       format="%,.0f"),
                    },
                    hide_index=True, use_container_width=True,
                )

    with col_b:
        with st.container(border=True, height="stretch"):
            st.markdown("**Linear revenue share by channel**")
            if not attribution.empty:
                fig = px.pie(attribution, names="channel", values="linear_revenue",
                             hole=0.4, color_discrete_sequence=PALETTE)
                fig.update_layout(template=tmpl, paper_bgcolor=BG,
                                  margin=dict(l=0, r=0, t=10, b=0), height=280)
                fig.update_traces(textinfo="label+percent")
                st.plotly_chart(fig, use_container_width=True)

    with st.container(border=True):
        st.markdown("**Pipeline by attribution channel**")
        if not pipeline_ch.empty:
            col_x, col_y = st.columns(2)
            with col_x:
                fig = px.bar(pipeline_ch, x="attribution_channel",
                             y=["total_leads","total_opportunities","closed_won"],
                             barmode="group", color_discrete_sequence=PALETTE,
                             labels={"value": "Count", "attribution_channel": "Channel", "variable": "Stage"})
                fig.update_layout(template=tmpl, paper_bgcolor=BG, plot_bgcolor=BG,
                                  margin=dict(l=0, r=0, t=10, b=0), height=280,
                                  legend=dict(orientation="h", y=1.1))
                st.plotly_chart(fig, use_container_width=True)
            with col_y:
                fig = px.scatter(pipeline_ch, x="total_leads", y="closed_won",
                                 size="total_touches", color="attribution_channel",
                                 color_discrete_sequence=PALETTE,
                                 labels={"total_leads": "Leads", "closed_won": "Closed won"},
                                 hover_data=["total_opportunities"])
                fig.update_layout(template=tmpl, paper_bgcolor=BG, plot_bgcolor=BG,
                                  margin=dict(l=0, r=0, t=10, b=0), height=280)
                st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — REVENUE & PRODUCTS
# ══════════════════════════════════════════════════════════════════════════════
with tabs[4]:
    st.subheader("Revenue & product analytics")

    with st.container(horizontal=True):
        st.metric("Total revenue",    fmt_m(total_revenue), border=True, chart_data=sp_rev,    chart_type="bar")
        st.metric("Avg order value",  f"${avg_aov:.2f}",   border=True, chart_data=sp_aov,    chart_type="line")
        st.metric("Avg delivery time", f"{avg_delivery:.1f} days", border=True)
        st.metric("Late delivery rate", f"{late_pct:.1f}%", border=True)

    with st.container(border=True):
        st.markdown("**Daily revenue trend**")
        fig = px.area(daily_rev, x="order_date", y="total_revenue",
                      color_discrete_sequence=[PALETTE[2]],
                      labels={"order_date": "", "total_revenue": "Revenue ($)"})
        fig.update_traces(line_color=PALETTE[2], fillcolor=PALETTE[2], opacity=0.7)
        fig.update_layout(template=tmpl, paper_bgcolor=BG, plot_bgcolor=BG,
                          margin=dict(l=0, r=0, t=10, b=0), height=260)
        st.plotly_chart(fig, use_container_width=True)

    col_a, col_b = st.columns([3, 2])

    with col_a:
        with st.container(border=True, height="stretch"):
            st.markdown("**Top 15 product categories**")
            fig = px.bar(top_cats, x="category", y="revenue",
                         color="orders", color_continuous_scale="Blues",
                         labels={"revenue": "Revenue ($)", "category": "Category", "orders": "Orders"})
            fig.update_layout(template=tmpl, paper_bgcolor=BG, plot_bgcolor=BG,
                              margin=dict(l=0, r=0, t=10, b=0), height=300, xaxis_tickangle=-35)
            st.plotly_chart(fig, use_container_width=True)

    with col_b:
        with st.container(border=True, height="stretch"):
            st.markdown("**Revenue by state**")
            fig = px.treemap(rev_by_state, path=["state"], values="revenue",
                             color="revenue", color_continuous_scale="Blues")
            fig.update_layout(template=tmpl, paper_bgcolor=BG,
                              margin=dict(l=0, r=0, t=10, b=0), height=300,
                              coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

    col_c, col_d = st.columns(2)

    with col_c:
        with st.container(border=True):
            st.markdown("**Payment method distribution**")
            if not payment_dist.empty:
                fig = px.pie(payment_dist, names="payment_type", values="cnt",
                             hole=0.4, color_discrete_sequence=PALETTE,
                             labels={"cnt": "Transactions"})
                fig.update_layout(template=tmpl, paper_bgcolor=BG,
                                  margin=dict(l=0, r=0, t=10, b=0), height=260)
                fig.update_traces(textinfo="label+percent")
                st.plotly_chart(fig, use_container_width=True)

    with col_d:
        with st.container(border=True):
            st.markdown("**Review score distribution**")
            if not review_dist.empty:
                colors = ["#f87171","#fb923c","#fbbf24","#60a5fa","#34d399"]
                fig = px.bar(review_dist, x="review_score", y="cnt",
                             color="review_score", color_discrete_sequence=colors,
                             labels={"review_score": "Score (1–5)", "cnt": "Count"})
                fig.update_layout(template=tmpl, paper_bgcolor=BG, plot_bgcolor=BG,
                                  margin=dict(l=0, r=0, t=10, b=0), height=260, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — CRM PIPELINE
# ══════════════════════════════════════════════════════════════════════════════
with tabs[5]:
    st.subheader("CRM pipeline — HubSpot & Salesforce")

    hs_total_deals  = int(hubspot_stages["deals"].sum()) if not hubspot_stages.empty else 0
    sf_total_opps   = int(sf_stages["opportunities"].sum()) if not sf_stages.empty else 0

    with st.container(horizontal=True):
        st.metric("HubSpot deals",    fmt_k(hs_total_deals),   border=True, chart_data=sp_pipe, chart_type="bar")
        st.metric("SF opportunities", fmt_k(sf_total_opps),    border=True)
        st.metric("HS closed won",    fmt_m(hs_won),           border=True)
        st.metric("SF closed won",    fmt_m(sf_won),           border=True)
        st.metric("Open pipeline",    fmt_m(pipeline_total),   border=True, chart_data=sp_pipe, chart_type="line")

    col_a, col_b = st.columns(2)

    with col_a:
        with st.container(border=True, height="stretch"):
            st.markdown("**HubSpot — pipeline by stage**")
            if not hubspot_stages.empty:
                fig = px.bar(hubspot_stages, x="pipeline_value", y="deal_stage", orientation="h",
                             color="deals", color_continuous_scale="Blues",
                             labels={"pipeline_value": "Value ($)", "deal_stage": "Stage", "deals": "Deals"})
                fig.update_layout(template=tmpl, paper_bgcolor=BG, plot_bgcolor=BG,
                                  margin=dict(l=0, r=0, t=10, b=0), height=300,
                                  yaxis=dict(autorange="reversed"))
                st.plotly_chart(fig, use_container_width=True)

    with col_b:
        with st.container(border=True, height="stretch"):
            st.markdown("**Salesforce — pipeline by stage**")
            if not sf_stages.empty:
                fig = px.bar(sf_stages, x="pipeline_value", y="stage", orientation="h",
                             color="avg_probability", color_continuous_scale="Greens",
                             labels={"pipeline_value": "Value ($)", "stage": "Stage", "avg_probability": "Avg close %"})
                fig.update_layout(template=tmpl, paper_bgcolor=BG, plot_bgcolor=BG,
                                  margin=dict(l=0, r=0, t=10, b=0), height=300,
                                  yaxis=dict(autorange="reversed"))
                st.plotly_chart(fig, use_container_width=True)

    col_c, col_d = st.columns(2)

    with col_c:
        with st.container(border=True):
            st.markdown("**HubSpot — deals by lead source**")
            if not hubspot_source.empty:
                fig = px.pie(hubspot_source, names="lead_source", values="value",
                             hole=0.4, color_discrete_sequence=PALETTE)
                fig.update_layout(template=tmpl, paper_bgcolor=BG,
                                  margin=dict(l=0, r=0, t=10, b=0), height=260)
                fig.update_traces(textinfo="label+percent")
                st.plotly_chart(fig, use_container_width=True)

    with col_d:
        with st.container(border=True):
            st.markdown("**Salesforce — opportunities by lead source**")
            if not sf_source.empty:
                fig = px.pie(sf_source, names="lead_source", values="value",
                             hole=0.4, color_discrete_sequence=PALETTE[1:])
                fig.update_layout(template=tmpl, paper_bgcolor=BG,
                                  margin=dict(l=0, r=0, t=10, b=0), height=260)
                fig.update_traces(textinfo="label+percent")
                st.plotly_chart(fig, use_container_width=True)

    with st.container(border=True):
        st.markdown("**Salesforce — stage details**")
        if not sf_stages.empty:
            st.dataframe(
                sf_stages,
                column_config={
                    "stage":           st.column_config.TextColumn("Stage", pinned=True),
                    "opportunities":   st.column_config.NumberColumn("Opportunities",   format="%,.0f"),
                    "pipeline_value":  st.column_config.NumberColumn("Pipeline value",  format="$%,.0f"),
                    "avg_probability": st.column_config.ProgressColumn("Avg close %",   min_value=0, max_value=100, format="%.1f%%"),
                },
                hide_index=True, use_container_width=True,
            )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 7 — LEAD INTELLIGENCE
# ══════════════════════════════════════════════════════════════════════════════
with tabs[6]:
    st.subheader("Lead intelligence & scoring")

    with st.container(horizontal=True):
        st.metric("Total customers",    fmt_k(int(total_customers)), border=True)
        st.metric("High-value customers", fmt_k(int(high_value)),   border=True)
        st.metric("High-value rate",    f"{high_value_pct:.1f}%",   border=True)
        st.metric("Avg customer LTV",   f"${avg_ltv:.0f}",          border=True)

    col_a, col_b = st.columns(2)

    with col_a:
        with st.container(border=True, height="stretch"):
            st.markdown("**Revenue by customer segment**")
            if not segments.empty:
                fig = px.bar(segments, x="customer_segment", y="revenue",
                             color="customer_segment", color_discrete_sequence=PALETTE,
                             text="customers",
                             labels={"revenue": "Revenue ($)", "customer_segment": "Segment"})
                fig.update_traces(texttemplate="%{text:,.0f} customers", textposition="outside")
                fig.update_layout(template=tmpl, paper_bgcolor=BG, plot_bgcolor=BG,
                                  margin=dict(l=0, r=0, t=10, b=0), height=300, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

    with col_b:
        with st.container(border=True, height="stretch"):
            st.markdown("**Revenue share by segment**")
            if not segments.empty:
                fig = px.pie(segments, names="customer_segment", values="revenue",
                             hole=0.45, color_discrete_sequence=PALETTE)
                fig.update_layout(template=tmpl, paper_bgcolor=BG,
                                  margin=dict(l=0, r=0, t=10, b=0), height=300)
                fig.update_traces(textinfo="label+percent")
                st.plotly_chart(fig, use_container_width=True)

    with st.container(border=True):
        st.markdown("**Lead source performance**")
        if not lead_sources.empty:
            col_x, col_y = st.columns(2)
            with col_x:
                fig = px.scatter(lead_sources, x="avg_orders", y="high_value_pct",
                                 size="customers", color="lead_source",
                                 color_discrete_sequence=PALETTE,
                                 labels={"avg_orders": "Avg orders", "high_value_pct": "High-value %"},
                                 hover_data=["revenue"])
                fig.update_layout(template=tmpl, paper_bgcolor=BG, plot_bgcolor=BG,
                                  margin=dict(l=0, r=0, t=10, b=0), height=280)
                st.plotly_chart(fig, use_container_width=True)
            with col_y:
                fig = px.bar(lead_sources, x="lead_source", y="revenue",
                             color="high_value_pct", color_continuous_scale="Purples",
                             labels={"revenue": "Revenue ($)", "lead_source": "Lead source",
                                     "high_value_pct": "High-value %"})
                fig.update_layout(template=tmpl, paper_bgcolor=BG, plot_bgcolor=BG,
                                  margin=dict(l=0, r=0, t=10, b=0), height=280)
                st.plotly_chart(fig, use_container_width=True)

    col_c, col_d = st.columns(2)

    with col_c:
        with st.container(border=True):
            st.markdown("**Customer revenue distribution**")
            if not rev_hist.empty:
                fig = px.bar(rev_hist, x="bucket", y="customers",
                             color_discrete_sequence=[PALETTE[4]],
                             labels={"bucket": "Revenue bucket", "customers": "Customers"})
                fig.update_layout(template=tmpl, paper_bgcolor=BG, plot_bgcolor=BG,
                                  margin=dict(l=0, r=0, t=10, b=0), height=260)
                st.plotly_chart(fig, use_container_width=True)

    with col_d:
        with st.container(border=True):
            st.markdown("**Lead conversion scorer**")
            with st.form("score_form", border=False):
                f1, f2 = st.columns(2)
                past_orders = f1.number_input("Past orders", 0, 50, 2)
                ltv         = f2.number_input("Total revenue ($)", 0.0, 10000.0, 150.0)
                f3, f4 = st.columns(2)
                segment  = f3.selectbox("Segment", ["Economy","Standard","Premium"])
                lead_src = f4.selectbox("Lead source", ["organic","paid_search","email","referral","direct","social"])
                submitted = st.form_submit_button("Score lead", type="primary", use_container_width=True)

                if submitted:
                    seg_score  = {"Premium": 0.25, "Standard": 0.15, "Economy": 0.05}.get(segment, 0.1)
                    src_score  = {"paid_search": 0.12, "email": 0.10, "referral": 0.08,
                                  "organic": 0.06, "social": 0.04, "direct": 0.03}.get(lead_src, 0.05)
                    order_score = min(past_orders * 0.08, 0.40)
                    ltv_score   = min(ltv / 10000 * 0.20, 0.20)
                    prob = min(0.10 + seg_score + src_score + order_score + ltv_score, 0.97)
                    tier = "High value" if prob >= 0.6 else ("Medium value" if prob >= 0.35 else "Low value")
                    r1, r2 = st.columns(2)
                    r1.metric("Conversion probability", f"{prob:.1%}", border=True)
                    r2.metric("Predicted tier", tier, border=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 8 — AI ANALYST
# ══════════════════════════════════════════════════════════════════════════════
with tabs[7]:
    st.subheader("Governed AI analyst")

    _api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not _api_key:
        st.caption(":material/key: Set ANTHROPIC_API_KEY to enable real AI answers.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        avatar = ":material/robot:" if msg["role"] == "assistant" else None
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
            if msg.get("dataframe") is not None:
                st.dataframe(msg["dataframe"], use_container_width=True)

    if not st.session_state.messages:
        SUGGESTIONS = {
            "📈 Blended ROAS?":         "What is our blended ROAS across all paid channels?",
            "💰 Top revenue channels?": "Which channels drive the most revenue and how much?",
            "🎯 Funnel conversion?":    "Show me funnel conversion rates from sessions to orders.",
            "🤝 Open pipeline value?":  "What is our total open pipeline value in HubSpot and Salesforce?",
        }
        selected = st.pills("Quick questions:", list(SUGGESTIONS.keys()), label_visibility="collapsed")
        if selected:
            st.session_state.messages.append({"role": "user", "content": SUGGESTIONS[selected]})
            st.rerun()

    if prompt := st.chat_input("Ask about ROAS, CAC, pipeline, lead trends, products…"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar=":material/robot:"):
            if not _api_key:
                fallback = "Please set **ANTHROPIC_API_KEY** to enable the AI analyst."
                st.markdown(fallback)
                st.session_state.messages.append({"role": "assistant", "content": fallback})
            else:
                with st.spinner("Querying the warehouse…"):
                    schema = get_db_schema()
                    system_prompt = f"""You are an analytics assistant for a full-funnel marketing platform.
The DuckDB warehouse covers e-commerce and marketing data from 2024-03-30 to 2026-03-15.
ALWAYS use the query_database tool to fetch real numbers — never guess or invent data.
Write clean DuckDB SQL. Limit results to 20 rows unless asked otherwise.
After fetching data, give a concise business-focused answer (2–4 sentences).

Available tables:
{schema}"""

                    tools = [{
                        "name": "query_database",
                        "description": "Execute a DuckDB SQL query and return results.",
                        "input_schema": {
                            "type": "object",
                            "properties": {"sql": {"type": "string", "description": "Valid DuckDB SQL."}},
                            "required": ["sql"],
                        },
                    }]

                    client = anthropic.Anthropic(api_key=_api_key)
                    api_messages = [{"role": "user", "content": prompt}]
                    result_df = None
                    final_text = ""

                    for _ in range(6):
                        response = client.messages.create(
                            model="claude-haiku-4-5-20251001",
                            max_tokens=1024,
                            system=system_prompt,
                            tools=tools,
                            messages=api_messages,
                        )
                        if response.stop_reason == "tool_use":
                            api_messages.append({"role": "assistant", "content": response.content})
                            tool_results = []
                            for block in response.content:
                                if block.type == "tool_use":
                                    df, err = run_sql(block.input["sql"])
                                    tool_content = f"SQL error: {err}" if err else df.to_string(index=False, max_rows=20)
                                    if df is not None:
                                        result_df = df
                                    tool_results.append({
                                        "type": "tool_result",
                                        "tool_use_id": block.id,
                                        "content": tool_content,
                                    })
                            api_messages.append({"role": "user", "content": tool_results})
                        else:
                            for block in response.content:
                                if hasattr(block, "text"):
                                    final_text = block.text
                            break

                    st.markdown(final_text or "_No response generated._")
                    if result_df is not None and not result_df.empty:
                        st.dataframe(result_df, use_container_width=True)

                    st.session_state.messages.append({
                        "role": "assistant", "content": final_text, "dataframe": result_df,
                    })


# ══════════════════════════════════════════════════════════════════════════════
# TAB 9 — DATA EXPLORER
# ══════════════════════════════════════════════════════════════════════════════
with tabs[8]:
    st.subheader("Data explorer")

    col_a, col_b = st.columns([2, 1])
    with col_a:
        table_list = q("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")["name"].tolist()
        selected_table = st.selectbox("Select table", table_list)
    with col_b:
        row_limit = st.number_input("Row limit", min_value=10, max_value=10000, value=100, step=50)

    if selected_table:
        schema_df = q(f"DESCRIBE {selected_table}")
        row_count = q(f"SELECT COUNT(*) as cnt FROM {selected_table}")["cnt"].iloc[0]

        with st.container(horizontal=True):
            st.metric("Rows",    f"{row_count:,}",    border=True)
            st.metric("Columns", str(len(schema_df)), border=True)

        with st.expander("Schema", expanded=False, icon=":material/schema:"):
            st.dataframe(schema_df, use_container_width=True, hide_index=True)

        data = q(f"SELECT * FROM {selected_table} LIMIT {row_limit}")
        st.dataframe(data, use_container_width=True)

        with st.container(border=True):
            st.markdown("**Custom SQL query**")
            custom_sql = st.text_area("", value=f"SELECT * FROM {selected_table} LIMIT 10",
                                      height=90, label_visibility="collapsed")
            if st.button("Run query", type="primary", icon=":material/play_arrow:"):
                df, err = run_sql(custom_sql)
                if err:
                    st.error(f"SQL error: {err}", icon=":material/error:")
                elif df is not None:
                    st.success(f"{len(df)} rows returned", icon=":material/check_circle:")
                    st.dataframe(df, use_container_width=True)

st.space("small")
st.caption(f"Full-funnel AI analytics · DuckDB + dbt · {env} · {S} → {E}")
