# 📖 Full-Funnel AI Analytics: Setup & Execution Guide

Follow these steps to get your complete AI marketing platform running on your local machine.

## 📋 Prerequisites
- Python 3.11+
- Git
- [uv](https://github.com/astral-sh/uv) (recommended) or `pip`
- A Google Cloud Platform (GCP) project (optional, for BigQuery)

---

## 🛠️ Step 1: Environment Setup

```bash
# 1. Clone the repository (if not already in it)
# cd full-funnel-ai-analytics

# 2. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

## 📊 Step 2: Data & Warehouse Initialization

```bash
# 1. Download the real Olist dataset (requires Kaggle API key)
python scripts/download_olist_data.py

# 2. Generate the synthetic marketing, CRM, and attribution data
python scripts/generate_mock_marketing_data.py

# 3. Load everything into your local DuckDB database
python scripts/load_duckdb.py

# 4. (Optional) Load into BigQuery (if GCP_PROJECT_ID is set in .env)
# python scripts/load_bigquery.py
```

## 🧪 Step 3: dbt Build & Semantic Layer

```bash
# 1. Move into dbt directory
cd dbt_project

# 2. Install dbt packages
dbt deps

# 3. Build all models (24+ staging, intermediate, and marts)
dbt build --target duckdb

cd ..
```

## 🧠 Step 4: ML Lead Scoring & API

```bash
# 1. Generate specialized features for the ML model
python scripts/generate_lead_scoring_features.py

# 2. Train the XGBoost model (logged via MLflow)
python ml/src/train.py

# 3. Start the Scoring API (Leave this running in a separate terminal)
uvicorn api.main:app --port 8000
```

## 🤖 Step 5: MCP & AI Client Connectivity

### A. Claude Desktop (Visual Artifacts)
1. Open your Claude Desktop config:
   - **Linux:** `~/.config/Claude/claude_desktop_config.json`
   - **Mac:** `~/Library/Application\ Support/Claude/claude_desktop_config.json`
   - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
2. Copy the contents of `mcp_servers/claude_desktop_config.example.json` into that file.
3. **Restart Claude Desktop.**

### B. Claude Code (Terminal CLI)
If using Claude Code, you can use the same server configurations. Claude Code automatically reads `.opencode/opencode.json` (which I created for you) if you are using that specific tool, or you can point it to your MCPs.

## 🚀 Step 6: Execution & Interaction

### Launch the Dashboard
```bash
streamlit run streamlit_app/app.py
```

### Interact with the AI
Open Claude (Desktop or CLI) and ask:
- *"Show me the blended CAC for last month using the /marketing command."*
- *"Compare First-Touch vs Last-Touch revenue for my top 5 channels."*
- *"Score this lead: 10 sessions, 8 engaged, from Paid Search."*

---

## 📂 Key File Locations
- **Mock Servers:** `mcp_servers/` (5 platform mocks + 1 weather)
- **ML Training:** `ml/src/train.py`
- **Scoring API:** `api/main.py`
- **Dashboard:** `streamlit_app/app.py`
- **dbt Project:** `dbt_project/`
