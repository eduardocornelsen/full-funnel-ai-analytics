# Mock MCP Servers

This document explains how the five mock MCP servers in this project work — what they are, how they serve data, how AI clients connect to them, and how to swap them for real production APIs.

---

## Table of Contents

1. [What is MCP?](#1-what-is-mcp)
2. [Why mock servers?](#2-why-mock-servers)
3. [How a server is built](#3-how-a-server-is-built)
4. [The five mock servers](#4-the-five-mock-servers)
   - [Google Ads](#google-ads-mock_google_ads_serverpy)
   - [Meta Ads](#meta-ads-mock_meta_ads_serverpy)
   - [GA4](#ga4-mock_ga4_serverpy)
   - [HubSpot](#hubspot-mock_hubspot_serverpy)
   - [Salesforce](#salesforce-mock_salesforce_serverpy)
5. [How date filtering works](#5-how-date-filtering-works)
6. [Configuration (.mcp.json)](#6-configuration-mcpjson)
7. [Running servers locally](#7-running-servers-locally)
8. [Swapping mock → production](#8-swapping-mock--production)

---

## 1. What is MCP?

**Model Context Protocol (MCP)** is an open protocol that lets AI clients (Claude, OpenCode, Gemini CLI, etc.) call structured tools exposed by external servers. From the AI's perspective, an MCP server is a set of typed function calls — the same interface regardless of whether the data comes from a CSV file or a live SaaS API.

This project uses [**FastMCP**](https://github.com/jlowin/fastmcp) — a Python library that turns decorated functions into MCP-compliant tool definitions with a single `@mcp.tool()` decorator.

```
AI Client (Claude / OpenCode / Gemini)
        │
        │  MCP protocol (stdin/stdout)
        ▼
FastMCP server  ──►  reads CSV  ──►  returns JSON
```

---

## 2. Why mock servers?

The project ships with mock servers for three reasons:

| Reason | Detail |
|--------|--------|
| **Zero credentials** | No API keys, OAuth flows, or billing accounts needed to run the full platform |
| **Reproducible data** | Synthetic CSVs have fixed, version-controlled data — dashboards and tests produce the same output every time |
| **Identical interface** | Every mock server uses the exact same tool signatures as the corresponding real platform API. Swapping to production requires zero code changes |

The trade-off: mock servers read from static CSV files and do not reflect live campaign changes. See [§8 Swapping mock → production](#8-swapping-mock--production) for how to connect to real platforms.

---

## 3. How a server is built

Every mock server follows the same four-line pattern:

```python
from fastmcp import FastMCP
import pandas as pd
from pathlib import Path

mcp = FastMCP("Server Name")                            # 1. Create named server
DATA_DIR = Path(__file__).parent.parent / "data" / "mock_marketing"

@mcp.tool()                                             # 2. Decorate each tool
def my_tool(start_date: str = None, end_date: str = None):
    """Docstring becomes the tool description shown to the AI."""
    df = pd.read_csv(DATA_DIR / "source_file.csv")     # 3. Read from CSV
    # ... filter and aggregate ...
    return df.to_dict(orient="records")                 # 4. Return JSON

if __name__ == "__main__":
    mcp.run()                                           # 5. Start the server
```

FastMCP reads the type annotations and docstrings to generate the tool schema that AI clients use to call the function correctly.

---

## 4. The five mock servers

### Google Ads — `mock_google_ads_server.py`

**Data source:** `data/mock_marketing/google_ads_daily_performance.csv`

| Tool | Description | Returns |
|------|-------------|---------|
| `get_campaign_performance(start_date, end_date)` | Aggregated performance per campaign for the date range | `campaign_id`, `campaign_name`, `campaign_type`, `impressions`, `clicks`, `cost`, `conversions`, `ctr`, `cpc`, `cvr` |
| `list_campaigns()` | All distinct campaigns | `campaign_id`, `campaign_name`, `campaign_type` |

**Notes:**
- `cost` is in USD — use this field for Google ROAS calculations (never `spend`)
- `cvr` in the raw response is click-based (`conversions / clicks`) — label it `CVR (click)` per CLAUDE.md §1

---

### Meta Ads — `mock_meta_ads_server.py`

**Data source:** `data/mock_marketing/meta_ads_daily_performance.csv`

| Tool | Description | Returns |
|------|-------------|---------|
| `get_campaign_insights(start_date, end_date)` | Aggregated performance per campaign | `campaign_id`, `campaign_name`, `objective`, `impressions`, `reach`, `spend`, `link_clicks`, `purchases`, `cpm`, `cpc`, `roas` |
| `list_campaigns()` | All distinct campaigns | `campaign_id`, `campaign_name`, `objective` |

**Notes:**
- `spend` is in USD — use this field for Meta spend (never `cost`)
- `roas` is the platform-reported ROAS (last-click, 7-day window) — use it directly, do not recalculate
- `purchases` maps to "conversions" in the funnel

---

### GA4 — `mock_ga4_server.py`

**Data source:** `data/mock_marketing/ga4_daily_sessions.csv`

| Tool | Description | Returns |
|------|-------------|---------|
| `get_traffic_by_channel(start_date, end_date)` | Session metrics grouped by channel | `channel_group`, `sessions`, `engaged_sessions`, `conversions`, `engagement_rate`, `conversion_rate` |
| `get_daily_trends(channel)` | Daily sessions and conversions, optionally filtered by channel | `date`, `sessions`, `conversions` |

**Notes:**
- `conversion_rate` in the response is session-based (`conversions / sessions`) — this is `CVR (session)` per CLAUDE.md §1
- `channel_group` values: `Paid Search`, `Paid Social`, `Organic Search`, `Email`, `Direct`, `Referral`

---

### HubSpot — `mock_hubspot_server.py`

**Data sources:**
- `data/mock_marketing/hubspot_contacts.csv`
- `data/mock_marketing/hubspot_deals.csv`

| Tool | Description | Returns |
|------|-------------|---------|
| `get_contacts_summary()` | Contact distribution by lifecycle stage and city | `lifecycle_stages` (dict), `top_cities` (dict), `total_contacts` (int) |
| `get_deal_pipeline_summary(start_date, end_date)` | Deal stage breakdown, filtered by `create_date` | `deal_stage`, `deal_count`, `total_value` |
| `search_contacts(query)` | Find contacts by email, first name, or last name | Top 10 matching rows |

**Critical notes:**
- `get_contacts_summary()` has **no date filter** — it returns the all-time lifetime count. This is intentional and matches real HubSpot behaviour. Never compare this number against a 90-day attributed revenue figure (see CLAUDE.md §5 Funnel Integrity Rules)
- `get_deal_pipeline_summary()` **does** accept dates — pass `start_date=2025-12-16`, `end_date=2026-03-15` when comparing pipeline to 90-day ad spend

---

### Salesforce — `mock_salesforce_server.py`

**Data source:** `data/mock_marketing/salesforce_opportunities.csv`

| Tool | Description | Returns |
|------|-------------|---------|
| `get_opportunity_pipeline(start_date, end_date)` | Opportunities by stage, filtered by `close_date` | `stage`, `opportunity_count`, `amount`, `expected_revenue` |
| `get_revenue_by_source(start_date, end_date)` | Closed-won revenue broken down by lead source | `lead_source`, `closed_won_count`, `total_revenue` |

**Notes:**
- Filter by `close_date` to align with the 90-day analysis window
- `expected_revenue` is `amount × probability` — use only for pipeline estimates, not as actual revenue

---

## 5. How date filtering works

All five servers accept optional `start_date` / `end_date` parameters in `YYYY-MM-DD` format. If omitted, the server returns all available data.

**Canonical dates for this project's synthetic dataset:**

```
start_date = 2025-12-16   # 90 days before the anchor date
end_date   = 2026-03-15   # anchor date (dataset boundary)
```

Always pass explicit dates to avoid cross-period contamination. The golden-layer skills pass these dates automatically — you only need to specify them when querying MCP servers directly (the `-mcp` skill variants).

---

## 6. Configuration (`.mcp.json`)

The `.mcp.json` file at the project root tells AI clients how to start each server:

```json
{
  "mcpServers": {
    "google-ads": {
      "command": "python",
      "args": ["mcp_servers/mock_google_ads_server.py"]
    },
    "meta-ads": {
      "command": "python",
      "args": ["mcp_servers/mock_meta_ads_server.py"]
    },
    "ga4": {
      "command": "python",
      "args": ["mcp_servers/mock_ga4_server.py"]
    },
    "hubspot": {
      "command": "python",
      "args": ["mcp_servers/mock_hubspot_server.py"]
    },
    "salesforce": {
      "command": "python",
      "args": ["mcp_servers/mock_salesforce_server.py"]
    },
    "dbt-semantic-layer": {
      "command": "uvx",
      "args": ["dbt-mcp", "--project-dir", "dbt_project", "--target", "duckdb"]
    }
  }
}
```

Claude Code reads this file automatically. For Claude Desktop, use `mcp_servers/claude_desktop_config.example.json` as the template.

---

## 7. Running servers locally

The servers are managed by the AI client — they start and stop automatically when you open/close a conversation. You do not normally need to start them manually.

To test a server in isolation:

```bash
# Start a server directly
python mcp_servers/mock_google_ads_server.py

# Or via the MCP inspector (requires @modelcontextprotocol/inspector)
npx @modelcontextprotocol/inspector python mcp_servers/mock_google_ads_server.py
```

**Verify the data is available** before starting any server (required one-time setup):

```bash
python scripts/generate_mock_marketing_data.py
```

This creates the six CSV files in `data/mock_marketing/`. See [setup_guide.md](guides/setup_guide.md) for the full first-run sequence.

---

## 8. Swapping mock → production

The mock servers are drop-in replacements for real platform clients. To switch to live data, replace the server file with a production MCP implementation — no changes needed to `.mcp.json` or any dashboard/skill code.

| Platform | Production replacement |
|----------|----------------------|
| **Google Ads** | [google-ads-mcp](https://github.com/google-gemini/gemini-fullstack-langgraph-quickstart) or the official Google Ads Python client wrapped in FastMCP |
| **Meta Ads** | Meta Marketing API v20+ wrapped in FastMCP |
| **GA4** | Google Analytics Data API (GA4) wrapped in FastMCP |
| **HubSpot** | [HubSpot MCP server](https://developers.hubspot.com/docs/api/overview) via FastMCP |
| **Salesforce** | Salesforce REST API or SOQL wrapper in FastMCP |
| **dbt Semantic Layer** | [dbt-mcp](https://github.com/dbt-labs/dbt-mcp) pointing at BigQuery/Snowflake target |

The key constraint: your production server must expose tools with the **same names and parameter signatures** as the mock. If you add new fields to the response, that's fine — the skills and dashboards only use the fields they know about.

For a full walkthrough of replacing all mock data sources, see [Data Import Guide](guides/data_import_guide.md).
