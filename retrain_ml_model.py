"""
Script para REENTRENAR el Modelo ML con Datos Nuevos
Mejora la precisión de las predicciones educativas
Usa scikit-learn MLP Classifier
"""

import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import warnings
import json

warnings.filterwarnings('ignore')

print("="*80)
print("🔄 REENTRENAMIENTO DEL MODELO ML (Fine-tuning)")
print("="*80)

# ==================== PASO 1: CARGAR DATOS ====================

print("\n📊 Paso 1: Cargando datos de entrenamiento...")

data_frames = []

# Intentar cargar datos originales
original_data_path = Path('PROYECTO SIUUU/data/original_education_data.csv')
if original_data_path.exists():
    try:
        df_original = pd.read_csv(original_data_path)
        data_frames.append(df_original)
        print(f"   ✓ Datos originales: {len(df_original)} registros")
    except Exception as e:
        print(f"   ⚠ No se pudo cargar datos originales: {str(e)}")

# Cargar datos nuevos (OBLIGATORIO)
new_data_path = Path('data/new_training_data.csv')
if new_data_path.exists():
    df_new = pd.read_csv(new_data_path)
    data_frames.append(df_new)
    print(f"   ✓ Datos nuevos: {len(df_new)} registros")
else:
    print(f"   ✗ ERROR: Datos nuevos no encontrados en {new_data_path}")
    print(f"   💡 Ejecuta primero: python collect_training_data.py")
    exit(1)

# Combinar todos los datos
if len(data_frames) == 0:
    print("   ✗ ERROR: No hay datos para entrenar!")
    exit(1)

df = pd.concat(data_frames, ignore_index=True)
print(f"   ✓ Total de registros combinados: {len(df)}")

# ==================== PASO 2: PREPARAR DATOS ====================

print("\n🔧 Paso 2: Preparando datos para el entrenamiento...")

# Definir features requeridas (DEBEN COINCIDIR con el modelo actual)
FEATURES = [
    'poblacion_total', 'porcentaje_rural', 'estrato_promedio', 'tasa_pobreza',
    'num_instituciones', 'computadores_por_estudiante', 'salones_por_institucion',
    'docentes_por_institucion', 'cobertura_electrica', 'cobertura_4g',
    'dispositivos_promedio_hogar', 'tasa_aprobacion', 'tasa_desercion',
    'puntaje_pruebas'
]

TARGET = 'tiene_internet'

# Verificar que tenemos todos los features
missing_features = [f for f in FEATURES if f not in df.columns]
if missing_features:
    print(f"   ✗ ERROR: Features faltantes: {missing_features}")
    exit(1)

print(f"   ✓ Todos los {len(FEATURES)} features presentes")

# Limpiar datos
df_clean = df[FEATURES + [TARGET]].dropna()
removed = len(df) - len(df_clean)
if removed > 0:
    print(f"   ✓ Registros con NaN removidos: {removed}")

# Verificar balanceo del target
target_counts = df_clean[TARGET].value_counts()
print(f"   ✓ Balance de clases:")
print(f"     - Con acceso (1): {target_counts.get(1, 0)} ({target_counts.get(1, 0)/len(df_clean)*100:.1f}%)")
print(f"     - Sin acceso (0): {target_counts.get(0, 0)} ({target_counts.get(0, 0)/len(df_clean)*100:.1f}%)")

# Preparar X y y
X = df_clean[FEATURES].values
y = df_clean[TARGET].values

print(f"   ✓ X shape: {X.shape}")
print(f"   ✓ y shape: {y.shape}")

# ==================== PASO 3: SPLIT TRAIN/TEST ====================

print("\n📈 Paso 3: Dividiendo datos en train/test...")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"   ✓ Training set: {len(X_train)} registros")
print(f"   ✓ Test set: {len(X_test)} registros")
print(f"   ✓ Ratio: 80/20")

# ==================== PASO 4: CREAR PIPELINE ====================

print("\n🏗️ Paso 4: Creando pipeline de ML...")

pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('mlp', MLPClassifier(
        hidden_layer_sizes=(128, 64, 32),  # 3 capas ocultas: 128, 64, 32 neuronas
        max_iter=1000,
        early_stopping=True,
        validation_fraction=0.1,
        n_iter_no_change=50,
        alpha=0.001,  # Regularización L2
        learning_rate_init=0.01,
        learning_rate='adaptive',
        random_state=42,
        verbose=0,
        warm_start=False
    ))
])

print("   ✓ Pipeline creado:")
print("     - Scaler: StandardScaler")
print("     - Model: MLPClassifier")
print("     - Capas ocultas: (128, 64, 32)")
print("     - Max iteraciones: 1000")

# ==================== PASO 5: ENTRENAR ====================

print("\n🚀 Paso 5: Entrenando modelo...")
print("   (Esto puede tardar 30-60 segundos)")
print("-" * 80)

pipeline.fit(X_train, y_train)

print("-" * 80)
print("   ✓ Entrenamiento completado")

# ==================== PASO 6: EVALUAR ====================

print("\n📊 Paso 6: Evaluando modelo...")

# Predicciones
y_pred_train = pipeline.predict(X_train)
y_pred_test = pipeline.predict(X_test)

# Probabilidades
y_pred_proba_train = pipeline.predict_proba(X_train)
y_pred_proba_test = pipeline.predict_proba(X_test)

# Calcular métricas
metrics_train = {
    'accuracy': accuracy_score(y_train, y_pred_train),
    'precision': precision_score(y_train, y_pred_train),
    'recall': recall_score(y_train, y_pred_train),
    'f1': f1_score(y_train, y_pred_train)
}

metrics_test = {
    'accuracy': accuracy_score(y_test, y_pred_test),
    'precision': precision_score(y_test, y_pred_test),
    'recall': recall_score(y_test, y_pred_test),
    'f1': f1_score(y_test, y_pred_test)
}

print(f"\n   📊 MÉTRICAS DE ENTRENAMIENTO:")
print(f"      Accuracy:  {metrics_train['accuracy']:.4f} ({metrics_train['accuracy']*100:.2f}%)")
print(f"      Precision: {metrics_train['precision']:.4f}")
print(f"      Recall:    {metrics_train['recall']:.4f}")
print(f"      F1-Score:  {metrics_train['f1']:.4f}")

print(f"\n   📊 MÉTRICAS DE PRUEBA (MÁS IMPORTANTE):")
print(f"      Accuracy:  {metrics_test['accuracy']:.4f} ({metrics_test['accuracy']*100:.2f}%)")
print(f"      Precision: {metrics_test['precision']:.4f}")
print(f"      Recall:    {metrics_test['recall']:.4f}")
print(f"      F1-Score:  {metrics_test['f1']:.4f}")

# Matriz de confusión
cm = confusion_matrix(y_test, y_pred_test)
print(f"\n   🎯 Matriz de Confusión (Test Set):")
print(f"      Verdaderos Negativos: {cm[0,0]}")
print(f"      Falsos Positivos: {cm[0,1]}")
print(f"      Falsos Negativos: {cm[1,0]}")
print(f"      Verdaderos Positivos: {cm[1,1]}")

# ==================== PASO 7: GUARDAR MODELO ====================

print("\n💾 Paso 7: Guardando modelo mejorado...")

models_dir = Path('PROYECTO SIUUU/models')
models_dir.mkdir(parents=True, exist_ok=True)

# Guardar pipeline
model_path = models_dir / 'education_mlp_pipeline.joblib'
joblib.dump(pipeline, model_path)
print(f"   ✓ Modelo guardado: {model_path}")

# Guardar metadata
metadata = {
    'training_date': str(pd.Timestamp.now()),
    'model_type': 'MLPClassifier',
    'architecture': '(128, 64, 32)',
    'total_records': len(df_clean),
    'train_records': len(X_train),
    'test_records': len(X_test),
    'features': FEATURES,
    'target': TARGET,
    'metrics': {
        'train': {k: float(v) for k, v in metrics_train.items()},
        'test': {k: float(v) for k, v in metrics_test.items()}
    },
    'confusion_matrix': {
        'tn': int(cm[0,0]),
        'fp': int(cm[0,1]),
        'fn': int(cm[1,0]),
        'tp': int(cm[1,1])
    }
}

metadata_path = models_dir / 'model_metadata.json'
with open(metadata_path, 'w', encoding='utf-8') as f:
    json.dump(metadata, f, indent=2)

print(f"   ✓ Metadata guardada: {metadata_path}")

# ==================== PASO 8: CONCLUSIÓN ====================

print("\n" + "="*80)
print("✅ REENTRENAMIENTO COMPLETADO EXITOSAMENTE")
print("="*80)

print(f"\n📊 Resumen Final:")
print(f"   • Registros totales: {len(df_clean)}")
print(f"   • Accuracy en Test Set: {metrics_test['accuracy']*100:.2f}%")
print(f"   • F1-Score: {metrics_test['f1']:.4f}")
print(f"   • Modelo guardado: {model_path}")
print(f"   • Metadata guardada: {metadata_path}")

print(f"\n🎯 Mejoras:")
if metrics_test['accuracy'] >= 0.85:
    print(f"   ✓ Excelente precisión (>= 85%)")
elif metrics_test['accuracy'] >= 0.80:
    print(f"   ✓ Buena precisión (>= 80%)")
elif metrics_test['accuracy'] >= 0.75:
    print(f"   ✓ Precisión aceptable (>= 75%)")
else:
    print(f"   ⚠ Precisión baja. Considera más datos.")

print(f"\n💡 Próximos pasos:")
print(f"   1. Reinicia el servidor Flask")
print(f"      python app.py")
print(f"   2. El nuevo modelo se cargará automáticamente")
print(f"   3. Prueba las predicciones")
print(f"      python test_api_simple.py")

print("="*80 + "\n")
