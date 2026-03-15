# 🚀 Full-Funnel AI Marketing Analytics Platform

![Status](https://img.shields.io/badge/status-work%20in%20progress-yellow?style=for-the-badge)
![Phase](https://img.shields.io/badge/phase-1%20of%206-blue?style=for-the-badge)

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![dbt](https://img.shields.io/badge/dbt-Core%20%2B%20MetricFlow-FF694B?style=flat-square&logo=dbt&logoColor=white)
![BigQuery](https://img.shields.io/badge/BigQuery-Free%20Tier-4285F4?style=flat-square&logo=googlebigquery&logoColor=white)
![Snowflake](https://img.shields.io/badge/Snowflake-Trial%20Demo-29B5E8?style=flat-square&logo=snowflake&logoColor=white)
![Databricks](https://img.shields.io/badge/Databricks-Trial%20Demo-FF3621?style=flat-square&logo=databricks&logoColor=white)
![DuckDB](https://img.shields.io/badge/DuckDB-Local%20Dev-FFF000?style=flat-square&logo=duckdb&logoColor=black)
![Supabase](https://img.shields.io/badge/Supabase-Postgres-3FCF8E?style=flat-square&logo=supabase&logoColor=white)
![Claude](https://img.shields.io/badge/Claude-Desktop%20%2B%20Cowork-D4A574?style=flat-square&logo=anthropic&logoColor=white)
![OpenCode](https://img.shields.io/badge/OpenCode-CLI%20Agent-00D1B2?style=flat-square&logo=opensourceinitiative&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini-CLI-4285F4?style=flat-square&logo=google&logoColor=white)
![Antigravity](https://img.shields.io/badge/Antigravity-IDE-34A853?style=flat-square&logo=google&logoColor=white)
![MLflow](https://img.shields.io/badge/MLflow-Experiment%20Tracking-0194E2?style=flat-square&logo=mlflow&logoColor=white)
![XGBoost](https://img.shields.io/badge/XGBoost-Lead%20Scoring-189FDD?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-Scoring%20API-009688?style=flat-square&logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)
![Looker Studio](https://img.shields.io/badge/Looker%20Studio-BI-4285F4?style=flat-square&logo=looker&logoColor=white)
![n8n](https://img.shields.io/badge/n8n-Automation-EA4B71?style=flat-square&logo=n8n&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)
![Cost](https://img.shields.io/badge/cost-%240%2Fmo%20base-brightgreen?style=flat-square)

**Natural language marketing analytics powered by MCP, dbt Semantic Layer, and ML lead scoring. Works with Claude Desktop, OpenCode, Gemini CLI, and Antigravity IDE.**

> *"Which channels actually drive revenue, not just clicks?"*
> This system answers that question in 15 seconds via natural language — backed by multi-touch attribution, a production ML scoring API, and dashboards fed from a single governed semantic layer across 5 data warehouses.

### 📊 Build Progress

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1: Data Foundation | ✅ Complete | Olist dataset + synthetic marketing data + warehouse loading |
| Phase 2: dbt Semantic Layer | ✅ Complete | 14 staging + 4 intermediate + 11 mart models + Core Build |
| Phase 3: AI Layer (MCP) | ✅ Complete | 7 MCP servers + 4 client configs (Claude, OpenCode, Gemini, Antigravity) |
| Phase 4: ML Scoring | 🟡 In progress | XGBoost + MLflow + FastAPI endpoint |
| Phase 5: Dashboards & Automation | 🔲 Not started | Looker Studio + Streamlit + n8n routing |
| Phase 6: Portability & Polish | 🔲 Not started | Snowflake/Databricks demos + documentation + video |

> Update status: 🔲 Not started · 🟡 In progress · ✅ Complete

---

## The Problem

Companies run ads across Google, Meta, and organic channels. Marketing claims leads, Sales says they're low quality, and the CEO asks: *"Where should we spend next quarter?"*

Answering this requires joining data from 5+ platforms, building attribution models, scoring leads, and making it all accessible to non-technical stakeholders. Most teams cobble together spreadsheets and one-off queries. This project builds the production system.

## What This Project Does

### Data Sources → MCP Servers → AI Clients
![full_funnel_architecture_flow](full_funnel_architecture_flow.svg)




### MCP Server Details

| MCP Server | What it exposes | Source | Key tools |
|---|---|---|---|
| **BigQuery** | Warehouse queries | `uvx mcp-server-bigquery` | `execute_query`, `list_tables`, `get_schema` |
| **dbt Semantic Layer** | Governed metrics + SQL generation | `uvx dbt-mcp` | `text_to_sql`, `get_metrics`, `get_dimensions` (60+ tools) |
| **Google Ads** | Campaign performance, keywords | `mock_google_ads_server.py` | `get_campaign_performance`, `get_keyword_performance`, `list_campaigns` |
| **Meta Ads** | Ad sets, reach, purchases | `mock_meta_ads_server.py` | `get_campaign_insights`, `get_ad_set_breakdown`, `list_campaigns` |
| **GA4** | Sessions, channels, conversions | `mock_ga4_server.py` | `get_traffic_by_channel`, `get_daily_trend`, `get_device_breakdown` |
| **HubSpot** | Contacts, deals, pipeline | `mock_hubspot_server.py` | `get_contacts_by_source`, `get_deal_pipeline`, `search_contacts` |
| **Salesforce** | Opportunities, accounts, revenue | `mock_salesforce_server.py` | `get_opportunity_pipeline`, `get_revenue_by_source`, `get_quarterly_forecast` |

> All mock servers use the same tool interface as real platform APIs. Swap mock → production with zero code changes.

### AI Client Comparison

| Client | MCP Support | Unique Strength | Primary Use | Cost |
|---|---|---|---|---|
| 🟣 **Claude Desktop** | Native (best) | Cowork plugin, React artifact rendering, multi-tool chaining | Portfolio demo, dashboard generation, non-technical user experience | $20/mo (optional) |
| 🟢 **OpenCode** | Native | 75+ models (Claude, Gemini, GPT, Llama, local), open source | Terminal workflows, model flexibility proof, CI/CD integration | Free + API costs |
| 🔵 **Gemini CLI** | Native | Native BigQuery integration, free generous rate limits | Quick warehouse queries, Google ecosystem, ad-hoc analysis | Free |
| 🟡 **Antigravity IDE** | Native (MCP Store) | Manager View with parallel agents, VS Code fork | Building the project itself, multi-agent coding | Free (preview) |

> **Key point:** The same 7 MCP servers work with ALL 4 clients. No code changes between clients.

### Three Heads, One Spine

| Head | What it does | Tools |
|------|-------------|-------|
| **🤖 AI Analytics** | Query marketing data in plain English, generate dashboards | 7 MCP servers → Claude Desktop (primary) + OpenCode + Gemini CLI + Antigravity |
| **🧠 ML Scoring** | Predict which leads become high-value customers | XGBoost → MLflow → FastAPI `/score` endpoint → n8n auto-routing |
| **📊 BI Dashboards** | Self-serve dashboards for marketing and sales teams | Looker Studio + Streamlit (4 pages) + Claude React artifacts |

## 🏗️ Architecture & Technical Stack

This project implements a modern data stack centered around a unified semantic layer, serving insights through AI, Machine Learning, and traditional BI—all running at a **$0/month base cost**.


```
┌─────────────────────────────────────────────────────────────────┐
│                       DATA SOURCES                               │
│  Google Ads · Meta Ads · GA4 · HubSpot · Salesforce (mock MCP) │
│                    + Olist Dataset (real)                        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
              ┌────────────▼────────────┐
              │    DATA WAREHOUSE       │
              │  BigQuery (free tier)   │  ← Primary
              │  DuckDB (local)         │  ← Dev
              │  Supabase (Postgres)    │  ← SQL demo
              │  Snowflake (trial)      │  ← Enterprise demo
              │  Databricks (trial)     │  ← Lakehouse demo
              └────────────┬────────────┘
                           │
              ┌────────────▼────────────┐
              │  dbt + MetricFlow       │
              │  Semantic Layer         │
              │                         │
              │  30+ models             │
              │  15+ governed metrics   │
              │  4 attribution models   │
              └────────────┬────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
   ┌──────▼──────┐  ┌─────▼─────┐  ┌──────▼──────┐
   │  AI Layer   │  │ ML Layer  │  │  BI Layer   │
   │             │  │           │  │             │
   │ 7 MCP      │  │ XGBoost   │  │ Looker      │
   │ servers     │  │ MLflow    │  │ Studio      │
   │ Claude Dskp│  │ FastAPI   │  │ Streamlit   │
   │ OpenCode   │  │ n8n       │  │ React       │
   │ Gemini CLI │  │ routing   │  │ artifacts   │
   │ Antigravity│  │           │  │             │
   └─────────────┘  └───────────┘  └─────────────┘
```

---

### ☁️ Data Warehouse Strategy
We leverage a multi-warehouse approach to balance cost-efficiency with high-performance processing.

| Provider | Recommendation | Pricing & Limits |
| :--- | :--- | :--- |
| **BigQuery** | Primary warehouse for scaled analytics | **Free 10GB** storage + 1TB query/mo |
| **DuckDB** | High-speed local processing & testing | **Free** (Local/Open Source) |
| **Supabase** | Backend for Postgres-centric apps | **Free 500MB** database |
| **Snowflake** | Professional/Enterprise scale | **30-day trial** |
| **Databricks** | Spark workloads & heavy ML modeling | **14-day trial** |

---

### 🧠 The Three Pillars ("Three Heads, One Spine")

| Pillar | Focus | Core Tech Stack |
| :--- | :--- | :--- |
| **🤖 AI Layer** | Natural language queries & automated insights | 7 MCP Servers, Claude Desktop, OpenCode, Gemini CLI, Antigravity |
| **🧠 ML Layer** | Predictive lead scoring & automated routing | XGBoost, Polars, MLflow, FastAPI (`/score`), n8n |
| **📊 BI Layer** | Executive reporting & interactive tools | Looker Studio, Streamlit, Plotly, React Artifacts |

### 🛠️ Key Technical Details
* **Data Origin:** Real dataset via **Olist (Kaggle)**, live API via **Open-Meteo**, and mock marketing APIs.
* **Semantic Layer:** Powered by **dbt + MetricFlow**, ensuring governed metrics are consumed identically by AI, ML, and BI layers.
* **Protocol:** Built entirely on the **Model Context Protocol (MCP)** for zero-friction tool integration.


## Demo

### Hero Query
> *"Show me the complete marketing funnel for Q1 2018: ad spend across Google and Meta, website sessions by channel, lead conversion rates, and final revenue. Calculate blended CAC and ROAS."*

The AI client queries the dbt semantic layer, executes against BigQuery via MCP, pulls GA4 traffic and CRM pipeline data from mock platform servers, and returns a formatted analysis with KPI cards, charts, and recommendations — all in ~15 seconds. Works from Claude Desktop, OpenCode, Gemini CLI, or Antigravity IDE.

**[▶ Watch the demo video →](./demo/demo_video_link.md)**

### Other queries this system handles
- *"Compare first-touch vs last-touch attribution for our top channels"*
- *"Score this lead: came from Google Ads, visited 5 pages, 3 min on site"*
- *"Which product categories have the highest CAC but lowest LTV?"*
- *"What should we change about our ad spend next quarter?"*

## Stack & Cost

**Total base cost: $0/month.** Claude Pro ($20/mo) optional for Cowork plugin + React artifacts.

| Component | Tool | Cost |
|-----------|------|------|
| Primary Warehouse | BigQuery | $0 — 10GB + 1TB queries/month free |
| Local Dev | DuckDB | $0 — open source |
| Postgres Demo | Supabase | $0 — 500MB free |
| Semantic Layer | dbt Core + MetricFlow | $0 — open source |
| ML Tracking | MLflow | $0 — open source, self-hosted |
| Scoring API | FastAPI | $0 — open source |
| Automation | n8n | $0 — self-hosted |
| BI Dashboards | Looker Studio | $0 — free with Google |
| Interactive App | Streamlit | $0 — community cloud |
| Weather API | Open-Meteo | $0 — no key needed |
| MCP Servers | Open source | $0 |
| **AI: Claude Desktop** | **Cowork + React artifacts** | **$20/month (optional)** |
| **AI: OpenCode** | **Terminal + 75 models** | **$0 (free + API costs)** |
| **AI: Gemini CLI** | **BigQuery native** | **$0 (free generous limits)** |
| **AI: Antigravity IDE** | **Parallel agents** | **$0 (free public preview)** |

Enterprise warehouse demos use free trials: Snowflake (30-day, ~$400 credits) and Databricks (14-day).

## Quick Start

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/full-funnel-ai-analytics.git
cd full-funnel-ai-analytics

# 2. Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Fill in credentials

# 3. Download data
python scripts/download_olist_data.py
python scripts/generate_mock_marketing_data.py

# 4. Load into warehouses
python scripts/load_bigquery.py
python scripts/load_duckdb.py

# 5. Build dbt models
cd dbt_project && dbt build --target bigquery && cd ..

# 6. Start ML tracking
bash scripts/run_mlflow_server.sh &

# 7. Train lead scoring model
python ml/src/train.py

# 8. Start scoring API
cd api && uvicorn main:app --port 8000 &

# 9. Configure MCP servers for your preferred client(s)

# Claude Desktop:
cp mcp_servers/claude_desktop_config.example.json \
   ~/Library/Application\ Support/Claude/claude_desktop_config.json
# Edit with your paths and credentials

# OpenCode (config already at .opencode/opencode.json):
opencode  # launch and verify MCP tools detected

# Gemini CLI:
gemini --mcp-server "bigquery=uvx mcp-server-bigquery --project YOUR_PROJECT"

# 10. Query your data in natural language from ANY client:
# "Show me blended ROAS across Google and Meta for Q1 2018,
#  with attribution model comparison and lead quality breakdown."
```

## Project Structure

```
full-funnel-ai-analytics/
├── dbt_project/                    # Semantic layer + transformations
│   ├── models/
│   │   ├── staging/                #   14 staging models (Olist + marketing)
│   │   ├── intermediate/           #   4 intermediate (LTV, funnel, unified campaigns)
│   │   ├── marts/                  #   11 mart models (facts + dimensions)
│   │   ├── semantic_models/        #   MetricFlow definitions
│   │   └── metrics/                #   15+ governed metrics
│   └── macros/                     #   Attribution model logic + cross-db helpers
│
├── mcp_servers/                    # 7 MCP servers (work with all 4 clients)
│   ├── mock_google_ads_server.py   #   Campaign performance, keywords, ROAS
│   ├── mock_meta_ads_server.py     #   Ad sets, reach, purchases, ROAS
│   ├── mock_ga4_server.py          #   Sessions, channels, conversions
│   ├── mock_hubspot_server.py      #   Contacts, deals, pipeline
│   ├── mock_salesforce_server.py   #   Opportunities, accounts, revenue
│   └── weather_server.py           #   Open-Meteo historical weather
│
├── cowork_plugin/                  # Claude Desktop Cowork plugin
│   ├── commands/                   #   /marketing, /attribution, /pipeline, /score
│   └── skills/                     #   Brand voice, metric definitions, workflows
│
├── .opencode/                      # OpenCode CLI config + commands + skills
│   ├── opencode.json               #   MCP server config
│   ├── commands/                   #   Same commands as Cowork (OpenCode format)
│   └── skills/                     #   Same skills (SKILL.md format)
│
├── ml/                             # Lead scoring ML pipeline
│   ├── src/train.py                #   XGBoost training with MLflow tracking
│   └── notebooks/                  #   EDA, training, evaluation notebooks
│
├── api/                            # FastAPI lead scoring endpoint
│   ├── main.py                     #   POST /score, GET /health, GET /model-info
│   └── Dockerfile                  #   Containerized deployment
│
├── automation/                     # n8n lead routing workflow
│   └── n8n_workflow.json
│
├── streamlit_app/                  # Interactive AI dashboard
│   └── app.py
│
├── scripts/                        # Data download + loading
│   ├── download_olist_data.py
│   ├── generate_mock_marketing_data.py
│   ├── load_bigquery.py
│   ├── load_duckdb.py
│   └── load_supabase.py
│
├── warehouse_configs/              # Setup scripts per warehouse
│   ├── bigquery/
│   ├── snowflake/
│   ├── databricks/
│   ├── supabase/
│   └── duckdb/
│
└── docs/                           # Architecture, cost analysis, guides
    ├── architecture.md
    ├── warehouse_swap_guide.md
    └── mock_vs_real_integrations.md
```

## Key Design Decisions

### Why MCP instead of LangChain?
MCP is an open standard (Linux Foundation) for AI tool calling — it eliminates the middleware layer that LangChain adds. The result is simpler code, fewer dependencies, and a direct connection between any LLM client and data sources. Unlike LangChain, which ties you to its abstraction layer, MCP servers work with Claude Desktop, OpenCode, Gemini CLI, Antigravity IDE, Cursor, and any future MCP-compatible client.

### Why mock MCP servers?
The mock servers expose the **exact same tool interface** as real platform APIs. When you swap mock → production (connecting real Google Ads or HubSpot accounts), all client configurations, commands, and dashboards work without any code changes. This proves the MCP abstraction layer works — and that the system is both vendor-agnostic and LLM-agnostic.

### Why MetricFlow?
When AI writes SQL on behalf of a marketing manager who can't verify it, you need guaranteed correctness. MetricFlow ensures "ROAS" always means `SUM(attributed_revenue) / SUM(ad_spend)` with the correct filters and joins — defined once in YAML, consumed everywhere.

### Why 5 warehouses?
Not because you'd run 5 in production — but because it proves the semantic layer is truly warehouse-agnostic. Same dbt models, same metrics, same MCP interface, different execution engine. This directly addresses the hiring manager who says *"but we use Snowflake"* — you show it working on Snowflake.

### Why 4 AI clients?
Same principle as warehouses — it proves the MCP architecture is LLM-agnostic. The 7 MCP servers work identically with Claude, Gemini, GPT, or local models. This directly addresses *"but we use GPT-4"* — you show the same servers working with any client.

| Client | Unique strength | Use it for |
|---|---|---|
| **Claude Desktop** | Cowork plugin, React artifacts, best MCP UX | Portfolio demo video, non-technical user experience |
| **OpenCode** | 75+ models, open source, terminal-native | Terminal workflows, model flexibility demo |
| **Gemini CLI** | Native BigQuery integration, free generous limits | Quick warehouse queries, Google ecosystem demo |
| **Antigravity IDE** | Manager View (parallel agents), VS Code fork | Building the project, multi-agent coding |

## Metrics Governed by the Semantic Layer

| Metric | Definition | Category |
|--------|-----------|----------|
| Blended CAC | Total ad spend / New customers | Marketing |
| Blended ROAS | Attributed revenue / Total ad spend | Marketing |
| Channel ROAS | Revenue (per model) / Channel spend | Attribution |
| First-Touch Revenue | Revenue credited to first interaction | Attribution |
| Last-Touch Revenue | Revenue credited to last interaction | Attribution |
| Linear Revenue | Revenue split equally across touchpoints | Attribution |
| AOV | Total revenue / Total orders | Revenue |
| Customer LTV | Predicted lifetime revenue per customer | Revenue |
| Lead Score | ML-predicted probability of high-value conversion | Scoring |
| Pipeline Velocity | Weighted pipeline value / Days in period | Pipeline |
| Win Rate | Closed Won / (Closed Won + Closed Lost) | Pipeline |
| Conversion Rate | Conversions / Sessions | Website |

## Target Roles This Project Supports

| Role | What they see in this project |
|------|------------------------------|
| **Paid Media / Growth Analytics** | Multi-touch attribution (4 models), ROAS by channel, spend optimization |
| **RevOps Analyst** | Full-funnel pipeline, CRM integration, lead routing automation |
| **Data Scientist** | XGBoost lead scoring, MLflow experiment tracking, FastAPI deployment |
| **Analytics Engineer** | dbt semantic layer, MCP architecture, multi-warehouse + multi-client portability |
| **BI / Data Analyst** | Looker Studio dashboards, Streamlit app, Voi-style React artifacts |
| **Marketing Analyst** | CAC/LTV analysis, channel comparison, attribution model comparison |

## Swapping to Real Platform Data

Every mock MCP server has a production equivalent:

| Mock Server | Production Swap | Setup |
|---|---|---|
| `mock_google_ads_server.py` | `cohnen/mcp-google-ads` | Google Ads API developer token + OAuth |
| `mock_meta_ads_server.py` | `meta-ads-mcp-server` (npx) | Meta access token with ads_read |
| `mock_ga4_server.py` | GrowthSpree GA4 MCP | Google OAuth |
| `mock_hubspot_server.py` | Official HubSpot MCP | HubSpot access token |
| `mock_salesforce_server.py` | Airbyte agent connector | Salesforce Connected App |

For batch ETL (loading historical data into your warehouse), use **Airbyte Open Source** (self-hosted, free, 600+ connectors) or **dlt** (Python library, pip install).

## Switching Warehouses: BigQuery → Snowflake → Databricks

The entire stack is warehouse-agnostic. The same dbt models, MetricFlow metrics, MCP tool interfaces, client commands, and dashboards work across all five warehouses. Only connection config changes.

### What stays identical across ALL warehouses
- All dbt model SQL (Jinja handles dialect differences)
- All MetricFlow semantic model YAML and metric definitions
- All MCP server tool interfaces (any client calls the same tools)
- All client commands and skills (Cowork, OpenCode, Antigravity)
- FastAPI scoring endpoint, n8n workflows, Streamlit app
- Looker Studio dashboards (reconnect data source)

### What changes per warehouse
- `~/.dbt/profiles.yml` connection details
- One MCP server binary/config in `claude_desktop_config.json`
- Minor SQL dialect differences (handled automatically by dbt Jinja macros)

### Switch to Snowflake

**1. Sign up** at [signup.snowflake.com](https://signup.snowflake.com) — 30-day trial with ~$400 free credits.

**2. Create infrastructure:**
```sql
CREATE WAREHOUSE ANALYTICS_WH WITH WAREHOUSE_SIZE='XSMALL' AUTO_SUSPEND=60;
CREATE DATABASE OLIST_ANALYTICS;
CREATE SCHEMA OLIST_ANALYTICS.PUBLIC;

-- Read-only role for MCP
CREATE ROLE ANALYST_READONLY;
GRANT USAGE ON DATABASE OLIST_ANALYTICS TO ROLE ANALYST_READONLY;
GRANT USAGE ON SCHEMA OLIST_ANALYTICS.PUBLIC TO ROLE ANALYST_READONLY;
GRANT SELECT ON ALL TABLES IN SCHEMA OLIST_ANALYTICS.PUBLIC TO ROLE ANALYST_READONLY;
GRANT USAGE ON WAREHOUSE ANALYTICS_WH TO ROLE ANALYST_READONLY;
```

**3. Load data** — upload CSVs via Snowflake UI or stage from S3.

**4. Add dbt profile** in `~/.dbt/profiles.yml`:
```yaml
    snowflake:
      type: snowflake
      account: "{{ env_var('SNOWFLAKE_ACCOUNT') }}"
      user: "{{ env_var('SNOWFLAKE_USER') }}"
      password: "{{ env_var('SNOWFLAKE_PASSWORD') }}"
      warehouse: ANALYTICS_WH
      database: OLIST_ANALYTICS
      schema: PUBLIC
      threads: 4
```

**5. Build models:**
```bash
dbt build --target snowflake
```

**6. Connect MCP server** — add to `claude_desktop_config.json`:
```json
{
  "snowflake": {
    "command": "uvx",
    "args": ["--python=3.12", "mcp_snowflake_server",
             "--account", "your-account",
             "--warehouse", "ANALYTICS_WH",
             "--user", "your-user",
             "--password", "your-password",
             "--database", "OLIST_ANALYTICS",
             "--schema", "PUBLIC"]
  }
}
```

**7. Run the same hero query** — identical results, different engine.

**Snowflake bonus features:** Snowflake Managed MCP Server (`CREATE MCP SERVER` SQL object), Cortex Analyst (native NL-to-SQL), Time Travel.

### Switch to Databricks

**1. Sign up** at [databricks.com/try](https://databricks.com/try) — 14-day full trial.

**2. Load data into Delta Lake** — in a Databricks notebook:
```python
# Upload CSVs to DBFS via UI first, then:
for table in ["orders", "order_items", "customers", "products", "sellers",
              "order_payments", "order_reviews"]:
    df = spark.read.option("header", True).option("inferSchema", True) \
        .csv(f"dbfs:/FileStore/olist/olist_{table}_dataset.csv")
    df.write.format("delta").mode("overwrite") \
        .saveAsTable(f"olist_analytics.public.{table}")

# Same for mock marketing CSVs
for file in ["google_ads_daily_performance", "meta_ads_daily_performance",
             "ga4_daily_sessions", "hubspot_contacts", "hubspot_deals",
             "salesforce_opportunities", "marketing_attribution"]:
    df = spark.read.option("header", True).option("inferSchema", True) \
        .csv(f"dbfs:/FileStore/mock_marketing/{file}.csv")
    df.write.format("delta").mode("overwrite") \
        .saveAsTable(f"olist_analytics.marketing.{file}")
```

**3. Add dbt profile** in `~/.dbt/profiles.yml`:
```yaml
    databricks:
      type: databricks
      host: "{{ env_var('DATABRICKS_HOST') }}"
      http_path: "/sql/1.0/warehouses/{{ env_var('DATABRICKS_SQL_WAREHOUSE_ID') }}"
      token: "{{ env_var('DATABRICKS_TOKEN') }}"
      catalog: olist_analytics
      schema: public
      threads: 4
```

**4. Build models:**
```bash
dbt build --target databricks
```

**5. Connect MCP server** — add to `claude_desktop_config.json`:
```json
{
  "databricks": {
    "command": "npx",
    "args": ["mcp-remote",
             "https://your-workspace.cloud.databricks.com/api/2.0/mcp/sql",
             "--header", "Authorization: Bearer YOUR_PAT_TOKEN"]
  }
}
```

**6. Run the same hero query** — identical results, Delta Lake engine.

**Databricks bonus features:** MLflow is built-in (zero setup — `import mlflow` just works), Unity Catalog governance, Delta Lake time travel, Genie Spaces (Databricks' own NL-to-SQL — compare with your MCP approach).

### Permanent free alternative: DuckDB

If you don't want to pay for any cloud warehouse, DuckDB gives you the full analytics experience locally:

| Capability | BigQuery Free | DuckDB Local |
|---|---|---|
| Storage | 10GB | Unlimited (your disk) |
| Queries | 1TB/month | Unlimited |
| Speed | Network latency | Instant (in-process) |
| dbt adapter | dbt-bigquery | dbt-duckdb |
| MCP server | Official Google | MotherDuck MCP |
| Looker Studio | Native connection | Use Streamlit/Evidence instead |
| Best for | Cloud demo + BI tools | Fast iteration + ML feature extraction |

Recommended approach: develop on DuckDB locally, demo on BigQuery (free), record Snowflake/Databricks during trial windows.

## Built With

**Data:** Olist Brazilian E-Commerce Dataset (Kaggle) + Synthetic Marketing Data

**Warehouse:** BigQuery · DuckDB · Supabase · Snowflake · Databricks

**Transformation:** dbt Core · MetricFlow · Polars

**AI Clients:** Claude Desktop · OpenCode · Gemini CLI · Antigravity IDE

**AI/MCP:** Model Context Protocol · Anthropic API · Cowork Plugin · OpenCode Commands

**ML:** XGBoost · Scikit-learn · MLflow · FastAPI

**Automation:** n8n

**Visualization:** Looker Studio · Streamlit · Plotly · Recharts

**Infrastructure:** Docker · uv · GitHub Actions

## License

MIT

---

*Built by [Eduardo](https://github.com/YOUR_USERNAME) as a portfolio project demonstrating modern data analytics architecture with AI integration.*
