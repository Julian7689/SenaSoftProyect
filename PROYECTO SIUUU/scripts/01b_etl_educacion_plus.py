# scripts/01b_etl_educacion_plus.py
# ETL extendido y feature engineering para Educación
# Genera: data/processed/education_dataset_plus.csv

import re
from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
DATA_RAW = BASE / "data" / "raw"
DATA_INTERIM = BASE / "data" / "interim"
DATA_PROCESSED = BASE / "data" / "processed"

DATA_INTERIM.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

RAW_SYNTH = DATA_RAW / "synthetic_education_dataset.csv"      # NUEVO: fuente sintética si existe
RAW_PATH  = DATA_RAW / "dataset_comunidades_senasoft.csv"
CLEAN_PATH = DATA_PROCESSED / "clean_dataset.csv"

# -------------------------
# 1) Cargar (prioriza clean; si no, intenta sintético; si no, raw original)
# -------------------------
if CLEAN_PATH.exists():
    df = pd.read_csv(CLEAN_PATH)
elif RAW_SYNTH.exists():
    df = pd.read_csv(RAW_SYNTH)
else:
    df = pd.read_csv(RAW_PATH)

# -------------------------
# 2) Normalización columnas y binarios
# -------------------------
def slugify(s: str) -> str:
    s = s.strip()
    s = (s.replace("Á","A").replace("É","E").replace("Í","I").replace("Ó","O").replace("Ú","U")
           .replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u").replace("ñ","n"))
    s = re.sub(r"[^0-9a-zA-Z]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_").lower()
    return s

df.columns = [slugify(c) for c in df.columns]

BIN_TRUE = {"1", 1, "si", "sí", "true", "t", "y", "yes", "x"}
BIN_FALSE = {"0", 0, "no", "false", "f", "n"}

def normalize_binary(series: pd.Series):
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

# Detectar binarias y normalizar
for c in df.columns:
    vals = set(str(v).strip().lower() for v in df[c].dropna().unique()[:50])
    if vals <= {"0","1","si","sí","no","true","false","t","f","y","n","x"} or vals <= {"0","1"}:
        df[c] = normalize_binary(df[c])

# Tipos e imputación
num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
cat_cols = [c for c in df.columns if c not in num_cols]

for c in num_cols:
    if df[c].isna().any():
        df[c] = df[c].fillna(df[c].median())
for c in cat_cols:
    df[c] = df[c].fillna("desconocido")

# -------------------------
# 3) Selección EDU y contexto (más amplia)
# -------------------------
edu_kw = [
    "educ","escuel","coleg","internet","bibliot","comput","tecno","conect",
    "formacion","alfabet","docent","estudiant","matricula","infra","capacit",
    "disposit","tics","curric","servicio","salon","profes","institu","acceso"
]
edu_cols = [c for c in df.columns if any(k in c for k in edu_kw)]

# target preferido
target = "acceso_a_internet" if "acceso_a_internet" in df.columns else None
if target and target not in edu_cols:
    edu_cols.append(target)

# contexto ampliado
ctx_kw = [
    "zona","rural","urb","estrato","poblacion","ingreso","region","departamento",
    "municipio","barrio","genero","edad","nbi","pobre","empleo","transporte",
    "energia","vivienda","agua","seguridad","servicios_publicos"
]
ctx_cols = [c for c in df.columns if any(k in c for k in ctx_kw)]
ctx_cols = ctx_cols[:20]  # límite de contexto

base_cols = sorted(set(edu_cols + ctx_cols))
E = df[base_cols].copy()
created = []

def exists(*cols):
    return all(col in E.columns for col in cols)

def add_ratio(num1, num2, out):
    if exists(num1, num2) and out not in E.columns:
        E[out] = E[num1] / (E[num2].replace(0, np.nan) + 1)
        E[out] = E[out].replace([np.inf, -np.inf], np.nan).fillna(0)
        created.append(out)

def add_sum(cols, out):
    if all(col in E.columns for col in cols) and out not in E.columns:
        E[out] = E[cols].sum(axis=1, skipna=True)
        created.append(out)

def add_mean(cols, out):
    if all(col in E.columns for col in cols) and out not in E.columns:
        E[out] = E[cols].mean(axis=1)
        created.append(out)

def add_interaction(a, b, out):
    if exists(a, b) and out not in E.columns:
        E[out] = E[a] * E[b]
        created.append(out)

def add_bin(src, quantiles, prefix):
    if src in E.columns and pd.api.types.is_numeric_dtype(E[src]):
        qs = np.clip(quantiles, 0, 1)
        bins = E[src].quantile(qs).values
        bins = np.unique(np.concatenate([[E[src].min()-1], bins, [E[src].max()+1]])).astype(float)
        labels = [f"{prefix}_q{i+1}" for i in range(len(bins)-1)]
        colname = f"{prefix}_bin"
        E[colname] = pd.cut(E[src], bins=bins, labels=labels, include_lowest=True)
        created.append(colname)

# -------------------------
# 4) Feature Engineering (SIN USAR el target)
# -------------------------

# Ratios (solo si existen)
add_ratio("computadores_funcionales", "poblacion", "ratio_comp_poblacion")
add_ratio("computadores_funcionales", "matriculas", "ratio_comp_matriculas")
add_ratio("docentes", "matriculas", "ratio_docente_alumno")
add_ratio("instituciones", "poblacion", "ratio_instituciones_pob")
# Compatibilidad con dataset sintético
add_ratio("computadores_por_estudiante", "num_instituciones", "comp_per_inst_proxy")

# Índices (excluir target explícitamente)
def index_from(parts, out, target_name=None):
    valid = []
    for c in parts:
        if (target_name is not None) and (c == target_name):
            continue
        if c in E.columns and pd.api.types.is_numeric_dtype(E[c]):
            valid.append(c)
    if not valid:
        return
    temp = E[valid].copy()
    for c in valid:
        mn, mx = temp[c].min(), temp[c].max()
        if mx > mn:
            temp[c] = (temp[c] - mn) / (mx - mn)
        else:
            temp[c] = 0.0
    E[out] = temp.mean(axis=1)
    created.append(out)

# Listas de partes (cuidar que NO incluyan el target)
tic_parts = [c for c in E.columns if any(k in c for k in ["internet","conect","comput","tics","disposit"])]
infra_parts = [c for c in E.columns if any(k in c for k in ["infra","salon","bibliot","laboratorio","institu"])]
socio_parts = [c for c in E.columns if any(k in c for k in ["estrato","nbi","pobre","ingreso"])]

index_from(tic_parts, "idx_tic", target_name=target)
index_from(infra_parts, "idx_infra_educ", target_name=target)
index_from(socio_parts, "idx_socio", target_name=target)

# Interacciones (no combinamos con el target)
if "zona_rural" in E.columns:
    for col in ["idx_tic","idx_infra_educ","idx_socio","estrato","poblacion","poblacion_total"]:
        if col in E.columns:
            add_interaction("zona_rural", col, f"int_rural_{col}")

# Discretizaciones (bines)
for col in ["poblacion","ingreso","matriculas","docentes","computadores_funcionales",
            "poblacion_total","num_instituciones","computadores_por_estudiante"]:
    if col in E.columns and pd.api.types.is_numeric_dtype(E[col]):
        add_bin(col, np.array([0.25,0.5,0.75]), f"{col}")

# Proxies de entorno habilitante
serv_cols = [c for c in E.columns if any(k in c for k in ["energia","agua","servicios_publicos","transporte","seguridad"])]
if serv_cols:
    add_sum(serv_cols, "servicios_total")
    add_mean(serv_cols, "servicios_mean")

edu_avail_cols = [c for c in E.columns if any(k in c for k in ["bibliot","laboratorio","salon","institu","docent","comput"])]
if edu_avail_cols:
    add_sum(edu_avail_cols, "edu_recursos_total")
    add_mean(edu_avail_cols, "edu_recursos_mean")

# -------------------------
# 5) Subconjunto final + limpieza
# -------------------------
final_cols = list(E.columns)
if target and target not in final_cols:
    final_cols.append(target)
E_final = E[final_cols].copy()

# Imputación final
num_cols_final = [c for c in E_final.columns if pd.api.types.is_numeric_dtype(E_final[c])]
cat_cols_final = [c for c in E_final.columns if c not in num_cols_final]
for c in num_cols_final:
    if E_final[c].isna().any():
        E_final[c] = E_final[c].fillna(E_final[c].median())
for c in cat_cols_final:
    E_final[c] = E_final[c].fillna("desconocido")

# -------------------------
# 6) Guardar y reporte
# -------------------------
OUT_PATH = DATA_PROCESSED / "education_dataset_plus.csv"
E_final.to_csv(OUT_PATH, index=False)

report_lines = [
    f"# ETL Educación Plus - {datetime.now():%Y-%m-%d %H:%M}",
    f"- Fuente: {'synthetic_education_dataset.csv' if RAW_SYNTH.exists() else (CLEAN_PATH.name if CLEAN_PATH.exists() else RAW_PATH.name)}",
    f"- Registros: {len(E_final):,}",
    f"- Columnas finales: {len(E_final.columns)}",
    f"- Target: {target}",
    f"- Nuevas características creadas: {len([c for c in E_final.columns if c not in df.columns])}",
    "## Ejemplos de nuevas columnas:",
]
nuevas = [c for c in E_final.columns if c not in df.columns]
report_lines += [f"  - {c}" for c in nuevas[:30]]

(DATA_INTERIM / "etl_plus_report.md").write_text("\n".join(report_lines), encoding="utf-8")

print("ETL Educación PLUS OK ✅")
print(f"Archivo: {OUT_PATH}")
print("Algunas características nuevas:")
for c in nuevas[:15]:
    print(" -", c)
