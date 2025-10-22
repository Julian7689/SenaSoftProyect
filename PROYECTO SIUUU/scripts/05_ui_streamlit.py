# scripts/05_ui_streamlit.py
import streamlit as st
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

pipe = joblib.load(PIPE_PATH)
meta = json.loads(META_PATH.read_text(encoding="utf-8"))
EXPECTED_NUM = set(meta.get("features_num", []))
EXPECTED_CAT = set(meta.get("features_cat", []))
MODEL_VERSION = meta.get("created_at", "unknown")

st.set_page_config(page_title="Education Access Predictor", layout="centered")
st.title("🔮 Predicción de Acceso a Internet (Educación)")

st.markdown(f"**Modelo:** `education_mlp_pipeline`  \n**Versión:** `{MODEL_VERSION}`")

def align_payload_to_frame(payload):
    df = pd.DataFrame([payload])
    # completar faltantes
    for c in EXPECTED_NUM:
        if c not in df.columns: df[c] = 0
    for c in EXPECTED_CAT:
        if c not in df.columns: df[c] = "desconocido"
    # recortar a las esperadas
    expected_all = list(EXPECTED_NUM | EXPECTED_CAT)
    df = df[[c for c in df.columns if c in expected_all]]
    # tipos
    for c in EXPECTED_NUM: df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    for c in EXPECTED_CAT: df[c] = df[c].astype(str).fillna("desconocido")
    return df

def log_prediction(features, proba, label):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO predictions(created_at, model_name, model_version, features_json, proba, pred_label)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (datetime.now().isoformat(), "education_mlp_pipeline", MODEL_VERSION,
          json.dumps(features, ensure_ascii=False), float(proba), int(label)))
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return pid

with st.form("form_pred"):
    st.subheader("Variables de entrada (ejemplos)")

    region = st.selectbox("region", ["andina","caribe","pacifica","orinoquia","amazonia","desconocido"])
    estrato_promedio = st.number_input("estrato_promedio", min_value=0.0, max_value=6.0, value=2.5, step=0.1)
    tasa_pobreza = st.number_input("tasa_pobreza (0-1)", min_value=0.0, max_value=1.0, value=0.3, step=0.01)
    num_instituciones = st.number_input("num_instituciones", min_value=0, max_value=1000, value=20, step=1)
    salones_por_institucion = st.number_input("salones_por_institucion", min_value=0.0, max_value=100.0, value=12.0, step=1.0)
    docentes_por_institucion = st.number_input("docentes_por_institucion", min_value=0.0, max_value=100.0, value=20.0, step=1.0)
    computadores_por_estudiante = st.number_input("computadores_por_estudiante", min_value=0.0, max_value=5.0, value=0.5, step=0.1)
    cobertura_electrica = st.number_input("cobertura_electrica (0-1)", min_value=0.0, max_value=1.0, value=0.95, step=0.01)
    dispositivos_promedio_hogar = st.number_input("dispositivos_promedio_hogar", min_value=0.0, max_value=10.0, value=2.0, step=0.1)

    submitted = st.form_submit_button("Predecir")

if submitted:
    payload = {
        "region": region,
        "estrato_promedio": estrato_promedio,
        "tasa_pobreza": tasa_pobreza,
        "num_instituciones": num_instituciones,
        "salones_por_institucion": salones_por_institucion,
        "docentes_por_institucion": docentes_por_institucion,
        "computadores_por_estudiante": computadores_por_estudiante,
        "cobertura_electrica": cobertura_electrica,
        "dispositivos_promedio_hogar": dispositivos_promedio_hogar,
    }
    X = align_payload_to_frame(payload)
    proba = float(pipe.predict_proba(X)[:,1][0])
    label = int(proba >= 0.5)
    pid = log_prediction(payload, proba, label)

    st.success(f"Prediction ID: {pid}")
    st.metric("Probabilidad de **ACCESO**", f"{proba:.3f}")
    st.metric("Predicción", "Con Internet" if label==1 else "Sin Internet")

    st.caption("Los registros quedan guardados en data/education.db → tabla `predictions`.")
