# scripts/00_bootstrap.py
from pathlib import Path
import shutil

BASE = Path(__file__).resolve().parents[1]
DATA_RAW = BASE / "data" / "raw"
DATA_INTERIM = BASE / "data" / "interim"
DATA_PROCESSED = BASE / "data" / "processed"
MODELS = BASE / "models"
PLOTS = BASE / "plots"
APP = BASE / "app"
SCRIPTS = BASE / "scripts"
DOCS = BASE / "docs"

for p in [DATA_RAW, DATA_INTERIM, DATA_PROCESSED, MODELS, PLOTS, APP, SCRIPTS, DOCS]:
    p.mkdir(parents=True, exist_ok=True)

# Cambia esta ruta a tu archivo original
SOURCE_CSV = Path(r"C:/Users/AdminSena/Desktop/PROYECTO SIUUU/data/dataset_comunidades_senasoft.csv")


if SOURCE_CSV.exists():
    dst = DATA_RAW / "dataset_comunidades_senasoft.csv"
    if not dst.exists():
        shutil.copy2(SOURCE_CSV, dst)
        print(f"Copiado a {dst}")
    else:
        print("El archivo ya existe en data/raw/.")
else:
    print("⚠️ Ajusta SOURCE_CSV a la ruta correcta de tu CSV.")
