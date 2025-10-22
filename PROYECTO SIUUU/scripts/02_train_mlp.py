# scripts/02_train_mlp.py
# Entrenamiento robusto: Pipeline(Preproc) + GridSearchCV + Balanceo en Train + Métricas + Plots
import json
from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import warnings

from sklearn.model_selection import train_test_split, StratifiedKFold, GridSearchCV
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score, roc_curve,
    accuracy_score, f1_score
)
from sklearn.inspection import permutation_importance
from sklearn.utils import resample
import joblib

warnings.filterwarnings("ignore")

# --------------------------------------------------
# Rutas base
# --------------------------------------------------
BASE = Path(__file__).resolve().parents[1]
DATA_PROCESSED = BASE / "data" / "processed"
MODELS = BASE / "models"
PLOTS = BASE / "plots"

MODELS.mkdir(parents=True, exist_ok=True)
PLOTS.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------
# Carga de dataset EDU (generado por 01_etl_educacion.py)
# --------------------------------------------------
EDU_PATH = DATA_PROCESSED / "education_dataset.csv"
if not EDU_PATH.exists():
    raise FileNotFoundError(f"No existe {EDU_PATH}. Ejecuta primero scripts/01_etl_educacion.py")

EDU = pd.read_csv(EDU_PATH)

# --------------------------------------------------
# Selección de target
# --------------------------------------------------
target_candidates = ["acceso_a_internet"]
target = None
for t in target_candidates:
    if t in EDU.columns:
        target = t
        break
if target is None:
    # Fallback: buscar alguna binaria
    bin_cols = [c for c in EDU.columns if set(pd.Series(EDU[c]).dropna().unique()) <= {0, 1}]
    target = bin_cols[0] if bin_cols else None

if target is None:
    raise ValueError("No se encontró una columna target binaria para entrenar.")

# --------------------------------------------------
# Separación X/y
# --------------------------------------------------
X = EDU.drop(columns=[target])
y = EDU[target].astype(int)

# (Opcional) Feature Engineering seguro (si existen columnas)
# Agregamos columnas derivadas sin romper si faltan
def add_safe_ratio(df, num1, num2, out_name):
    if (num1 in df.columns) and (num2 in df.columns):
        df[out_name] = df[num1] / (df[num2].replace(0, np.nan) + 1)
        df[out_name] = df[out_name].replace([np.inf, -np.inf], np.nan).fillna(0)

# ejemplos comunes (ajusta a tus nombres si aplica)
add_safe_ratio(X, "computadores_funcionales", "poblacion", "ratio_comp_poblacion")
add_safe_ratio(X, "matriculas", "instituciones", "densidad_educativa")

# --------------------------------------------------
# Tipos de columnas
# --------------------------------------------------
X_num = [c for c in X.columns if pd.api.types.is_numeric_dtype(X[c])]
X_cat = [c for c in X.columns if c not in X_num]

# --------------------------------------------------
# Preprocesamiento
# --------------------------------------------------
pre = ColumnTransformer(
    transformers=[
        ("num", StandardScaler(), X_num),
        ("cat", OneHotEncoder(handle_unknown="ignore"), X_cat)
    ]
)

# --------------------------------------------------
# Split Train/Test (estratificado)
# --------------------------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)

print("Distribución original del target:")
print(y.value_counts())
print("\nDistribución en TRAIN antes de balanceo:")
print(y_train.value_counts())

# --------------------------------------------------
# Balanceo SOLO en Train (sobremuestreo de la clase minoritaria)
# --------------------------------------------------
train_df = pd.concat([X_train.reset_index(drop=True), y_train.reset_index(drop=True)], axis=1)
min_class = train_df[target].value_counts().idxmin()
maj_class = train_df[target].value_counts().idxmax()
df_min = train_df[train_df[target] == min_class]
df_maj = train_df[train_df[target] == maj_class]
df_min_up = resample(df_min, replace=True, n_samples=len(df_maj), random_state=42)
balanced_train = pd.concat([df_maj, df_min_up]).sample(frac=1.0, random_state=42).reset_index(drop=True)

X_train_bal = balanced_train.drop(columns=[target])
y_train_bal = balanced_train[target]

print("\nDistribución en TRAIN después de balanceo:")
print(y_train_bal.value_counts())
print()

# --------------------------------------------------
# Modelo base (MLP) + GridSearchCV en TRAIN balanceado
# --------------------------------------------------
mlp = MLPClassifier(max_iter=500, early_stopping=True, random_state=42)

# Ajusta el grid si quieres más velocidad (menos combinaciones)
param_grid = {
    "clf__hidden_layer_sizes": [(64, 32), (128, 64, 32), (100, 50), (64, 64, 32), (128, 64)],
    "clf__activation": ["relu", "tanh"],
    "clf__solver": ["adam", "lbfgs"],
    "clf__alpha": [0.0001, 0.001, 0.01],
    "clf__learning_rate_init": [0.001, 0.01],
}

pipe = Pipeline([("pre", pre), ("clf", mlp)])

cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
search = GridSearchCV(
    estimator=pipe,
    param_grid=param_grid,
    cv=cv,
    scoring="accuracy",   # puedes usar 'f1' si te importa más F1
    verbose=2,
    n_jobs=-1
)

print("Buscando la mejor configuración (GridSearchCV)...")
search.fit(X_train_bal, y_train_bal)
print("\nMejor configuración encontrada:")
print(search.best_params_)

# Usar el mejor estimador y entrenar en TODO el train balanceado
pipe_best = search.best_estimator_
pipe_best.fit(X_train_bal, y_train_bal)

# --------------------------------------------------
# Evaluación en TEST (sin tocar, sin balancear)
# --------------------------------------------------
y_pred = pipe_best.predict(X_test)
try:
    y_prob = pipe_best.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, y_prob)
except Exception:
    y_prob = None
    auc = np.nan

acc = accuracy_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred, average="binary")

print("\nMétricas en TEST")
print("================")
print(f"Accuracy: {acc:.3f}")
print(f"F1:       {f1:.3f}")
if not np.isnan(auc):
    print(f"ROC-AUC:  {auc:.3f}")

print("\nClassification Report:")
print(classification_report(y_test, y_pred, digits=3))

print("Matriz de confusión:")
print(confusion_matrix(y_test, y_pred))

# --------------------------------------------------
# Curva ROC (si hay probabilidades)
# --------------------------------------------------
if y_prob is not None:
    fpr, tpr, thr = roc_curve(y_test, y_prob)
    plt.figure()
    plt.plot(fpr, tpr, label=f"AUC={auc:.3f}")
    plt.plot([0, 1], [0, 1], linestyle="--")
    plt.xlabel("FPR")
    plt.ylabel("TPR")
    plt.title("Curva ROC - MLP (Educación)")
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(PLOTS / "roc_curve.png")
    plt.close()

# --------------------------------------------------
# Importancias por permutación (top 15)
# --------------------------------------------------
try:
    result = permutation_importance(
        pipe_best, X_test, y_test, n_repeats=5, random_state=42, n_jobs=1
    )
    importances = result.importances_mean

    # Obtener nombres de features transformados
    ohe = pipe_best.named_steps["pre"].named_transformers_["cat"]
    num_features = X_num
    if hasattr(ohe, "get_feature_names_out"):
        cat_features = list(ohe.get_feature_names_out(X_cat))
    else:
        cat_features = X_cat
    feature_names = num_features + cat_features

    top_idx = np.argsort(importances)[-15:][::-1]
    top_features = [feature_names[i] if i < len(feature_names) else f"f{i}" for i in top_idx]
    top_values = importances[top_idx]

    plt.figure()
    plt.barh(range(len(top_features)), top_values[::-1])
    plt.yticks(range(len(top_features)), top_features[::-1])
    plt.xlabel("Permutation importance")
    plt.title("Top 15 features (permutación)")
    plt.tight_layout()
    plt.savefig(PLOTS / "feature_importance.png", dpi=200)
    plt.close()
except Exception as e:
    print("Aviso: no se pudo calcular permutation_importance:", e)

# --------------------------------------------------
# Guardar modelo y metadatos
# --------------------------------------------------
PIPE_FILE = MODELS / "education_mlp_pipeline.joblib"
joblib.dump(pipe_best, PIPE_FILE)

META_FILE = MODELS / "model_meta.json"
META_FILE.write_text(json.dumps({
    "created_at": datetime.now().isoformat(),
    "target": target,
    "metrics": {
        "accuracy": float(acc),
        "f1": float(f1),
        "roc_auc": (None if np.isnan(auc) else float(auc))
    },
    "features_num": X_num,
    "features_cat": X_cat,
    "best_params": search.best_params_
}, indent=2), encoding="utf-8")

print(f"\nModelo guardado en: {PIPE_FILE}")
print(f"Metadatos: {META_FILE}")
print("Listo ✅")
