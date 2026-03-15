Set up the Python development environment for this project. Do the following in order:

1. Create a Python 3.11 virtual environment at .venv in the project root
2. Activate it
3. Create a requirements.txt with these dependencies:

# Core data
pandas>=2.1.0
polars>=0.20.0
numpy>=1.24.0
duckdb>=0.9.0
google-cloud-bigquery>=3.13.0
supabase>=2.0.0

# dbt
dbt-core>=1.7.0
dbt-bigquery>=1.7.0
dbt-duckdb>=1.7.0
dbt-postgres>=1.7.0

# MCP servers
mcp>=1.0.0
httpx>=0.25.0

# ML
xgboost>=2.0.0
scikit-learn>=1.3.0
mlflow>=2.9.0

# API
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.5.0

# Visualization
streamlit>=1.30.0
plotly>=5.18.0

# Automation
python-dotenv>=1.0.0
requests>=2.31.0

4. Install all dependencies with pip install -r requirements.txt
5. Install uv globally (needed for MCP servers): curl -LsSf https://astral.sh/uv/install.sh | sh
6. Verify the environment works by running: python -c "import pandas, polars, duckdb, xgboost, mlflow, fastapi; print('All core packages imported successfully')"
7. Create a .env.example file with placeholder variables:
   GCP_PROJECT_ID=your-project-id
   BIGQUERY_LOCATION=US
   SUPABASE_URL=your-supabase-url
   SUPABASE_KEY=your-supabase-key
   DBT_CLOUD_TOKEN=your-dbt-cloud-token
   DBT_PROD_ENV_ID=your-env-id
   MLFLOW_TRACKING_URI=http://127.0.0.1:5000
8. Copy .env.example to .env

Confirm each step as you complete it. If any install fails, troubleshoot and fix it before moving to the next step.