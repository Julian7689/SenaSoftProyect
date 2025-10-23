# scripts/01c_etl_educacion_noleak.py
# ETL PLUS con barreras anti-fuga de información (data leakage)
# Salida: data/processed/education_dataset_plus_noleak.csv
import re
from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd

# -----------------------------
# Rutas
# -----------------------------
BASE = Path(__file__).resolve().parents[1]
DATA_RAW = BASE / "data" / "raw"
DATA_INTERIM = BASE / "data" / "interim"
DATA_PROCESSED = BASE / "data" / "processed"

DATA_INTERIM.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

RAW_SYNTH = DATA_RAW / "synthetic_education_dataset.csv"
RAW_ORIG  = DATA_RAW / "dataset_comunidades_senasoft.csv"

# -----------------------------
# Lectura priorizando el sintético
# -----------------------------
if RAW_SYNTH.exists():
    SRC = RAW_SYNTH
    source_name = RAW_SYNTH.name
else:
    SRC = RAW_ORIG
    source_name = RAW_ORIG.name

df = pd.read_csv(SRC)
print(f"[ETL] Fuente usada: {source_name}")
print("[ETL] Shape raw:", df.shape)

# -----------------------------
# Utilidades
# -----------------------------
def slugify(s: str) -> str:
    s = s.strip()
    s = (s.replace("Á","A").replace("É","E").replace("Í","I").replace("Ó","O").replace("Ú","U")
           .replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u").replace("ñ","n"))
    s = re.sub(r"[^0-9a-zA-Z]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_").lower()
    return s

def normalize_binary(series: pd.Series):
    BIN_TRUE  = {"1", 1, "si", "sí", "true", "t", "y", "yes", "x"}
    BIN_FALSE = {"0", 0, "no", "false", "f", "n"}
    def map_val(v):
        if pd.isna(v): return np.nan
        s = str(v).strip().lower()
        if s in {"nan",""}: return np.nan
        if s in {str(x).lower() for x in BIN_TRUE}: return 1
        if s in {str(x).lower() for x in BIN_FALSE}: return 0
        try:
            f = float(s)
            if f == 1.0: return 1
            if f == 0.0: return 0
        except: pass
        return v
    return series.map(map_val)

def add_ratio_safe(df, a, b, out):
    if a in df.columns and b in df.columns and out not in df.columns:
        df[out] = df[a] / (df[b].replace(0, np.nan) + 1)
        df[out] = df[out].replace([np.inf, -np.inf], np.nan).fillna(0)

# -----------------------------
# 1) Normalización de columnas
# -----------------------------
df.columns = [slugify(c) for c in df.columns]

# -----------------------------
# 2) Normalización de binarios + imputación
# -----------------------------
# detectar binarios candidatos
binary_candidates = []
for c in df.columns:
    vals = set(str(v).strip().lower() for v in df[c].dropna().unique()[:50])
    if vals <= {"0","1","si","sí","no","true","false","t","f","y","n","x"} or vals <= {"0","1"}:
        binary_candidates.append(c)
for c in binary_candidates:
    df[c] = normalize_binary(df[c])

num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
cat_cols = [c for c in df.columns if c not in num_cols]

for c in num_cols:
    if df[c].isna().any():
        df[c] = df[c].fillna(df[c].median())
for c in cat_cols:
    df[c] = df[c].fillna("desconocido")

# -----------------------------
# 3) Subconjunto EDU + contexto
# -----------------------------
edu_kw = [
    "educ","escuel","coleg","internet","bibliot","comput","tecno","conect",
    "formacion","alfabet","docent","estudiant","matricula","infra","capacit",
    "disposit","tics","curric","energia","servicio","salon","profes","niv_",
    "acceso","comunic","institu","programa","4g"
]
edu_cols = [c for c in df.columns if any(k in c for k in edu_kw)]

# whitelist común (sintético)
whitelist = [
    "municipio_id","region",
    "poblacion_total","porcentaje_rural","estrato_promedio","tasa_pobreza",
    "num_instituciones","salones_por_institucion","docentes_por_institucion",
    "computadores_por_estudiante","cobertura_electrica","cobertura_4g",
    "dispositivos_promedio_hogar","tasa_aprobacion","tasa_desercion","puntaje_pruebas",
    "tiene_biblioteca","lab_tecnologia","servicios_publicos","agua_potable","transporte_publico",
    "zona_rural","genero","edad","poblacion","ingreso","departamento","municipio",
    "acceso_a_internet"
]
for c in whitelist:
    if c in df.columns and c not in edu_cols:
        edu_cols.append(c)

# contexto adicional (limitado)
ctx_kw = ["zona","rural","urb","estrato","poblacion","ingreso","region","departamento",
          "municipio","barrio","genero","edad","nbi","pobre","empleo","transporte",
          "energia","vivienda","agua","seguridad"]
ctx_cols = [c for c in df.columns if (c not in edu_cols) and any(k in c for k in ctx_kw)]
ctx_cols = ctx_cols[:20]

base_cols = sorted(set(edu_cols + ctx_cols))
E = df[base_cols].copy()

# -----------------------------
# 4) Feature engineering SEGURO (evita usar el target)
# -----------------------------
target = "acceso_a_internet" if "acceso_a_internet" in E.columns else None

# ejemplos de ratios (solo si existen columnas)
add_ratio_safe(E, "computadores_por_estudiante", "num_instituciones", "comp_per_inst_ratio")
add_ratio_safe(E, "docentes_por_institucion", "salones_por_institucion", "docente_salon_ratio")
add_ratio_safe(E, "poblacion_total", "num_instituciones", "pob_por_inst")
add_ratio_safe(E, "tasa_aprobacion", "tasa_desercion", "aprob_deserc_ratio")

# -----------------------------
# 5) DETECCIÓN Y BLOQUEO DE LEAKAGE
# -----------------------------
reasons = {}  # col -> reason

# 5.1 Reglas por NOMBRE (blacklist)
name_blacklist = [
    "internet", "conect", "tic", "idx_tic", "wifi", "banda", "ancho", "fibra", "4g"
]
suspect_by_name = [c for c in E.columns if any(k in c for k in name_blacklist) and c != target]
for c in suspect_by_name:
    reasons[c] = "name_match"

# 5.2 Correlación numérica extremadamente alta con el target (si target es binario)
if target and target in E.columns and pd.api.types.is_numeric_dtype(E[target]):
    num_cols_E = [c for c in E.columns if pd.api.types.is_numeric_dtype(E[c]) and c != target]
    if num_cols_E:
        corr = E[num_cols_E + [target]].corr(numeric_only=True)[target].drop(labels=[target], errors="ignore")
        high_corr = corr[abs(corr) >= 0.95].index.tolist()
        for c in high_corr:
            reasons[c] = f"high_corr_{float(corr[c]):.3f}"

# 5.3 Igualdad/duplicidad directa con el target (binaria)
if target and target in E.columns:
    # columnas binarias que igualan al target casi perfectamente
    for c in E.columns:
        if c == target: 
            continue
        # si ambas son binarias o casi binarias
        if set(pd.Series(E[c]).dropna().unique()) <= {0,1}:
            same_ratio = (E[c] == E[target]).mean()
            if same_ratio >= 0.98:
                reasons[c] = f"near_duplicate_to_target_{same_ratio:.3f}"

# 5.4 Categóricas con mapeo perfecto a una sola clase (entropía ~0 por categoría)
if target and target in E.columns:
    y = E[target]
    for c in E.columns:
        if c == target: 
            continue
        if not pd.api.types.is_numeric_dtype(E[c]):
            # por cada categoría, si siempre la misma clase → sospechosa
            vc = E.groupby(c)[target].nunique(dropna=True)
            if (vc.max() == 1) and (E[c].nunique() > 1):
                reasons[c] = "category_to_single_class_map"

# construir lista final de columnas a eliminar
leak_cols = sorted(set(reasons.keys()))

if leak_cols:
    print("\n[LEAKAGE] Columnas eliminadas por sospecha de fuga:")
    for c in leak_cols:
        print(f" - {c:30s}  ({reasons[c]})")
    E_nl = E.drop(columns=leak_cols).copy()
else:
    print("\n[LEAKAGE] No se detectaron columnas sospechosas.")
    E_nl = E.copy()

# -----------------------------
# 6) Guardado + reporte
# -----------------------------
OUT_PATH = DATA_PROCESSED / "education_dataset_plus_noleak.csv"
E_nl.to_csv(OUT_PATH, index=False)

report_lines = [
    f"# ETL Educación NO-LEAK - {datetime.now():%Y-%m-%d %H:%M}",
    f"- Fuente usada: {source_name}",
    f"- Registros: {len(E_nl):,}",
    f"- Columnas finales: {len(E_nl.columns)}",
    f"- Target: {target}",
    f"- Leak columns detectadas: {len(leak_cols)}",
]
if leak_cols:
    report_lines += [f"  - {c} :: {reasons[c]}" for c in leak_cols]

(DATA_INTERIM / "etl_noleak_report.md").write_text("\n".join(report_lines), encoding="utf-8")

print("\nETL NO-LEAK OK ✅")
print(f"Archivo: {OUT_PATH}")
print(f"Columnas eliminadas por fuga: {leak_cols if leak_cols else '(ninguna)'}")
