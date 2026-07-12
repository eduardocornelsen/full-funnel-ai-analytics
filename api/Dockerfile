FROM python:3.11-slim

WORKDIR /app

# Install only what the scoring API needs (core + [ml] extra), not the full
# multi-warehouse requirements set.
COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src/
RUN pip install --no-cache-dir -e ".[ml]"

COPY api/ ./api/
COPY ml/lead_scoring_model.json ./ml/

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
