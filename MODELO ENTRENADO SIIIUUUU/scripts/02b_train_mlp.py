# scripts/02_train_mlp.py
# Entrenamiento robusto: Pipeline(Preproc) + GridSearchCV + Balanceo en Train + Métricas + Plots + Anti-Leak Guards
import json
from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import warnings

from sklearn.model_selection import (
    train_test_split, StratifiedKFold, GridSearchCV, cross_val_score
)
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
from sklearn.ensemble import RandomForestClassifier  # Baseline opcional
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
# Carga de dataset EDU (prioridad: NO-LEAK -> PLUS -> BASE)
# --------------------------------------------------
plus_noleak = DATA_PROCESSED / "education_dataset_plus_noleak.csv"
plus_path   = DATA_PROCESSED / "education_dataset_plus.csv"
base_path   = DATA_PROCESSED / "education_dataset.csv"

if plus_noleak.exists():
    EDU_PATH = plus_noleak
    print("Usando dataset enriquecido NO-LEAK: education_dataset_plus_noleak.csv")
elif plus_path.exists():
    EDU_PATH = plus_path
    print("Usando dataset enriquecido: education_dataset_plus.csv")
elif base_path.exists():
    EDU_PATH = base_path
    print("⚠️ Usando el dataset base: education_dataset.csv")
else:
    raise FileNotFoundError(
        "No encontré ningún dataset procesado. Ejecuta:\n"
        " - scripts/01c_etl_educacion_noleak.py (recomendado)\n"
        "   o\n"
        " - scripts/01b_etl_educacion_plus.py / scripts/01_etl_educacion.py"
    )

EDU = pd.read_csv(EDU_PATH)

# Info del dataset realmente cargado
print(f"\n[INFO] Entrenando con: {EDU_PATH}")
print("[INFO] Shape:", EDU.shape)
print("[INFO] Columnas (primeras 30):", list(EDU.columns)[:30])

if "acceso_a_internet" not in EDU.columns:
    raise ValueError("El dataset no trae la columna 'acceso_a_internet' como target.")

print("[INFO] Distribución target:")
print(EDU['acceso_a_internet'].value_counts(normalize=True).round(3))

# --------------------------------------------------
# Guardia anti-fuga por NOMBRE antes del split
# --------------------------------------------------
hard_suspect_keys = ["internet","conect","tic","idx_tic","wifi","banda","ancho","fibra","4g"]
suspect_cols_hard = [c for c in EDU.columns
                     if any(k in c.lower() for k in hard_suspect_keys)
                     and c != "acceso_a_internet"]
if suspect_cols_hard:
    print("\n[TRAIN-GUARD] Eliminando columnas sospechosas en entrenamiento:", suspect_cols_hard)
    EDU = EDU.drop(columns=suspect_cols_hard)

# --------------------------------------------------
# Selección de target
# --------------------------------------------------
target = "acceso_a_internet"

# --------------------------------------------------
# Separación X/y
# --------------------------------------------------
X = EDU.drop(columns=[target])
y = EDU[target].astype(int)

# (Opcional) Feature Engineering seguro (si existen columnas)
def add_safe_ratio(df, num1, num2, out_name):
    if (num1 in df.columns) and (num2 in df.columns):
        df[out_name] = df[num1] / (df[num2].replace(0, np.nan) + 1)
        df[out_name] = df[out_name].replace([np.inf, -np.inf], np.nan).fillna(0)

# Ejemplos comunes (ajusta a tus nombres si aplica)
add_safe_ratio(X, "computadores_funcionales", "poblacion", "ratio_comp_poblacion")
add_safe_ratio(X, "matriculas", "instituciones", "densidad_educativa")

# --------------------------------------------------
# Señal: correlaciones con el target (solo numéricas)
# --------------------------------------------------
num_cols_corr = EDU.select_dtypes(include=np.number).columns
if target in num_cols_corr:
    corr_target = EDU[num_cols_corr].corr(numeric_only=True)[target].sort_values(ascending=False)
    print("\n[INFO] Top correlaciones con el target:")
    print(corr_target.head(10).round(3))
    print("\n[INFO] Peores correlaciones con el target:")
    print(corr_target.tail(10).round(3))
else:
    print("\n[INFO] No es posible imprimir correlaciones numéricas con el target (target no numérico en corr).")

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

print("\nDistribución original del target (global):")
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

param_grid = {
    "clf__hidden_layer_sizes": [(64, 32), (128, 64, 32), (100, 50), (64, 64, 32), (128, 64)],
    "clf__activation": ["relu", "tanh"],
    "clf__solver": ["adam", "lbfgs"],
    "clf__alpha": [0.0001, 0.001, 0.01],
    "clf__learning_rate_init": [0.001, 0.01],
}

pipe = Pipeline([("pre", pre), ("clf", mlp)])

cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
print("Buscando la mejor configuración (GridSearchCV)...")
search = GridSearchCV(
    estimator=pipe,
    param_grid=param_grid,
    cv=cv,
    scoring="accuracy",   # usa 'f1' si te interesa más el F1
    verbose=2,
    n_jobs=-1
)
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
# VALIDACIONES EXTRA (Overfitting / Fuga de info)
# --------------------------------------------------

# ===== VALIDACIÓN 1: Cross-Validation (5 folds) sobre todo el dataset =====
cv5 = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
scores_acc = cross_val_score(pipe_best, X, y, cv=cv5, scoring="accuracy", n_jobs=-1)
scores_f1  = cross_val_score(pipe_best, X, y, cv=cv5, scoring="f1", n_jobs=-1)

print("\n[VALIDACIÓN 1] CV=5 (accuracy):", np.round(scores_acc, 4),
      "→ mean:", scores_acc.mean().round(4), "±", scores_acc.std().round(4))
print("[VALIDACIÓN 1] CV=5 (f1):      ", np.round(scores_f1,  4),
      "→ mean:", scores_f1.mean().round(4), "±", scores_f1.std().round(4))

# ===== VALIDACIÓN 2: Ablation test (quitar columnas sospechosas por nombre) =====
suspect_keys = ["internet", "conect", "tic", "idx_tic", "wifi", "banda", "ancho", "fibra", "4g"]
suspect_cols = [c for c in X.columns if any(k in c.lower() for k in suspect_keys)]
print("\n[VALIDACIÓN 2] Columnas sospechosas de filtrar:",
      suspect_cols if suspect_cols else "(ninguna)")

if suspect_cols:
    # 1) Dataset reducido
    X_red = X.drop(columns=suspect_cols)

    # Rehacer tipos
    X_num_red = [c for c in X_red.columns if pd.api.types.is_numeric_dtype(X_red[c])]
    X_cat_red = [c for c in X_red.columns if c not in X_num_red]

    pre_red = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), X_num_red),
            ("cat", OneHotEncoder(handle_unknown="ignore"), X_cat_red)
        ]
    )

    # 2) Reconstruir el MLP con los mejores hiperparámetros del grid
    best = search.best_params_
    mlp_red = MLPClassifier(
        max_iter=500, early_stopping=True, random_state=42,
        activation=best["clf__activation"],
        alpha=best["clf__alpha"],
        learning_rate_init=best["clf__learning_rate_init"],
        solver=best["clf__solver"],
        hidden_layer_sizes=best["clf__hidden_layer_sizes"]
    )
    pipe_red = Pipeline([("pre", pre_red), ("clf", mlp_red)])

    # 3) Split idéntico (misma semilla) y balanceo SOLO en train
    X_train_r, X_test_r, y_train_r, y_test_r = train_test_split(
        X_red, y, test_size=0.20, random_state=42, stratify=y
    )
    train_df_r = pd.concat([X_train_r.reset_index(drop=True), y_train_r.reset_index(drop=True)], axis=1)
    min_class_r = train_df_r[target].value_counts().idxmin()
    maj_class_r = train_df_r[target].value_counts().idxmax()
    df_min_r = train_df_r[train_df_r[target] == min_class_r]
    df_maj_r = train_df_r[train_df_r[target] == maj_class_r]
    df_min_up_r = resample(df_min_r, replace=True, n_samples=len(df_maj_r), random_state=42)
    balanced_train_r = pd.concat([df_maj_r, df_min_up_r]).sample(frac=1.0, random_state=42).reset_index(drop=True)
    X_train_bal_r = balanced_train_r.drop(columns=[target])
    y_train_bal_r = balanced_train_r[target]

    # 4) Entrenar y evaluar
    pipe_red.fit(X_train_bal_r, y_train_bal_r)
    y_pred_r = pipe_red.predict(X_test_r)
    try:
        y_prob_r = pipe_red.predict_proba(X_test_r)[:, 1]
        auc_r = roc_auc_score(y_test_r, y_prob_r)
    except Exception:
        y_prob_r = None
        auc_r = np.nan

    acc_r = accuracy_score(y_test_r, y_pred_r)
    f1_r = f1_score(y_test_r, y_pred_r, average="binary")

    print("[VALIDACIÓN 2] TEST sin columnas sospechosas -> "
          f"Accuracy: {round(acc_r,3)}  F1: {round(f1_r,3)}  AUC: {(None if np.isnan(auc_r) else round(auc_r,3))}")
else:
    print("[VALIDACIÓN 2] Sin columnas sospechosas. Prueba omitida.")

# ===== VALIDACIÓN 3: Sanity check con etiquetas barajadas (barajar SOLO y) =====
y_shuf = y.sample(frac=1.0, random_state=123).reset_index(drop=True)  # SOLO y
X_fix  = X.reset_index(drop=True)                                     # X sin barajar
scores_acc_shuf = cross_val_score(pipe_best, X_fix, y_shuf, cv=5, scoring="accuracy", n_jobs=-1)
print("\n[VALIDACIÓN 3] CV con etiquetas barajadas (accuracy):",
      np.round(scores_acc_shuf, 4), "→ mean:", scores_acc_shuf.mean().round(4))

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
# (Opcional) Baseline RandomForest para comparar
# --------------------------------------------------
try:
    rf = Pipeline([
        ("pre", pre),
        ("clf", RandomForestClassifier(
            n_estimators=300, max_depth=None, random_state=42, n_jobs=-1, class_weight=None
        ))
    ])
    rf.fit(X_train_bal, y_train_bal)
    rf_pred = rf.predict(X_test)
    rf_prob = None
    try:
        rf_prob = rf.predict_proba(X_test)[:, 1]
        rf_auc = roc_auc_score(y_test, rf_prob)
    except Exception:
        rf_auc = np.nan
    rf_acc = accuracy_score(y_test, rf_pred)
    rf_f1  = f1_score(y_test, rf_pred, average="binary")
    print("\n[BASELINE RF] TEST → Accuracy:", round(rf_acc,3),
          "F1:", round(rf_f1,3),
          "AUC:", (None if np.isnan(rf_auc) else round(rf_auc,3)))
except Exception as e:
    print("[BASELINE RF] Omitido por error:", e)

# --------------------------------------------------
# Guardar modelo y metadatos
# --------------------------------------------------
PIPE_FILE = MODELS / "education_mlp_pipeline.joblib"
joblib.dump(pipe_best, PIPE_FILE)

META_FILE = MODELS / "model_meta.json"
META_FILE.write_text(json.dumps({
    "created_at": datetime.now().isoformat(),
    "dataset_path": str(EDU_PATH),
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
