# scripts/03_db_init.py
from pathlib import Path
import sqlite3
import json
from datetime import datetime

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data"
DATA.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA / "education.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        model_name TEXT NOT NULL,
        model_version TEXT,
        features_json TEXT NOT NULL,
        proba REAL,
        pred_label INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prediction_id INTEGER,
        true_label INTEGER,
        notes TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(prediction_id) REFERENCES predictions(id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS metadata (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE,
        value TEXT
    )
    """)

    # opcional: registrar versión de modelo
    models_dir = BASE / "models"
    meta_file = models_dir / "model_meta.json"
    model_version = None
    if meta_file.exists():
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        model_version = meta.get("created_at")

    cur.execute("INSERT OR REPLACE INTO metadata(key, value) VALUES(?,?)",
                ("model_in_use", json.dumps({
                    "path": str(models_dir / "education_mlp_pipeline.joblib"),
                    "version": model_version,
                    "registered_at": datetime.now().isoformat()
                })))
    conn.commit()
    conn.close()
    print(f"DB creada/actualizada en {DB_PATH}")

if __name__ == "__main__":
    main()
