from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import xgboost as xgb
import pandas as pd
from pathlib import Path

app = FastAPI(title="Lead Scoring API", description="Predicts conversion probability for leads.")

# Paths
MODEL_PATH = Path(__file__).parent.parent / "ml" / "lead_scoring_model.json"

# Load model on startup
model = None
if MODEL_PATH.exists():
    model = xgb.XGBClassifier()
    model.load_model(str(MODEL_PATH))

# Must match ml/src/train.py exactly — the model was trained on these four
# columns in this order. country/channel are NOT model features today; they are
# accepted for lead-routing metadata only and must never adjust the score
# (a post-hoc multiplier on model output is a fabricated probability).
MODEL_FEATURES = ["sessions", "engaged_sessions", "page_views", "is_first_visit"]

class LeadFeatures(BaseModel):
    sessions: int
    engaged_sessions: int
    page_views: int
    country: str
    channel: str
    is_first_visit: bool

@app.get("/health")
def health():
    return {"status": "healthy", "model_loaded": model is not None}

@app.post("/score")
def score_lead(features: LeadFeatures):
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    x_input = pd.DataFrame([{
        "sessions":         features.sessions,
        "engaged_sessions": features.engaged_sessions,
        "page_views":       features.page_views,
        "is_first_visit":   1 if features.is_first_visit else 0,
    }], columns=MODEL_FEATURES)

    prob = float(model.predict_proba(x_input)[:, 1][0])

    return {
        "score": prob,
        "lead_tier": "A" if prob > 0.8 else "B" if prob > 0.5 else "C",
        "recommendation": "High priority: Instant sales follow-up" if prob > 0.8 else "Nurture: Add to email drip",
        "model_features_used": MODEL_FEATURES,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
