# 📚 Documentation Index

Your complete map of every file in the `docs/` folder. Start here whenever you can't remember where something lives.

---

## Table of Contents

1. [How to use this index](#how-to-use-this-index)
2. [Quick-find: I want to…](#quick-find-i-want-to)
3. [Folder structure at a glance](#folder-structure-at-a-glance)
4. [`docs/` root files](#docs-root-files)
   - [architecture.md](#architecturemd)
   - [mcp_servers.md](#mcp_serversmd)
   - [ml_model.md](#ml_modelmd)
5. [`docs/guides/` — step-by-step how-to docs](#docsguides--step-by-step-how-to-docs)
6. [`docs/images/` — diagrams and screenshots](#docsimages--diagrams-and-screenshots)
7. [`docs/slides/` — presentations](#docsslides--presentations)
8. [Reading paths by role](#reading-paths-by-role)
9. [Where things live OUTSIDE `docs/`](#where-things-live-outside-docs)

---

## How to use this index

Every file is listed below with:

- **One-line purpose** — what the document answers
- **Audience** — who should read it
- **When to read it** — the moment you'd reach for this file
- **Size** — line count, so you know if it's a 5-minute skim or a deep read

If you only have time for one section, skip to [Quick-find](#quick-find-i-want-to).

---

## Quick-find: I want to…

| Goal | Read this |
|------|-----------|
| Run the project for the first time | [`guides/setup_guide.md`](guides/setup_guide.md) |
| See the platform roadmap and strategic direction | [`STRATEGY.md`](STRATEGY.md) |
| Prepare interview talk tracks from this project | [`INTERVIEW_STORIES.md`](INTERVIEW_STORIES.md) |
| Understand the dbt model layers and MetricFlow | [`architecture.md`](architecture.md) |
| Understand how mock MCP servers work | [`mcp_servers.md`](mcp_servers.md) |
| Understand the ML model, MLflow, and n8n integration | [`ml_model.md`](ml_model.md) |
| Use a slash command in Claude (`/marketing`, `/attribution`, etc.) | [`guides/commands_guide.md`](guides/commands_guide.md) |
| Set up Claude Desktop with this project | [`guides/claude_desktop_project_instructions.md`](guides/claude_desktop_project_instructions.md) |
| Import my own CSV / Excel data | [`guides/data_import_guide.md`](guides/data_import_guide.md) |
| Use the Streamlit Data Sources UI | [`guides/connector_ui_guide.md`](guides/connector_ui_guide.md) |
| Configure CI/CD secrets for BigQuery / Snowflake | [`guides/production_readiness_guide.md`](guides/production_readiness_guide.md) |
| Promote v0.9 → v1.0 (the release checklist) | [`guides/production_readiness_guide.md`](guides/production_readiness_guide.md#promoting-v09--v10--pre-release-checklist) |
| Move from DuckDB to Snowflake / Databricks | [`guides/portability_guide.md`](guides/portability_guide.md) |
| Understand the BigQuery data warehouse design | [`guides/data-warehouse-plan.md`](guides/data-warehouse-plan.md) |
| See the architecture diagram | [`images/full_funnel_architecture_flow_v2.png`](images/full_funnel_architecture_flow_v2.png) |
| Show this project in a presentation | [`slides/Governed_AI_Marketing_Analytics_compressed.pdf`](slides/Governed_AI_Marketing_Analytics_compressed.pdf) |

---

## Folder structure at a glance

```
docs/
├── README.md                                # ← you are here
├── architecture.md                          # full dbt + MetricFlow internals (1,200 lines)
├── mcp_servers.md                           # how mock MCP servers work + swap guide
├── ml_model.md                              # XGBoost, MLflow, FastAPI, n8n integration
│
├── guides/                                  # task-oriented how-to docs
│   ├── setup_guide.md                       # first-time setup (104 lines)
│   ├── commands_guide.md                    # slash command reference (60 lines)
│   ├── claude_desktop_project_instructions.md  # Claude Desktop config (117 lines)
│   ├── data_import_guide.md                 # bring your own data (331 lines)
│   ├── connector_ui_guide.md                # Streamlit Data Sources UI (231 lines)
│   ├── production_readiness_guide.md        # CI/CD, secrets, v0.9 → v1.0 checklist (330 lines)
│   ├── portability_guide.md                 # multi-warehouse deploy (20 lines)
│   └── data-warehouse-plan.md               # BigQuery design decisions (320 lines)
│
├── images/                                  # diagrams and screenshots
│   ├── full_funnel_architecture_flow_v2.png # latest architecture diagram
│   ├── full_funnel_architecture_flow.png    # original PNG version
│   ├── full_funnel_architecture_flow.svg    # original vector version
│   └── marketing-dashboard.png              # sample dashboard screenshot
│
└── slides/                                  # presentations
    └── Governed_AI_Marketing_Analytics_compressed.pdf  # talk deck
```

---

## `docs/` root files

### [`architecture.md`](architecture.md)

> **The single deepest reference document in the project — 1,205 lines.**

| | |
|---|---|
| **Purpose** | Complete tour of the dbt medallion architecture, every staging / intermediate / mart model, every MetricFlow semantic model and metric, the dbt CLI command reference, and the AI agent's data flow with drift-prevention logic. |
| **Audience** | Analytics engineers, dbt practitioners, anyone debugging the data layer. |
| **When to read** | When you need to know exactly how a metric is computed, what columns a fact table has, or how MetricFlow time spines work. |
| **Sections** | 1. Medallion overview 2. Staging layer (14 models) 3. Intermediate layer (4 models) 4. Marts layer (11 models) 5. MetricFlow semantic models 6. Metric definitions 7. Architecture summary table 8. dbt CLI reference 9. AI agent — querying, drift prevention & validation |

### [`mcp_servers.md`](mcp_servers.md)

| | |
|---|---|
| **Purpose** | Explains the five mock MCP servers: how they're built with FastMCP, what each tool returns, how date filtering works, how to configure `.mcp.json`, and how to swap any mock for a real production API. |
| **Audience** | Anyone adding a new AI client, debugging MCP tool calls, or replacing mock data with live platform APIs. |
| **When to read** | When you need to understand what data an MCP tool returns, why a tool call returns unexpected results, or how to connect to a real Ads/CRM platform. |
| **Sections** | 1. What is MCP? 2. Why mock servers? 3. How a server is built 4. All five servers with tool schemas 5. Date filtering rules 6. `.mcp.json` config 7. Local testing 8. Swap mock → production |

### [`ml_model.md`](ml_model.md)

| | |
|---|---|
| **Purpose** | Documents the XGBoost lead scoring pipeline end-to-end: input features, training script, MLflow experiment tracking, FastAPI endpoint, and n8n lead routing automation. |
| **Audience** | Data scientists, ML engineers, and anyone integrating the scoring API into an automation workflow. |
| **When to read** | When training a new model version, debugging the `/score` endpoint, setting up the n8n workflow, or viewing MLflow experiment results. |
| **Sections** | 1. What the model does 2. Input features 3. Training pipeline 4. MLflow tracking 5. Saved artefacts 6. FastAPI endpoint 7. n8n automation + current status 8. How to retrain 9. Viewing results 10. Roadmap |

---

## `docs/guides/` — step-by-step how-to docs

Each guide solves a specific task. They are not meant to be read top-to-bottom; jump in when you have the problem they solve.

### [`setup_guide.md`](guides/setup_guide.md) — 104 lines

| | |
|---|---|
| **Purpose** | Run the project locally from a fresh clone in ~10 minutes. |
| **Audience** | Anyone running the project for the first time. |
| **When to read** | First thing after `git clone`. |
| **Covers** | venv + dependencies, downloading Olist, generating mock data, loading DuckDB, running dbt, training the ML model, starting the scoring API. |

### [`commands_guide.md`](guides/commands_guide.md) — 60 lines

| | |
|---|---|
| **Purpose** | Reference for every slash command (`/marketing`, `/attribution`, `/campaign`, `/pipeline`, `/traffic` and their `-mcp` variants). |
| **Audience** | Anyone using Claude Code, OpenCode, or any MCP client. |
| **When to read** | When you forget what a command does or want to know the difference between `/marketing` and `/marketing-mcp`. |
| **Covers** | Each command's data source (golden layer vs. live MCP), expected output, and when to use each one. |

### [`claude_desktop_project_instructions.md`](guides/claude_desktop_project_instructions.md) — 117 lines

| | |
|---|---|
| **Purpose** | Configure Claude Desktop "Projects" to use this codebase. |
| **Audience** | Claude Desktop users (the GUI app, not Claude Code CLI). |
| **When to read** | When setting up a Claude Desktop Project. |
| **Covers** | Project Instructions text to paste, natural-language equivalents for slash commands, MCP server config for Claude Desktop. |

### [`data_import_guide.md`](guides/data_import_guide.md) — 331 lines ⭐ **must-read**

| | |
|---|---|
| **Purpose** | Bring your own data (Excel, CSV, or live warehouse) into the platform. |
| **Audience** | Anyone replacing the mock data with real platform data. |
| **When to read** | First time you import a real dataset. |
| **Covers** | What lives in git vs. locally, three import methods (Streamlit UI / direct CSV / live warehouse), how to update local DuckDB, demo-vs-production pipeline comparison, column mapping reference for each platform, troubleshooting. |

### [`connector_ui_guide.md`](guides/connector_ui_guide.md) — 231 lines

| | |
|---|---|
| **Purpose** | Use the Streamlit Data Sources page (three-tab UI). |
| **Audience** | Anyone using `streamlit run streamlit_app/app.py`. |
| **When to read** | When you want to import data, configure a warehouse connection, or check MCP server status without using the terminal. |
| **Covers** | File Upload tab, Warehouse Connection tab (DuckDB / BigQuery / Snowflake), MCP Server Status tab, live-dashboard capability matrix (Claude vs. Streamlit vs. HTML vs. Perplexity), daily synthetic data workflow. |

### [`production_readiness_guide.md`](guides/production_readiness_guide.md) — 330 lines ⭐ **must-read**

| | |
|---|---|
| **Purpose** | Everything needed to deploy this project to production warehouses and certify it for v1.0. |
| **Audience** | Project maintainers, anyone configuring CI/CD. |
| **When to read** | Before configuring GitHub Secrets, deploying to BigQuery / Snowflake, or promoting v0.9 → v1.0. |
| **Covers** | **Pre-v1.0 release checklist** (8 categories), what each GitHub Actions workflow does, required GitHub Secrets, how to create a BigQuery service account, how to verify dashboard == warehouse, the daily synthetic data appender, running the test suite, switching between DuckDB / BigQuery / Snowflake locally. |

### [`portability_guide.md`](guides/portability_guide.md) — 20 lines

| | |
|---|---|
| **Purpose** | Quick reference for moving from DuckDB to other warehouses. |
| **Audience** | Engineers swapping the warehouse target. |
| **When to read** | When deciding which warehouse to use, or migrating between them. |
| **Covers** | What stays the same vs. what changes when you switch warehouses. (Short — most of the heavy lifting is in `production_readiness_guide.md`.) |

### [`data-warehouse-plan.md`](guides/data-warehouse-plan.md) — 320 lines

| | |
|---|---|
| **Purpose** | The BigQuery implementation plan and data-warehouse architecture decisions. |
| **Audience** | Data architects, anyone evaluating the cost / scalability model. |
| **When to read** | When asked "why BigQuery as the primary warehouse?" or "how do you keep this at $0/month?" |
| **Covers** | BigQuery free tier reasoning, dataset structure, partitioning + clustering decisions, cost projections, alternative warehouse trade-offs. |

---

## `docs/images/` — diagrams and screenshots

| File | What it shows | Where it's used |
|------|--------------|-----------------|
| [`full_funnel_architecture_flow_v2.png`](images/full_funnel_architecture_flow_v2.png) | **Latest** architecture diagram showing data → dbt → golden layer → AI/BI consumers | Top of the main `README.md` |
| [`full_funnel_architecture_flow.png`](images/full_funnel_architecture_flow.png) | Original v1 architecture diagram (PNG) | Folded inside a `<details>` block in `README.md` for reference |
| [`full_funnel_architecture_flow.svg`](images/full_funnel_architecture_flow.svg) | Original v1 architecture diagram (vector format) | Available for editing in any vector tool |
| [`marketing-dashboard.png`](images/marketing-dashboard.png) | Sample marketing dashboard screenshot | Demo / preview imagery |

---

## `docs/slides/` — presentations

| File | What it is |
|------|-----------|
| [`Governed_AI_Marketing_Analytics_compressed.pdf`](slides/Governed_AI_Marketing_Analytics_compressed.pdf) | The talk deck explaining this project's thesis — why governance is what makes AI analytics reliable, how the dbt Semantic Layer + MCP architecture moves AI confidence from 5.5/10 to deterministic. Use this when presenting the project. |

---

## Reading paths by role

### "I just cloned this repo — get me started"
1. Main [`/README.md`](../README.md) — project overview
2. [`guides/setup_guide.md`](guides/setup_guide.md) — install + run
3. [`guides/commands_guide.md`](guides/commands_guide.md) — try `/marketing`

### "I'm a data engineer / analyst evaluating this for production"
1. [`architecture.md`](architecture.md) — model and metric internals
2. [`guides/production_readiness_guide.md`](guides/production_readiness_guide.md) — CI/CD + warehouses
3. [`guides/portability_guide.md`](guides/portability_guide.md) — multi-warehouse story

### "I want to put my own company's data into this"
1. [`guides/data_import_guide.md`](guides/data_import_guide.md) — start here
2. [`guides/connector_ui_guide.md`](guides/connector_ui_guide.md) — Streamlit UI
3. [`architecture.md`](architecture.md) §2 staging — column requirements

### "I want to understand or extend the MCP servers"
1. [`mcp_servers.md`](mcp_servers.md) — full server reference + swap guide
2. [`guides/data_import_guide.md`](guides/data_import_guide.md) — replacing mock data with real platform data

### "I want to work on the ML model or n8n automation"
1. [`ml_model.md`](ml_model.md) — model, MLflow, FastAPI, n8n status
2. [`guides/setup_guide.md`](guides/setup_guide.md) §5–7 — MLflow server + training commands

### "I'm shipping v1.0 — what do I need to check?"
1. [`guides/production_readiness_guide.md`](guides/production_readiness_guide.md) — the 8-category checklist
2. Main [`/CLAUDE.md`](../CLAUDE.md) §14 — golden layer rules

### "I'm showing this to someone in a presentation"
1. [`slides/Governed_AI_Marketing_Analytics_compressed.pdf`](slides/Governed_AI_Marketing_Analytics_compressed.pdf) — talk deck
2. [`images/full_funnel_architecture_flow_v2.png`](images/full_funnel_architecture_flow_v2.png) — diagram

---

## Where things live OUTSIDE `docs/`

For completeness, the documentation surface of the project extends to a few files outside the `docs/` folder:

| Location | What it is |
|----------|-----------|
| [`/README.md`](../README.md) | Project front door — badges, hero query, architecture, quick start, links to everything else |
| [`/CLAUDE.md`](../CLAUDE.md) | **Mandatory AI agent rules** — metric definitions, attribution windows, golden-layer-first sourcing (§14). Read by Claude on every conversation. |
| [`/SETUP_GUIDE.md`](../SETUP_GUIDE.md) | Original setup guide kept at project root for visibility |
| [`/dbt_project/README.md`](../dbt_project/README.md) | dbt-specific README mirroring `docs/architecture.md` |
| `/cowork_plugin/skills/*` | Claude Desktop Cowork skill files (brand voice, workflows) |
| `/.claude/commands/*` | Claude Code slash command definitions |
| `/.opencode/commands/*` | OpenCode slash command definitions (same logic, different format) |

> **Tip:** If you can't find something here, run `grep -r "<keyword>" docs/ README.md CLAUDE.md` — almost every concept in the project has at least two places it's documented.
