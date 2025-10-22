# app/app.py
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from pathlib import Path
from datetime import datetime
import joblib, json, sqlite3, os
import pandas as pd

APP_DIR = Path(__file__).resolve().parent
BASE = APP_DIR.parents[1]
MODEL_PATH = BASE / "models" / "education_mlp_pipeline.joblib"
DB_PATH = APP_DIR / "predictions.db"

app = FastAPI(title="EducAI - Predicción Acceso a Internet")

class InputPayload(BaseModel):
    features: dict

# Crear tabla si no existe
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS predictions_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT,
        input_json TEXT,
        predicted_label INTEGER,
        predicted_proba REAL
    );
    """)
    conn.commit()
    conn.close()

init_db()

def load_model():
    return joblib.load(MODEL_PATH)

def predict_and_log(model, features: dict):
    X = pd.DataFrame([features])
    try:
        proba = float(model.predict_proba(X)[0,1])
    except Exception:
        proba = None
    pred = int(model.predict(X)[0])

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO predictions_log (created_at, input_json, predicted_label, predicted_proba) VALUES (?, ?, ?, ?)",
        (datetime.now().isoformat(), json.dumps(features, ensure_ascii=False), pred, proba)
    )
    conn.commit()
    conn.close()
    return pred, proba

@app.get("/", response_class=HTMLResponse)
def index():
    html = '''
    <html>
    <head><title>EducAI</title></head>
    <body>
        <h2>EducAI - Predicción de Acceso a Internet (proxy inclusión educativa)</h2>
        <form method="post" action="/predict_form">
            <p>Ingrese pares clave=valor en JSON (solo las features del modelo):</p>
            <textarea name="payload" rows="14" cols="90">{}</textarea><br/>
            <button type="submit">Predecir</button>
        </form>
        <p>Endpoints:</p>
        <ul>
            <li>POST /predict (JSON: {"features": {...}})</li>
            <li>GET /logs</li>
        </ul>
    </body>
    </html>
    '''
    return HTMLResponse(html)

@app.post("/predict")
def predict(payload: InputPayload):
    model = load_model()
    pred, proba = predict_and_log(model, payload.features)
    return {"predicted_label": pred, "predicted_proba": proba}

@app.post("/predict_form")
async def predict_form(payload: str = Form(...)):
    model = load_model()
    try:
        features = json.loads(payload)
    except Exception:
        return RedirectResponse("/", status_code=303)
    pred, proba = predict_and_log(model, features)
    return {"predicted_label": pred, "predicted_proba": proba, "features": features}

@app.get("/logs")
def logs():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, created_at, input_json, predicted_label, predicted_proba FROM predictions_log ORDER BY id DESC LIMIT 100")
    rows = cur.fetchall()
    conn.close()
    return {"rows": rows}
