"""
Data Sources — connector management page.
Accessible from the Streamlit sidebar automatically (pages/ directory).
"""

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.connector_registry import (  # noqa: E402
    load_config,
    preview_table,
    save_connection,
    test_connection,
)

PROJECT_ROOT = Path(__file__).parent.parent.parent
MOCK_DIR = PROJECT_ROOT / "data" / "mock_marketing"
MCP_CONFIG_PATH = PROJECT_ROOT / ".mcp.json"

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Data Sources · Full-Funnel Analytics",
    page_icon=":material/link:",
    layout="wide",
)

st.title("Data Sources")
st.caption("Configure connections, upload files, and monitor MCP server status.")

tab_upload, tab_warehouse, tab_mcp = st.tabs(
    ["📂 File Upload", "🏭 Warehouse Connection", "🔌 MCP Servers"]
)

# ── Tab 1: File Upload ─────────────────────────────────────────────────────────
with tab_upload:
    st.subheader("Import CSV / Excel")
    st.write(
        "Upload a CSV or Excel file and map its columns to one of the synthetic "
        "mock data tables. The file replaces the existing CSV so the next `dbt run` "
        "picks it up automatically."
    )

    _TABLE_OPTIONS = {
        "google_ads_daily_performance": "Google Ads daily performance",
        "meta_ads_daily_performance":   "Meta Ads daily performance",
        "ga4_daily_sessions":           "GA4 daily sessions",
        "hubspot_contacts":             "HubSpot contacts",
        "hubspot_deals":                "HubSpot deals",
        "salesforce_opportunities":     "Salesforce opportunities",
    }

    uploaded = st.file_uploader("Upload file", type=["csv", "xlsx", "xls"])

    if uploaded:
        try:
            if uploaded.name.endswith((".xlsx", ".xls")):
                df = pd.read_excel(uploaded)
            else:
                df = pd.read_csv(uploaded)
        except Exception as exc:
            st.error(f"Could not read file: {exc}")
            df = None

        if df is not None:
            st.write(f"**{len(df):,} rows × {len(df.columns)} columns**")
            st.dataframe(df.head(20), use_container_width=True)

            target_table = st.selectbox(
                "Import as (replaces existing CSV):",
                list(_TABLE_OPTIONS.keys()),
                format_func=lambda k: _TABLE_OPTIONS[k],
            )

            if st.button("💾 Save to mock data", type="primary"):
                MOCK_DIR.mkdir(parents=True, exist_ok=True)
                out_path = MOCK_DIR / f"{target_table}.csv"
                df.to_csv(out_path, index=False)
                st.success(
                    f"Saved {len(df):,} rows to `data/mock_marketing/{target_table}.csv`.\n\n"
                    "Run `dbt run --target duckdb` to rebuild the mart tables."
                )
    else:
        st.info("Drag and drop a CSV or Excel file above to get started.")

# ── Tab 2: Warehouse Connection ────────────────────────────────────────────────
with tab_warehouse:
    st.subheader("Warehouse Connection")

    cfg = load_config()
    active = cfg.get("active", "duckdb")

    _status_icon = {"duckdb": "🟡 DuckDB local", "bigquery": "🟢 BigQuery", "snowflake": "🟢 Snowflake"}
    st.info(f"Active target: **{_status_icon.get(active, active)}**")

    target_choice = st.selectbox("Connection type:", ["duckdb", "bigquery", "snowflake"],
                                 index=["duckdb", "bigquery", "snowflake"].index(active))

    params: dict = {}

    if target_choice == "duckdb":
        default_path = cfg.get("connections", {}).get("duckdb", {}).get(
            "path", str(PROJECT_ROOT / "data" / "olist_analytics.duckdb")
        )
        params["path"] = st.text_input("DuckDB file path:", value=default_path)

    elif target_choice == "bigquery":
        saved_bq = cfg.get("connections", {}).get("bigquery", {})
        params["project"] = st.text_input("GCP Project ID:", value=saved_bq.get("project", ""))
        st.caption("Ensure GOOGLE_APPLICATION_CREDENTIALS is set or you are logged in via `gcloud auth`.")

    elif target_choice == "snowflake":
        saved_sf = cfg.get("connections", {}).get("snowflake", {})
        c1, c2 = st.columns(2)
        with c1:
            params["account"]   = st.text_input("Account:",   value=saved_sf.get("account", ""))
            params["user"]      = st.text_input("User:",      value=saved_sf.get("user", ""))
            params["warehouse"] = st.text_input("Warehouse:", value=saved_sf.get("warehouse", "ANALYTICS_WH"))
        with c2:
            params["password"] = st.text_input("Password:", type="password", value="")
            params["database"] = st.text_input("Database:", value=saved_sf.get("database", "OLIST_ANALYTICS"))
            params["schema"]   = st.text_input("Schema:",   value=saved_sf.get("schema", "PUBLIC"))

    col_test, col_save = st.columns([1, 2])
    with col_test:
        if st.button("🔍 Test connection"):
            with st.spinner("Testing ..."):
                ok, msg = test_connection(target_choice, params)
            if ok:
                st.success(msg)
            else:
                st.error(msg)

    with col_save:
        set_active = st.checkbox("Set as default active connection", value=True)
        if st.button("💾 Save connection", type="primary"):
            save_connection(target_choice, params, set_active=set_active)
            st.success(
                f"Connection saved to `~/.full_funnel_connectors.json`. "
                f"{'Set as active.' if set_active else ''}"
            )

    # Preview table
    st.divider()
    st.subheader("Table Preview")
    preview_tbl = st.text_input("Table name to preview:", value="fct_marketing_daily")
    if st.button("Preview"):
        try:
            with st.spinner("Querying ..."):
                df_prev = preview_table(target_choice, preview_tbl, limit=20)
            st.dataframe(df_prev, use_container_width=True)
        except Exception as exc:
            st.error(f"Preview failed: {exc}")

# ── Tab 3: MCP Server Status ───────────────────────────────────────────────────
with tab_mcp:
    st.subheader("MCP Server Status")

    if not MCP_CONFIG_PATH.exists():
        st.warning(".mcp.json not found at project root.")
    else:
        mcp_cfg = json.loads(MCP_CONFIG_PATH.read_text())
        servers = mcp_cfg.get("mcpServers", {})

        for name, conf in servers.items():
            with st.expander(f"🔌 {name}", expanded=False):
                cmd = conf.get("command", "")
                args = conf.get("args", [])
                st.code(f"{cmd} {' '.join(str(a) for a in args)}", language="bash")

                # Show CSV row counts for mock servers
                mock_map = {
                    "google-ads": ["google_ads_daily_performance.csv", "google_ads_campaigns.csv"],
                    "meta-ads":   ["meta_ads_daily_performance.csv", "meta_ads_campaigns.csv"],
                    "ga4":        ["ga4_daily_sessions.csv"],
                    "hubspot":    ["hubspot_contacts.csv", "hubspot_deals.csv"],
                    "salesforce": ["salesforce_opportunities.csv", "salesforce_accounts.csv"],
                }
                if name in mock_map:
                    for fname in mock_map[name]:
                        csv_path = MOCK_DIR / fname
                        if csv_path.exists():
                            nrows = sum(1 for _ in open(csv_path)) - 1  # exclude header
                            latest = ""
                            try:
                                df_csv = pd.read_csv(csv_path, usecols=["date"])
                                latest = f" · latest: {df_csv['date'].max()}"
                            except Exception:
                                pass
                            st.write(f"  ✅ `{fname}`: **{nrows:,} rows**{latest}")
                        else:
                            st.write(f"  ⚠️ `{fname}`: not found — run `generate_mock_marketing_data.py`")
                elif name == "dbt-semantic-layer":
                    st.write("dbt Semantic Layer MCP — queries dbt Cloud / local dbt project.")
