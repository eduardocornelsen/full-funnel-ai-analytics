# Streamlit app + full pipeline image.
# `fullfunnel demo` at startup is idempotent: it builds DuckDB from the
# committed CSVs, runs dbt, regenerates golden metrics, and validates —
# so the container always serves fresh, gate-checked numbers.
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src/
RUN pip install --no-cache-dir -e ".[app]"

COPY . .

EXPOSE 8501

CMD ["bash", "-c", "fullfunnel demo && streamlit run streamlit_app/app.py --server.port 8501 --server.address 0.0.0.0"]
