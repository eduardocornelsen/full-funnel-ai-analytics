# Plan 2: Visual Connector Interface for Data Sources and Live Dashboards

## Context

The project connects to data through hardcoded Python scripts and mock MCP servers with no UI for configuring sources, uploading files, or managing connections. This plan adds a Streamlit "Data Sources" page (the Streamlit app at `streamlit_app/app.py` already exists at 73KB) and clarifies what "live dashboards" means across different environments.

---

## Live Dashboards: What's Actually Possible

| Environment | Interactive charts | Live server-side data | Notes |
|-------------|-------------------|-----------------------|-------|
| **Claude Code artifacts** | ✅ Yes (Chart.js, D3) | ❌ No (reads static snapshot) | Current approach — works well |
| **Streamlit (this project)** | ✅ Yes | ✅ Yes | Right tool for live data |
| **HTML in browser** | ✅ Yes | ✅ Via fetch() to FastAPI | Needs running server |
| **Perplexity** | ❌ No | ❌ No | No code execution environment |

**Conclusion:** Claude Code is correct for snapshot-based read-only dashboards (already done). Streamlit is the right tool for live, interactive, warehouse-connected dashboards. Plan 1's daily CI keeps `golden_metrics.json` fresh, which means Claude Code dashboards are always current.

---

## What Was Built

### 1. Streamlit "Data Sources" Page (`streamlit_app/pages/connectors.py`)

Three-tab page added automatically to Streamlit navigation:

**Tab 1 — File Upload**
- Drag-and-drop CSV or Excel upload
- Column preview (first 20 rows)
- Column mapper: match uploaded columns to canonical schema (date, channel, spend, sessions, conversions)
- "Import as..." dropdown: choose which mock table to replace
- Writes to `data/mock_marketing/<table>.csv` on submit

**Tab 2 — Warehouse Connection**
- Dropdown: DuckDB / BigQuery / Snowflake
- Connection form (project/account/path + credentials)
- "Test Connection" button — runs `SELECT 1`
- "Save as Default" — writes to `~/.full_funnel_connectors.json` (outside repo, never committed)
- Live status indicator per saved connection

**Tab 3 — MCP Server Status**
- Lists all 6 servers from `.mcp.json`
- Source CSV path + row count for mock servers
- Last-seen timestamp for dbt-semantic-layer
- "Reload" button per server

### 2. Shared Connection Registry (`streamlit_app/lib/connector_registry.py`)

```python
class ConnectorRegistry:
    def get_active_connection(target: str) -> Connection
    def test_connection(config: dict) -> bool
    def list_available_tables(connection) -> list[str]
    def preview_table(connection, table, limit=20) -> pd.DataFrame
```

Reused by both the Streamlit pages and CLI scripts.

### 3. Sidebar Connection Badge

`streamlit_app/app.py` gains a small connection status indicator in the sidebar:
- 🟢 Warehouse connected (BigQuery/Snowflake)
- 🟡 DuckDB local
- 🔴 No connection / DB not found

---

## Files Created/Modified

| Action | File |
|--------|------|
| Created | `streamlit_app/pages/connectors.py` |
| Created | `streamlit_app/lib/__init__.py` |
| Created | `streamlit_app/lib/connector_registry.py` |
| Modified | `streamlit_app/app.py` — sidebar connection badge |
| Modified | `requirements.txt` — added `openpyxl` |

---

## Running the Connector UI

```bash
# Start the app
streamlit run streamlit_app/app.py

# Navigate to "Connectors" in the sidebar
# Tab 1: Upload a CSV → maps columns → replaces mock data
# Tab 2: Enter DuckDB path → Test Connection → green status
# Tab 3: View MCP server status and row counts
```
