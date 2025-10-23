# scripts/06_score_batch.py
import argparse
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

def align_df(df: pd.DataFrame) -> pd.DataFrame:
    for c in EXPECTED_NUM:
        if c not in df.columns: df[c] = 0
    for c in EXPECTED_CAT:
        if c not in df.columns: df[c] = "desconocido"
    expected_all = list(EXPECTED_NUM | EXPECTED_CAT)
    df = df[[c for c in df.columns if c in expected_all]]
    for c in EXPECTED_NUM: df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    for c in EXPECTED_CAT: df[c] = df[c].astype(str).fillna("desconocido")
    return df

def log_row(features: dict, proba: float, label: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO predictions(created_at, model_name, model_version, features_json, proba, pred_label)
        VALUES (?,?,?,?,?,?)
    """, (datetime.now().isoformat(), "education_mlp_pipeline", MODEL_VERSION,
          json.dumps(features, ensure_ascii=False), float(proba), int(label)))
    conn.commit()
    conn.close()

def main(inp: Path, logdb: bool):
    df = pd.read_csv(inp)
    X = align_df(df.copy())
    probs = pipe.predict_proba(X)[:,1]
    preds = (probs >= 0.5).astype(int)

    out = df.copy()
    out["proba"] = probs
    out["pred_label"] = preds

    out_path = inp.with_name(inp.stem + "_scored.csv")
    out.to_csv(out_path, index=False)
    print(f"Guardado: {out_path}")

    if logdb:
        for i, row in df.iterrows():
            features = {c: row[c] for c in df.columns}
            log_row(features, float(probs[i]), int(preds[i]))
        print(f"Se registraron {len(df)} filas en la DB.")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Ruta del CSV a evaluar")
    ap.add_argument("--logdb", action="store_true", help="Registrar cada fila en SQLite")
    args = ap.parse_args()
    main(Path(args.input), args.logdb)
