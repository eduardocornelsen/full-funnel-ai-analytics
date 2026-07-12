# ML Lead Scoring Model & MLflow

This document explains the XGBoost lead scoring pipeline: what it predicts, how it's trained, how MLflow tracks experiments, how the FastAPI endpoint serves predictions, and the current state of the n8n automation integration.

---

## Table of Contents

1. [What the model does](#1-what-the-model-does)
2. [Input features](#2-input-features)
3. [Training pipeline](#3-training-pipeline)
4. [MLflow experiment tracking](#4-mlflow-experiment-tracking)
5. [Saved model artifacts](#5-saved-model-artifacts)
6. [FastAPI scoring endpoint](#6-fastapi-scoring-endpoint)
7. [n8n lead routing automation](#7-n8n-lead-routing-automation)
8. [How to retrain](#8-how-to-retrain)
9. [How to view experiment results](#9-how-to-view-experiment-results)
10. [Current status and roadmap](#10-current-status-and-roadmap)

---

## 1. What the model does

The lead scoring model predicts the **probability that a website visitor will convert into a closed-won deal** (`is_won`).

This probability — the "lead score" — is used in two ways:

1. **Dashboards:** The Streamlit app and HTML dashboards surface the score as a KPI alongside channel attribution and pipeline metrics
2. **Automation:** The n8n workflow calls the FastAPI endpoint and routes high-score leads (score > 0.8) to the sales team via Slack in real time

The model is intentionally lightweight — four behavioural features, one training script, one JSON file. The goal is a working ML-in-the-loop pipeline, not a production model requiring feature stores.

---

## 2. Input features

Features are derived from `fct_lead_scoring_features` (a dbt mart table) and exported to `data/lead_scoring_features.csv`.

| Feature | Type | Description |
|---------|------|-------------|
| `sessions` | int | Total GA4 sessions for this visitor |
| `engaged_sessions` | int | Sessions where engagement time > 10 seconds |
| `page_views` | int | Total pages viewed across all sessions |
| `is_first_visit` | bool (0/1) | Whether this is the visitor's first recorded session |

**Target variable:** `is_won` — binary (1 = contact became a closed-won deal, 0 = otherwise)

**Training data:** 93,000 rows sourced from the Olist e-commerce dataset joined with synthetic marketing engagement data.

The feature set is defined in `dbt_project/models/metrics/metrics.yml` under the `leads` semantic model. If you add new features to the dbt model, update the feature list in both `ml/src/train.py` and `api/main.py`.

---

## 3. Training pipeline

**Script:** `ml/src/train.py`

```
data/lead_scoring_features.csv
        │
        ▼
train_test_split (80 / 20, random_state=42)
        │
        ▼
XGBClassifier fit
        │
        ├──► MLflow run (logs params + metrics + model artifact)
        │
        └──► ml/lead_scoring_model.json  (local copy for the API)
```

**XGBoost hyperparameters:**

| Parameter | Value |
|-----------|-------|
| `max_depth` | 5 |
| `learning_rate` | 0.1 |
| `n_estimators` | 100 |
| `objective` | `binary:logistic` |
| `eval_metric` | `auc` |
| `random_state` | 42 |

**Evaluation metrics logged per run:**

| Metric | Description |
|--------|-------------|
| `accuracy` | Fraction of correct predictions |
| `precision` | True positives / (true positives + false positives) |
| `recall` | True positives / (true positives + false negatives) |
| `f1` | Harmonic mean of precision and recall |
| `auc` | Area under the ROC curve — primary model selection metric |

---

## 4. MLflow experiment tracking

**Tracking URI:** `file://ml/mlflow/` (local file-based, no server required)

**Experiment name:** `Lead Scoring Optimization`

Every call to `python ml/src/train.py` creates a new MLflow run under this experiment. MLflow records:

- **Parameters:** all XGBoost hyperparameters
- **Metrics:** accuracy, precision, recall, F1, AUC on the test set
- **Artefact:** the trained XGBoost model (logged via `mlflow.xgboost.log_model`)
- **Metadata:** run name, source type, git commit hash

The tracking directory structure:

```
ml/mlflow/
└── <experiment_id>/
    └── <run_id>/
        ├── params/           # hyperparameters
        ├── metrics/          # evaluation scores
        ├── artifacts/
        │   └── lead_scoring_xgb_model/
        │       ├── MLmodel   # model metadata
        │       └── model.xgb # serialised model
        └── tags/
```

---

## 5. Saved model artifacts

After training, two artefacts are produced:

| File | Format | Used by |
|------|--------|---------|
| `ml/lead_scoring_model.json` | XGBoost native JSON | FastAPI scoring endpoint |
| `ml/mlflow/<run_id>/artifacts/` | MLflow artefact store | MLflow UI, model registry |

The JSON file is loaded by `api/main.py` at startup. It does **not** need MLflow at inference time — the API depends only on `xgboost` and `fastapi`.

---

## 6. FastAPI scoring endpoint

**Location:** `api/main.py`

**Start the server:**

```bash
cd api && uvicorn main:app --port 8000 --reload
```

**Endpoint:** `POST /score`

**Request body:**

```json
{
  "sessions": 5,
  "engaged_sessions": 3,
  "page_views": 12,
  "channel": "Paid Search",
  "is_first_visit": false
}
```

**Response:**

```json
{
  "score": 0.84,
  "label": "high",
  "model_version": "1.0"
}
```

| Field | Description |
|-------|-------------|
| `score` | Float 0–1, probability of `is_won = 1` |
| `label` | `"high"` if score > 0.8, otherwise `"low"` |
| `model_version` | Version string from the model JSON |

The `channel` field in the request is accepted but not currently used as a model feature — it is reserved for a future model version that will include channel as a categorical feature.

**Interactive docs:** once running, visit `http://localhost:8000/docs` for the auto-generated Swagger UI.

---

## 7. n8n lead routing automation

**Workflow file:** `automation/n8n_workflow.json`

The n8n workflow automates the step between scoring and sales action:

```
Incoming webhook (new lead event)
        │
        ▼
POST http://api:8000/score
  { sessions, engaged_sessions, page_views, channel, is_first_visit }
        │
        ▼
score > 0.8?
    ├── YES → Slack #sales-notifications
    │         "🚀 High Value Lead Found! Email: ... Score: ..."
    └── NO  → (no action — lead stays in normal nurture sequence)
```

**Nodes:**

| Node | Type | Role |
|------|------|------|
| `Contact Hook` | Webhook trigger | Receives the lead event payload |
| `ML Score API` | HTTP Request | POSTs to the FastAPI `/score` endpoint |
| `High Score?` | IF condition | Routes on `score > 0.8` |
| `Slack Alert` | Slack | Posts to `#sales-notifications` with lead email and score |

### Current integration status

| Component | Status | Notes |
|-----------|--------|-------|
| Workflow definition | ✅ Complete | `automation/n8n_workflow.json` is fully specified |
| FastAPI endpoint | ✅ Running | `POST /score` is live when `uvicorn` is started |
| n8n runtime | ⚠️ Manual setup | n8n must be running separately; not started by `scripts/run_mlflow_server.sh` |
| Slack credentials | ⚠️ Not configured | The Slack node requires a Slack API token and channel ID configured in n8n |
| Production URL | ⚠️ Hardcoded | The workflow uses `http://api:8000/score` (Docker service name). Change to your actual API URL |

### Setting up n8n locally

```bash
# Install and start n8n
npx n8n

# Open the UI at http://localhost:5678
# Import the workflow:
#   Menu → Workflows → Import from file → automation/n8n_workflow.json
```

To connect to the scoring API, update the `ML Score API` node URL from `http://api:8000/score` to `http://localhost:8000/score` for local development.

### Configuring Slack alerts

1. In n8n, go to **Credentials → New → Slack API**
2. Add your Slack Bot OAuth token (`xoxb-...`)
3. Assign the credential to the `Slack Alert` node
4. Update the `channel` field to your actual Slack channel name

---

## 8. How to retrain

Run the training script after generating fresh feature data:

```bash
# 1. Ensure features are up to date (requires DuckDB + dbt)
python scripts/load_duckdb.py
cd dbt_project && dbt run --target duckdb --select fct_lead_scoring_features && cd ..

# 2. Export features to CSV (done by load_duckdb.py automatically)

# 3. Train
python ml/src/train.py
```

The script will:
1. Load `data/lead_scoring_features.csv`
2. Train a new XGBoost model
3. Create a new MLflow run under `Lead Scoring Optimization`
4. Overwrite `ml/lead_scoring_model.json`

The FastAPI server will use the new model on its next startup (it loads the JSON at init time, not per request).

---

## 9. How to view experiment results

**Start the MLflow UI:**

```bash
bash scripts/run_mlflow_server.sh
# or directly:
mlflow ui --backend-store-uri file://ml/mlflow --port 5001
```

Open `http://localhost:5001` to browse:

- All runs under the `Lead Scoring Optimization` experiment
- Side-by-side metric comparison between runs
- Parameter importance charts
- Registered model artefacts

**Compare runs from the CLI:**

```bash
mlflow runs list --experiment-name "Lead Scoring Optimization"
```

---

## 10. Current status and roadmap

| Item | Status |
|------|--------|
| XGBoost training on 93K rows | ✅ Complete |
| MLflow local experiment tracking | ✅ Complete |
| FastAPI `/score` endpoint | ✅ Complete |
| n8n workflow definition | ✅ Complete |
| n8n ↔ Slack integration | ⚠️ Requires manual credential setup |
| n8n ↔ HubSpot (write-back) | 🔲 Not yet implemented — planned to update contact score in CRM |
| Channel as model feature | 🔲 Planned — requires one-hot encoding in the feature pipeline |
| MLflow Model Registry | 🔲 Planned — currently uses file-based artefact store only |
| Automated retraining trigger | 🔲 Planned — would hook into `scheduled-refresh.yml` GitHub Actions workflow |
