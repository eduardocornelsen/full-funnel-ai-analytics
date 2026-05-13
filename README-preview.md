# Full-Funnel AI Marketing Analytics Platform

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![dbt](https://img.shields.io/badge/dbt-Core%20%2B%20MetricFlow-FF694B?style=flat-square&logo=dbt&logoColor=white)
![DuckDB](https://img.shields.io/badge/DuckDB-Golden%20Layer-FFF000?style=flat-square&logo=duckdb&logoColor=black)
![BigQuery](https://img.shields.io/badge/BigQuery-Free%20Tier-4285F4?style=flat-square&logo=googlebigquery&logoColor=white)
![Snowflake](https://img.shields.io/badge/Snowflake-Trial%20Demo-29B5E8?style=flat-square&logo=snowflake&logoColor=white)
![Databricks](https://img.shields.io/badge/Databricks-Trial%20Demo-FF3621?style=flat-square&logo=databricks&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-Postgres-3FCF8E?style=flat-square&logo=supabase&logoColor=white)
![Claude](https://img.shields.io/badge/Claude-Desktop%20%2B%20Cowork-D4A574?style=flat-square&logo=anthropic&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini-CLI-4285F4?style=flat-square&logo=google&logoColor=white)
![MLflow](https://img.shields.io/badge/MLflow-Experiment%20Tracking-0194E2?style=flat-square&logo=mlflow&logoColor=white)
![XGBoost](https://img.shields.io/badge/XGBoost-Lead%20Scoring-189FDD?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-Scoring%20API-009688?style=flat-square&logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)
![Looker Studio](https://img.shields.io/badge/Looker%20Studio-BI-4285F4?style=flat-square&logo=looker&logoColor=white)
![Zero Drift](https://img.shields.io/badge/metric%20drift-0%20detected-brightgreen?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)
![Cost](https://img.shields.io/badge/cost-%240%2Fmo%20base-brightgreen?style=flat-square)

**Natural language marketing analytics powered by MCP, dbt Semantic Layer, and ML lead scoring — with zero metric drift between the golden layer and every dashboard.**

> *"Which channels actually drive revenue, not just clicks?"*<br>
> This system answers that question in 15 seconds via natural language — backed by multi-touch attribution, a production ML scoring API, and dashboards fed from a **single governed golden layer** running across 5 data warehouses.

---

## Ask your data and get real-time answers

Ask Claude or other supported LLMs *any question about your data* and get **real-time insights and dashboards** — integrated with your data warehouses, CRMs, and Ads platforms.

> Predefined commands: type `/marketing` and see the magic happen:

![marketing-gif](demo/videos/marketing.gif)

**[▶ Watch the video →](demo/videos/marketing-query.mp4)**

> View the dashboards for all commands available: <br>
> [[/marketing]](dashboards/full_funnel_marketing_dashboard.html) | [[/attribution]](dashboards/attribution_dashboard.html) | [[/campaign]](dashboards/campaign_performance_dashboard.html) | [[/pipeline]](dashboards/pipeline_dashboard.html) | [[/traffic]](dashboards/traffic_ga4_dashboard.html)

---

## What's New — Golden Layer Architecture (v2)

> **Problem solved:** dashboards previously sourced from mock MCP CSV files with non-deterministic date windows, producing different numbers on every generation. This release eliminates metric drift entirely.

### Architecture: Before vs After

| | Before (v1) | After (v2) |
|--|-------------|------------|
| **Dashboard source** | Mock MCP CSV files (non-deterministic) | `golden_metrics.json` (pre-computed from dbt) |
| **Date window** | `today() - 90 days` (changes daily) | Fixed anchor `2026-03-15` (synthetic) / rolling `today()-90d` (live) |
| **Blended ROAS** | 71.1× (scope mismatch bug) | **20.69×** all-time · **24.12×** 90d |
| **Channel ROAS** | 0.00× (channel granularity bug) | Google **16.75×** · Meta **11.24×** |
| **Drift detection** | None | `validate_metrics.py` · 16/16 checks · exit 0 |
| **dbt parse errors** | `total_clicks` measure missing (blocked all runs) | Fixed — `metrics.yml` + `sem_marketing.yml` corrected |

---

## Data Flow (v2 — Golden Layer)

![Golden Layer Data Flow v2](docs/images/full_funnel_architecture_flow_v2.png)

> Previous architecture diagram: [v1 →](docs/images/full_funnel_architecture_flow.svg)

The new data flow adds **Lane 3** (anti-drift pipeline) between the dbt mart tables and the AI query layer:

```
Data Sources → dbt Staging Models → Golden Mart Tables
                                          │
                                  generate_golden_metrics.py
                                          │
                                  golden_metrics.json  ←── Single source of truth
                                          │
                    ┌─────────────────────┴──────────────────────┐
                    │                                            │
            Golden Layer Mode (default)              ⚡ Live MCP Mode (opt-in)
            /marketing, /campaign, etc.              /marketing-mcp, /campaign-mcp, etc.
                    │                                            │
                    └──────────────────┬─────────────────────────┘
                                       │
                              Dashboards / Artifacts
```

---

## Demo

### Hero Query

> *"Show me the complete marketing funnel for Q1 2025: ad spend across Google and Meta, website sessions by channel, lead conversion rates, and final revenue. Calculate blended CAC and ROAS."*

The AI reads `golden_metrics.json` (the dbt golden layer snapshot), and returns a formatted analysis with KPI cards, charts, and recommendations in ~15 seconds. Works from Claude Desktop, Gemini CLI, or Antigravity IDE.

![open-query.gif](demo/videos/open-query.gif)

**[▶ Watch the demo video →](demo/videos/open-query.mp4)**

### Other queries this system handles

- *"Compare first-touch vs last-touch attribution for our top channels"*
- *"Score this lead: came from Google Ads, visited 5 pages, 3 min on site"*
- *"Which product categories have the highest CAC but lowest LTV?"*
- *"What should we change about our ad spend next quarter?"*

---

## Canonical Metrics (Golden Layer — 90d Window: 2025-12-16 → 2026-03-15)

These values are locked in `dashboards/golden_metrics.json` and are **bit-for-bit identical** across every dashboard, report, and AI response.

| Metric | Value | Definition |
|--------|-------|------------|
| **Blended ROAS** | 24.12× | Linear attributed revenue / total ad spend |
| **Google Ads ROAS** | 19.05× | Linear attribution · 90d |
| **Meta Ads ROAS** | 13.35× | Linear attribution · 90d |
| **Session CVR** | 2.52% | GA4 conversions / GA4 sessions |
| **Total Sessions** | 431,698 | GA4 all channels |
| **Total Ad Spend** | $113,073 | Google $53,860 + Meta $59,212 |
| **GA4 Conversions** | 10,882 | Session-level, not click-level |
| **HubSpot Contacts** | 93,263 | All-time (CRM lifetime count) |
| **SF Closed Won** | $7,938,575 | All-time Salesforce |

> Run `python scripts/validate_metrics.py` to verify these against live DuckDB at any time.

---

## Who This Is Built For

| Role | What they see |
|------|--------------|
| **Paid Media / Growth Analytics** | Multi-touch attribution (4 models), ROAS by channel, spend optimization |
| **RevOps Analyst** | Full-funnel pipeline, CRM integration, lead routing automation |
| **Data Scientist** | XGBoost lead scoring, MLflow experiment tracking, FastAPI deployment |
| **Analytics Engineer** | dbt semantic layer, golden layer anti-drift, MCP architecture, multi-warehouse |
| **BI / Data Analyst** | Looker Studio dashboards, Streamlit app, Claude React artifacts |
| **Marketing Analyst** | CAC/LTV analysis, channel comparison, attribution model comparison |

---

## The Core Insight: Governance + Anti-Drift = Reliable AI Analytics

Most AI-to-SQL tools fail because they lack a **source of truth.** When an AI writes SQL on behalf of a marketing manager who can't verify it, you need two things:

1. **Metric governance** — define ROAS once in YAML (MetricFlow), consumed everywhere
2. **Anti-drift enforcement** — lock dashboards to a pre-computed golden snapshot so no two runs ever disagree

This project implements both:

- **dbt Semantic Layer (MetricFlow):** `ROAS = SUM(attributed_revenue) / SUM(ad_spend)` — defined once, consumed by every AI client, dashboard, and ML pipeline
- **Golden Layer Pipeline:** `generate_golden_metrics.py → golden_metrics.json → validate_metrics.py` — drift detected and rejected automatically

> *"Average confidence in AI-generated queries is just 5.5/10 without a semantic layer."*
> — [The 2025 Metabase Community Data Stack Report](https://www.metabase.com/data-stack-report-2025)
>
> **This project takes it to 10/10** — deterministic, production-grade, validated.

---

## Architecture: Three Heads, One Spine

> Full-stack analytics portfolio — data ingestion through AI-powered natural language querying, built entirely on free/trial tiers.

| Pillar | What it does | Tech |
|--------|-------------|------|
| **AI Layer** | Query marketing data in plain English, generate dashboards | 7 MCP servers + Claude Desktop, OpenCode, Gemini CLI, Antigravity |
| **ML Layer** | Predict which leads become high-value customers | XGBoost + MLflow + FastAPI `/score` + n8n auto-routing |
| **BI Layer** | Self-serve dashboards for marketing and sales teams | Looker Studio + Streamlit + Claude React artifacts |

---

## Build Status

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1: Data Foundation | ✅ Complete | Olist dataset + synthetic marketing data + warehouse loading |
| Phase 2: dbt Semantic Layer | ✅ Complete | 14 staging + 4 intermediate + 11 mart models |
| Phase 3: AI Layer (MCP) | ✅ Complete | 7 MCP servers + 4 AI client configs |
| Phase 4: ML Scoring | ✅ Complete | XGBoost + MLflow + FastAPI endpoint |
| Phase 5: Dashboards & Automation | ✅ Complete | Looker Studio + Streamlit + n8n routing |
| Phase 6: Portability & Polish | ✅ Complete | Snowflake/Databricks demos + documentation |
| **Phase 7: Golden Layer Anti-Drift** | ✅ **Complete** | **Zero metric drift · 16/16 validation checks** |

### Project Scale

| Component | Detail |
|-----------|--------|
| **Data Volume** | 23 CSV files, **2.2M+ rows**, aligned across 2024–2026 |
| **DuckDB Warehouse** | **46 objects** (staging views + mart tables), all populated |
| **dbt Models** | **29 models**, all materialized, end-to-end verified |
| **MCP Servers** | **7 servers**, column references cross-checked against source CSVs |
| **Streamlit App** | 5 tabs, all DuckDB queries valid, AI analyst integrated |
| **ML Pipeline** | XGBoost trained on **93K rows**, FastAPI `/score` endpoint live |
| **Semantic Layer** | **5 semantic models** + **13+ metrics** governed |
| **Golden Snapshot** | **23.5 KB** JSON · `all_time` + `windowed_90d` · schema v2.1 |
| **Validation** | **16/16 checks** · 0 drift · exit 0 |

---

## AI-Powered Commands

Each skill has two modes. The **golden mode** (default) reads `golden_metrics.json` for zero-drift guaranteed numbers. The **-mcp mode** (explicit opt-in) queries live platform servers for real-time raw data.

### Golden Layer Skills (default)

| Command | Data source | Primary metric |
|---------|-------------|----------------|
| `/marketing` | `windowed_90d` + `all_time` | Blended ROAS (linear · 90d) |
| `/campaign` | `windowed_90d.campaigns` | Platform ROAS per campaign |
| `/attribution` | `windowed_90d.attribution_by_channel` | Channel revenue share (linear · 90d) |
| `/traffic` | `windowed_90d.ga4_by_channel` | Session CVR by channel |
| `/pipeline` | `all_time.crm` | Win rate, pipeline value (CRM all-time) |

### Live MCP Skills (opt-in — add `-mcp` suffix or say "live data")

| Command | MCP servers queried | Badge shown |
|---------|--------------------|-|
| `/marketing-mcp` | google-ads, meta-ads, ga4, hubspot, salesforce | ⚡ Live MCP |
| `/campaign-mcp` | google-ads, meta-ads | ⚡ Live MCP |
| `/attribution-mcp` | ga4, google-ads, meta-ads | ⚡ Live MCP |
| `/traffic-mcp` | ga4 | ⚡ Live MCP |
| `/pipeline-mcp` | hubspot, salesforce | ⚡ Live MCP |

---

## Anti-Drift Pipeline

### How It Works

```bash
# 1. Rebuild dbt golden marts
cd dbt_project && dbt run --target duckdb

# 2. Generate the golden snapshot
python scripts/generate_golden_metrics.py
# → Writes dashboards/golden_metrics.json (all_time + windowed_90d)

# 3. Validate zero drift
python scripts/validate_metrics.py
# → Checks run: 16   ✅ Passed: 16   ❌ Drifted: 0
```

### Date Anchoring

| Dataset type | Rule |
|-------------|------|
| **Synthetic (this project)** | Fixed anchor `2026-03-15` · window `2025-12-16 → 2026-03-15` |
| **Live / real data (swap-in)** | Rolling `today() - 90 days → today()` |

This project is open source. Connect your real Google Ads, Meta, GA4, HubSpot, or Salesforce data by replacing mock servers with production MCP servers — the date logic adapts automatically.

---

## MCP Servers

| Server | What it exposes | Key tools |
|--------|----------------|-----------|
| **BigQuery** | Warehouse queries | `execute_query`, `list_tables`, `get_schema` |
| **dbt Semantic Layer** | Governed metrics + SQL generation | `text_to_sql`, `get_metrics`, `get_dimensions` (60+ tools) |
| **Google Ads** | Campaign performance, keywords | `get_campaign_performance`, `get_keyword_performance` |
| **Meta Ads** | Ad sets, reach, purchases | `get_campaign_insights`, `get_ad_set_breakdown` |
| **GA4** | Sessions, channels, conversions | `get_traffic_by_channel`, `get_daily_trend` |
| **HubSpot** | Contacts, deals, pipeline | `get_deal_pipeline_summary(start_date, end_date)` |
| **Salesforce** | Opportunities, accounts, revenue | `get_opportunity_pipeline(start_date, end_date)` |

> HubSpot and Salesforce servers now accept `start_date`/`end_date` parameters for date-filtered pipeline analysis.

---

## Metrics Governed by the Semantic Layer

| Metric | Definition | Category |
|--------|-----------|----------|
| Blended ROAS | Attributed revenue / Total ad spend (linear · 90d) | Marketing |
| Channel ROAS | Revenue (per attribution model) / Channel spend | Attribution |
| Session CVR | GA4 conversions / GA4 sessions (canonical) | Website |
| Click CVR | Platform conversions / Ad clicks (campaign tables only) | Platform |
| Blended CAC | Total ad spend / New customers | Marketing |
| First-Touch Revenue | Revenue credited to first interaction | Attribution |
| Last-Touch Revenue | Revenue credited to last interaction | Attribution |
| Linear Revenue | Revenue split equally across touchpoints | Attribution |
| AOV | Total revenue / Total orders ($100 assumption for Google) | Revenue |
| Customer LTV | Predicted lifetime revenue per customer | Revenue |
| Lead Score | ML-predicted probability of high-value conversion | Scoring |
| Pipeline Velocity | Weighted pipeline value / Days in period | Pipeline |
| Win Rate | Closed Won / (Closed Won + Closed Lost) | Pipeline |

---

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
| AI: Claude Desktop | Cowork + React artifacts | $20/month (optional) |
| AI: OpenCode | Terminal + 75 models | $0 (free + API costs) |
| AI: Gemini CLI | BigQuery native | $0 (free generous limits) |
| AI: Antigravity IDE | Parallel agents | $0 (free public preview) |

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/eduardocornelsen/full-funnel-ai-analytics.git
cd full-funnel-ai-analytics

# 2. Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Fill in your credentials

# 3. Download and generate data
python scripts/download_olist_data.py
python scripts/generate_mock_marketing_data.py

# 4. Load into DuckDB
python scripts/load_duckdb.py

# 5. Build dbt models
cd dbt_project && dbt build --target duckdb && cd ..

# 6. Generate golden metrics snapshot
python scripts/generate_golden_metrics.py

# 7. Validate zero drift
python scripts/validate_metrics.py
# → 16/16 checks passed ✅

# 8. Configure MCP for your preferred AI client
# Claude Desktop: copy mcp_servers/claude_desktop_config.example.json
# OpenCode:       already configured at .opencode/opencode.json
# Gemini CLI:     gemini --mcp-server "..."

# 9. Query in natural language:
# "/marketing" → reads golden_metrics.json → zero-drift dashboard
# "/marketing-mcp" → queries live MCP servers → ⚡ Live MCP badge
```

---

## Project Structure

```
full-funnel-ai-analytics/
├── dbt_project/                    # Semantic layer + transformations
│   ├── models/
│   │   ├── staging/                #   14 staging models (Olist + marketing)
│   │   ├── intermediate/           #   4 intermediate (LTV, funnel, unified campaigns)
│   │   ├── marts/                  #   11 mart models (facts + dimensions)  ← golden layer
│   │   ├── semantic_models/        #   MetricFlow definitions
│   │   └── metrics/                #   15+ governed metrics
│   └── macros/                     #   Attribution model logic + cross-db helpers
│
├── scripts/
│   ├── generate_golden_metrics.py  # ← NEW: DuckDB → golden_metrics.json
│   ├── validate_metrics.py         # ← NEW: drift detector (16/16 checks)
│   ├── download_olist_data.py
│   ├── generate_mock_marketing_data.py
│   └── load_duckdb.py
│
├── dashboards/
│   ├── golden_metrics.json         # ← NEW: single source of truth (23.5 KB)
│   ├── js/metrics.js               #   Canonical metric functions (CVR, ROAS, attribution)
│   └── *.html                      #   Generated dashboards (read from golden_metrics.json)
│
├── mcp_servers/                    # 7 MCP servers (work with all 4 AI clients)
│   ├── mock_google_ads_server.py
│   ├── mock_meta_ads_server.py
│   ├── mock_ga4_server.py
│   ├── mock_hubspot_server.py      # ← Updated: start_date/end_date params
│   ├── mock_salesforce_server.py   # ← Updated: start_date/end_date params
│   └── weather_server.py
│
├── docs/
│   └── images/
│       ├── full_funnel_architecture_flow.svg     # v1 — original architecture
│       ├── full_funnel_architecture_flow_v2.png  # ← NEW: golden layer data flow
│       └── marketing-dashboard.png
│
├── CLAUDE.md                       # ← Updated: §9 date rules, §11 skill table, §14 decision tree
├── ml/                             # Lead scoring ML pipeline
├── api/                            # FastAPI lead scoring endpoint
└── streamlit_app/                  # Interactive AI dashboard
```

---

## Key Design Decisions

### Why a golden metrics JSON instead of querying dbt on the fly?

Determinism. When an AI generates a dashboard, it may interpret query results differently each run (rounding, aggregation order, scope selection). Pre-computing the snapshot from DuckDB once and locking it as JSON guarantees every dashboard — regardless of which AI client, which conversation, or which day — shows the same numbers.

### Why mock MCP servers?

The mock servers expose the **exact same tool interface** as real platform APIs. When you swap mock → production, all client configurations, commands, and dashboards work without code changes. Now with `start_date`/`end_date` support, they also correctly scope data to the canonical 90-day window.

### Why MetricFlow?

When AI writes SQL on behalf of someone who can't verify it, you need guaranteed correctness. MetricFlow ensures "ROAS" always means the same thing — defined once in YAML, consumed everywhere: AI queries, BI dashboards, ML features.

### Why both golden and MCP modes?

- **Golden mode** (default): zero drift, reproducible, fast. Use for dashboards and reports.
- **MCP mode** (opt-in): real-time raw platform data. Use when you need live numbers or want to verify against the golden layer. Always labelled with ⚡ Live MCP badge.

---

## Swapping to Real Platform Data

| Mock Server | Production Replacement | Setup |
|-------------|----------------------|-------|
| `mock_google_ads_server.py` | `cohnen/mcp-google-ads` | Google Ads API developer token + OAuth |
| `mock_meta_ads_server.py` | `meta-ads-mcp-server` (npx) | Meta access token with ads_read |
| `mock_ga4_server.py` | GrowthSpree GA4 MCP | Google OAuth |
| `mock_hubspot_server.py` | Official HubSpot MCP | HubSpot access token |
| `mock_salesforce_server.py` | Airbyte agent connector | Salesforce Connected App |

When using real data, update `ANCHOR_DATE = date.today()` in `generate_golden_metrics.py` to switch from fixed synthetic dates to the rolling 90-day window.

---

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture Flow v2](docs/images/full_funnel_architecture_flow_v2.png) | Golden layer data flow with anti-drift pipeline |
| [Architecture Flow v1](docs/images/full_funnel_architecture_flow.svg) | Original system design |
| [CLAUDE.md](CLAUDE.md) | Mandatory agent instructions — metric definitions, date rules, data sourcing |
| [Setup & Execution Guide](docs/guides/setup_guide.md) | Step-by-step instructions |
| [Analytical Commands Guide](docs/guides/commands_guide.md) | Reference for all slash commands |
| [Multi-Warehouse Portability Guide](docs/guides/portability_guide.md) | Snowflake, Databricks, Supabase setup |
| [Claude Desktop Project Instructions](docs/guides/claude_desktop_project_instructions.md) | Claude Desktop Projects configuration |

---

## Contributing

Contributions are welcome! This project is part of a portfolio demonstrating end-to-end Revenue Operations engineering capabilities.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request — please squash before merging

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">
  <sub>Built with ☕ by <strong><a href="https://www.linkedin.com/in/eduardo-cornelsen/">Eduardo Cornelsen</a></strong> — © 2026 All Rights Reserved</sub><br/>
  <sub>Portfolio project demonstrating production-grade data analytics architecture with AI integration.</sub><br/>
  <sub>Revenue Operations · Data Engineering · AI/ML · Full-Stack Development</sub>
</p>
