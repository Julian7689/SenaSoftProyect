# scripts/04_serve_api.py
from fastapi import FastAPI, Body
from pydantic import BaseModel
from typing import Dict, Any, Optional
from pathlib import Path
import pandas as pd
import numpy as np
import joblib, json, sqlite3
from datetime import datetime

BASE = Path(__file__).resolve().parents[1]
MODELS = BASE / "models"
DATA = BASE / "data"
DB_PATH = DATA / "education.db"

PIPE_PATH = MODELS / "education_mlp_pipeline.joblib"
META_PATH = MODELS / "model_meta.json"

# Carga modelo y metadatos
pipe = joblib.load(PIPE_PATH)
meta = json.loads(META_PATH.read_text(encoding="utf-8"))
EXPECTED_NUM = set(meta.get("features_num", []))
EXPECTED_CAT = set(meta.get("features_cat", []))
MODEL_VERSION = meta.get("created_at", "unknown")

app = FastAPI(title="Education Access API", version="1.0")

def align_payload_to_frame(payload: Dict[str, Any]) -> pd.DataFrame:
    """Alinea el diccionario de entrada a las columnas esperadas por el pipeline."""
    # payload → DataFrame 1 fila
    df = pd.DataFrame([payload])

    # asegurar columnas esperadas
    for col in EXPECTED_NUM:
        if col not in df.columns:
            df[col] = 0
    for col in EXPECTED_CAT:
        if col not in df.columns:
            df[col] = "desconocido"

    # quitar columnas extrañas (no vistas en entrenamiento) para evitar sorpresas
    expected_all = list(EXPECTED_NUM | EXPECTED_CAT)
    # mantener también cualquier columna num/cat que pipe pueda procesar (por si meta tenía menos)
    # pero en general stick to meta:
    df = df[[c for c in df.columns if c in expected_all]]

    # asegurar tipos básicos
    for c in EXPECTED_NUM:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    for c in EXPECTED_CAT:
        df[c] = df[c].astype(str).fillna("desconocido")

    return df

def log_prediction(features: Dict[str, Any], proba: float, pred_label: int) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO predictions(created_at, model_name, model_version, features_json, proba, pred_label)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        "education_mlp_pipeline",
        MODEL_VERSION,
        json.dumps(features, ensure_ascii=False),
        float(proba),
        int(pred_label)
    ))
    conn.commit()
    pred_id = cur.lastrowid
    conn.close()
    return pred_id

class PredictIn(BaseModel):
    data: Dict[str, Any]

class PredictOut(BaseModel):
    prediction_id: int
    pred_label: int
    proba: float
    model_version: str

class FeedbackIn(BaseModel):
    prediction_id: int
    true_label: int
    notes: Optional[str] = None

@app.get("/health")
def health():
    return {"status": "ok", "model_version": MODEL_VERSION}

@app.post("/predict", response_model=PredictOut)
def predict(payload: PredictIn):
    X = align_payload_to_frame(payload.data)
    proba = pipe.predict_proba(X)[:, 1][0]
    label = int(proba >= 0.5)
    pred_id = log_prediction(payload.data, proba, label)
    return PredictOut(
        prediction_id=pred_id,
        pred_label=label,
        proba=float(proba),
        model_version=MODEL_VERSION
    )

@app.post("/feedback")
def feedback(fb: FeedbackIn):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO feedback(prediction_id, true_label, notes, created_at)
        VALUES (?, ?, ?, ?)
    """, (fb.prediction_id, fb.true_label, fb.notes, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return {"ok": True, "prediction_id": fb.prediction_id}
