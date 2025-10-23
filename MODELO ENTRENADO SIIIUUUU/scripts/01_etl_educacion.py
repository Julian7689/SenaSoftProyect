# scripts/01_etl_educacion.py
import re, json
from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# -----------------------------
# Rutas
# -----------------------------
BASE = Path(__file__).resolve().parents[1]
DATA_RAW = BASE / "data" / "raw"
DATA_INTERIM = BASE / "data" / "interim"
DATA_PROCESSED = BASE / "data" / "processed"
PLOTS = BASE / "plots"

PLOTS.mkdir(parents=True, exist_ok=True)
DATA_INTERIM.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

# -----------------------------
# Fuente de datos (PRIORIDAD: SINTÉTICO -> ORIGINAL)
# -----------------------------
SRC_SYNTH = DATA_RAW / "synthetic_education_dataset.csv"
SRC_ORIG  = DATA_RAW / "dataset_comunidades_senasoft.csv"

if SRC_SYNTH.exists():
    SRC = SRC_SYNTH
    source_name = "synthetic_education_dataset.csv"
else:
    SRC = SRC_ORIG
    source_name = "dataset_comunidades_senasoft.csv"

df = pd.read_csv(SRC)

print(f"[ETL] Fuente usada: {source_name}")
print("[ETL] Shape raw:", df.shape)
print("[ETL] Primeras columnas:", list(df.columns)[:15])

# -----------------------------
# Normalización de nombres
# -----------------------------
def slugify(col: str) -> str:
    col = col.strip()
    col = (col.replace("Á","A").replace("É","E").replace("Í","I").replace("Ó","O").replace("Ú","U")
               .replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u").replace("ñ","n"))
    col = re.sub(r"[^0-9a-zA-Z]+", "_", col)
    col = re.sub(r"_+", "_", col).strip("_").lower()
    return col

df.columns = [slugify(c) for c in df.columns]

# -----------------------------
# Normalización de binarios
# -----------------------------
BIN_TRUE = {"1", 1, "si", "sí", "true", "t", "y", "yes", "x"}
BIN_FALSE = {"0", 0, "no", "false", "f", "n"}

def normalize_binary(series: pd.Series):
    def map_val(v):
        if pd.isna(v): return np.nan
        s = str(v).strip().lower()
        if s in {"nan", ""}: return np.nan
        if s in {str(x).lower() for x in BIN_TRUE}: return 1
        if s in {str(x).lower() for x in BIN_FALSE}: return 0
        try:
            f = float(s)
            if f == 1.0: return 1
            if f == 0.0: return 0
        except:
            pass
        return v
    return series.map(map_val)

# Detectar columnas potencialmente binarias (heurística)
binary_candidates = []
for c in df.columns:
    vals = set(str(v).strip().lower() for v in df[c].dropna().unique()[:50])
    if vals <= {"0","1","si","sí","no","true","false","t","f","y","n","x"} or vals <= {"0","1"}:
        binary_candidates.append(c)

for c in binary_candidates:
    df[c] = normalize_binary(df[c])

# -----------------------------
# Imputación de faltantes
# -----------------------------
numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
categorical_cols = [c for c in df.columns if c not in numeric_cols]

for c in numeric_cols:
    if df[c].isna().any():
        df[c] = df[c].fillna(df[c].median())
for c in categorical_cols:
    df[c] = df[c].fillna("desconocido")

# -----------------------------
# Selección de columnas EDU + contexto
# -----------------------------
# Keywords ampliadas (incluye "4g" para el sintético)
edu_keywords = [
    "educ", "escuel", "coleg", "internet", "bibliot", "comput", "tecno", "conect",
    "formacion", "alfabet", "docent", "estudiant", "matricula", "infra", "capacit",
    "disposit", "tics", "curric", "energia", "servicio", "salon", "profes", "niv_",
    "acceso", "comunic", "institu", "programa", "4g"
]

edu_cols = [c for c in df.columns if any(k in c for k in edu_keywords)]

# Whitelist de columnas educativas y de contexto clave del dataset sintético (se añaden si existen)
synthetic_whitelist = [
    "municipio_id", "region",
    "poblacion_total", "porcentaje_rural", "estrato_promedio", "tasa_pobreza",
    "num_instituciones", "salones_por_institucion", "docentes_por_institucion",
    "computadores_por_estudiante",
    "cobertura_electrica", "cobertura_4g",
    "dispositivos_promedio_hogar",
    "tasa_aprobacion", "tasa_desercion", "puntaje_pruebas",
    "tiene_biblioteca", "lab_tecnologia",
    "servicios_publicos", "agua_potable", "transporte_publico",
    "acceso_a_internet",
    # compatibilidad con posibles campos del dataset original
    "zona_rural", "genero", "edad", "poblacion", "ingreso", "departamento", "municipio"
]

for c in synthetic_whitelist:
    if c in df.columns and c not in edu_cols:
        edu_cols.append(c)

# Asegurar target explícito si existe
if "acceso_a_internet" in df.columns and "acceso_a_internet" not in edu_cols:
    edu_cols.append("acceso_a_internet")

# Contexto adicional (limitado para no crecer demasiado)
context_cols = []
for c in df.columns:
    if c not in edu_cols:
        if any(k in c for k in [
            "zona","rural","urb","estrato","poblacion","ingreso","region","departamento",
            "municipio","barrio","genero","edad","nbi","pobre","empleo","servicio","transporte",
            "energia","vivienda","agua","seguridad"
        ]):
            context_cols.append(c)

# Permitir más contexto (20) — antes eran 10
context_cols = context_cols[:20]

edu_dataset_cols = sorted(set(edu_cols + context_cols))
edu_df = df[edu_dataset_cols].copy()

print(f"[ETL] Columnas seleccionadas para EDU: {len(edu_dataset_cols)}")
print("[ETL] Algunas columnas EDU:", edu_dataset_cols[:20])

# -----------------------------
# Guardar datasets
# -----------------------------
clean_path = DATA_PROCESSED / "clean_dataset.csv"
edu_path = DATA_PROCESSED / "education_dataset.csv"
df.to_csv(clean_path, index=False)
edu_df.to_csv(edu_path, index=False)

# -----------------------------
# Target prioritario
# -----------------------------
target = "acceso_a_internet" if "acceso_a_internet" in edu_df.columns else None
if target is None:
    # fallback por texto
    candidates = [c for c in edu_df.columns if "internet" in c or "conect" in c]
    target = candidates[0] if candidates else None
if target is None:
    # fallback por binarios
    bin_edu = [c for c in edu_df.columns if set(pd.Series(edu_df[c]).dropna().unique()) <= {0,1}]
    target = bin_edu[0] if bin_edu else None

# -----------------------------
# Gráficas
# -----------------------------
# 1) Nulos (top 20)
null_counts = df.isna().sum().sort_values(ascending=False).head(20)
plt.figure()
null_counts.plot(kind="bar")
plt.title("Top 20 columnas con más valores nulos")
plt.ylabel("Cantidad de nulos")
plt.tight_layout()
plt.savefig(BASE / "plots" / "nulls_top20.png")
plt.close()

# 2) Balance de clases (si target binario)
if target and set(pd.Series(edu_df[target]).dropna().unique()) <= {0,1}:
    class_counts = edu_df[target].value_counts().sort_index()
    plt.figure()
    class_counts.plot(kind="bar")
    plt.title(f"Balance de clases - {target}")
    plt.xlabel("Clase")
    plt.ylabel("Frecuencia")
    plt.tight_layout()
    plt.savefig(BASE / "plots" / "class_balance.png")
    plt.close()

# 3) Correlación numérica (solo si hay al menos 2 numéricas)
num_for_corr = edu_df.select_dtypes(include=[np.number])
if num_for_corr.shape[1] >= 2:
    corr = num_for_corr.corr(numeric_only=True)
    plt.figure()
    plt.imshow(corr, aspect='auto', interpolation='nearest')
    plt.colorbar()
    plt.title("Matriz de correlación (numérica) - EDU dataset")
    plt.xticks(range(corr.shape[1]), corr.columns, rotation=90)
    plt.yticks(range(corr.shape[0]), corr.index)
    plt.tight_layout()
    plt.savefig(BASE / "plots" / "corr_matrix.png", dpi=200)
    plt.close()

# -----------------------------
# Reporte ETL
# -----------------------------
report = [
    f"# ETL Report - {datetime.now():%Y-%m-%d %H:%M}",
    f"- Fuente usada: {source_name}",
    f"- Registros (raw): {len(df):,}",
    f"- Columnas totales (raw): {len(df.columns)}",
    f"- Columnas binarias normalizadas: {len(binary_candidates)}",
    f"- Columnas EDU detectadas: {len(edu_cols)}",
    f"- Columnas contexto incluidas: {len(context_cols)}",
    f"- Columnas finales EDU: {len(edu_dataset_cols)}",
    f"- Target seleccionado: {target}",
]
(DATA_INTERIM / "etl_report.md").write_text("\n".join(report), encoding="utf-8")

print("\nETL OK ✅")
print(f"clean_dataset.csv → {clean_path}")
print(f"education_dataset.csv → {edu_path}")
print(f"Target: {target}")
