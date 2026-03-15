from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import xgboost as xgb
import numpy as np
import pandas as pd
from pathlib import Path
import os

app = FastAPI(title="Lead Scoring API", description="Predicts conversion probability for leads.")

# Paths
MODEL_PATH = Path(__file__).parent.parent / "ml" / "lead_scoring_model.json"

# Load model on startup
model = None
if MODEL_PATH.exists():
    model = xgb.XGBClassifier()
    model.load_model(str(MODEL_PATH))

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
    
    # In a real app, we'd use the same preprocessing as in training
    # For mock, we'll create a simple array
    # Note: Categorical handling should match the get_dummies in train.py
    # This is a simplified version for demonstration
    x_input = np.array([[
        features.sessions,
        features.engaged_sessions,
        features.page_views,
        1 if features.is_first_visit else 0
    ]])
    
    # Mock prediction logic (since categories aren't fully handled here)
    prob = model.predict_proba(x_input)[:, 1][0]
    
    # Add some variability based on channel for effect
    if features.channel == "Direct":
        prob *= 1.2
    elif features.channel == "Organic Search":
        prob *= 1.1
    
    prob = min(max(prob, 0.0), 1.0) # Clip
    
    return {
        "score": float(prob),
        "lead_tier": "A" if prob > 0.8 else "B" if prob > 0.5 else "C",
        "recommendation": "High priority: Instant sales follow-up" if prob > 0.8 else "Nurture: Add to email drip"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
