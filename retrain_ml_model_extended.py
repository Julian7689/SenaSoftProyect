"""
Script MEJORADO para reentrenar el modelo ML con más datos
Usa los 100 registros para mejor precisión
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

warnings.filterwarnings('ignore')

print("=" * 80)
print("🔄 REENTRENAMIENTO MEJORADO DEL MODELO ML (con 100 registros)")
print("=" * 80)

# ==================== PASO 1: CARGAR DATOS ====================

print("\n📊 Paso 1: Cargando datos extendidos...")

new_data_path = Path('data/new_training_data_extended.csv')

if not new_data_path.exists():
    print(f"   ⚠ Archivo no encontrado: {new_data_path}")
    print(f"   💡 Ejecuta primero: python collect_training_data_extended.py")
    exit(1)

df = pd.read_csv(new_data_path)
print(f"   ✓ Datos cargados: {len(df)} registros")

# ==================== PASO 2: PREPARAR DATOS ====================

print("\n🔧 Paso 2: Preparando datos...")

FEATURES = [
    'poblacion_total', 'porcentaje_rural', 'estrato_promedio', 'tasa_pobreza',
    'num_instituciones', 'computadores_por_estudiante', 'salones_por_institucion',
    'docentes_por_institucion', 'cobertura_electrica', 'cobertura_4g',
    'dispositivos_promedio_hogar', 'tasa_aprobacion', 'tasa_desercion',
    'puntaje_pruebas'
]

TARGET = 'tiene_internet'

# Verificar features
missing_features = [f for f in FEATURES if f not in df.columns]
if missing_features:
    print(f"   ✗ Features faltantes: {missing_features}")
    exit(1)

# Limpiar datos
df = df[FEATURES + [TARGET]].dropna()
print(f"   ✓ Datos limpios: {len(df)} registros")

# Separar X y y
X = df[FEATURES].values
y = df[TARGET].values

# Split train/test (80/20)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"   ✓ Train: {len(X_train)} registros ({len(X_train)/len(df)*100:.1f}%)")
print(f"   ✓ Test: {len(X_test)} registros ({len(X_test)/len(df)*100:.1f}%)")
print(f"   ✓ Balance clase 0: {(y==0).sum()} ({(y==0).sum()/len(y)*100:.1f}%)")
print(f"   ✓ Balance clase 1: {(y==1).sum()} ({(y==1).sum()/len(y)*100:.1f}%)")

# ==================== PASO 3: CREAR PIPELINE ====================

print("\n🏗️ Paso 3: Creando pipeline mejorado...")

pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('mlp', MLPClassifier(
        hidden_layer_sizes=(256, 128, 64, 32),  # 4 capas (MEJORADO)
        max_iter=2000,  # Más iteraciones
        early_stopping=True,
        validation_fraction=0.1,
        n_iter_no_change=100,  # Más paciencia
        alpha=0.0001,  # Regularización
        learning_rate_init=0.001,
        random_state=42,
        verbose=0
    ))
])

print("   ✓ Pipeline creado:")
print("     - Scaler: StandardScaler")
print("     - MLP: 4 capas (256, 128, 64, 32)")
print("     - Max iteraciones: 2000")
print("     - Early stopping: Activado")

# ==================== PASO 4: ENTRENAR ====================

print("\n🚀 Paso 4: Entrenando modelo (puede tardar 1-2 minutos)...")
print("   ", end="", flush=True)

pipeline.fit(X_train, y_train)

print("\n   ✓ Entrenamiento completado")

# ==================== PASO 5: EVALUAR ====================

print("\n📈 Paso 5: Evaluando modelo...")

y_pred_train = pipeline.predict(X_train)
y_pred_test = pipeline.predict(X_test)

metrics_train = {
    'accuracy': accuracy_score(y_train, y_pred_train),
    'precision': precision_score(y_train, y_pred_train, zero_division=0),
    'recall': recall_score(y_train, y_pred_train, zero_division=0),
    'f1': f1_score(y_train, y_pred_train, zero_division=0)
}

metrics_test = {
    'accuracy': accuracy_score(y_test, y_pred_test),
    'precision': precision_score(y_test, y_pred_test, zero_division=0),
    'recall': recall_score(y_test, y_pred_test, zero_division=0),
    'f1': f1_score(y_test, y_pred_test, zero_division=0)
}

print(f"\n   📊 MÉTRICAS DE ENTRENAMIENTO:")
print(f"      • Accuracy:  {metrics_train['accuracy']:.4f} ({metrics_train['accuracy']*100:.2f}%)")
print(f"      • Precision: {metrics_train['precision']:.4f}")
print(f"      • Recall:    {metrics_train['recall']:.4f}")
print(f"      • F1-Score:  {metrics_train['f1']:.4f}")

print(f"\n   📊 MÉTRICAS DE PRUEBA (MÁS IMPORTANTE):")
print(f"      • Accuracy:  {metrics_test['accuracy']:.4f} ({metrics_test['accuracy']*100:.2f}%)")
print(f"      • Precision: {metrics_test['precision']:.4f}")
print(f"      • Recall:    {metrics_test['recall']:.4f}")
print(f"      • F1-Score:  {metrics_test['f1']:.4f}")

# Matriz de confusión
tn, fp, fn, tp = confusion_matrix(y_test, y_pred_test).ravel()
print(f"\n   🔍 Matriz de Confusión (Test Set):")
print(f"      • Verdaderos Negativos: {tn}")
print(f"      • Falsos Positivos: {fp}")
print(f"      • Falsos Negativos: {fn}")
print(f"      • Verdaderos Positivos: {tp}")

# ==================== PASO 6: GUARDAR MODELO ====================

print("\n💾 Paso 6: Guardando modelo mejorado...")

models_dir = Path('PROYECTO SIUUU/models')
models_dir.mkdir(parents=True, exist_ok=True)

# Guardar pipeline
model_path = models_dir / 'education_mlp_pipeline.joblib'
joblib.dump(pipeline, model_path)
print(f"   ✓ Modelo guardado: {model_path}")

# Guardar metadata
import json
from datetime import datetime

metadata = {
    'training_date': str(datetime.now()),
    'version': '2.0',
    'total_records': len(df),
    'train_records': len(X_train),
    'test_records': len(X_test),
    'features': FEATURES,
    'features_count': len(FEATURES),
    'architecture': {
        'scaler': 'StandardScaler',
        'model': 'MLPClassifier',
        'hidden_layers': [256, 128, 64, 32],
        'max_iterations': 2000,
        'early_stopping': True
    },
    'metrics': {
        'train': {k: float(v) for k, v in metrics_train.items()},
        'test': {k: float(v) for k, v in metrics_test.items()},
        'confusion_matrix': {
            'TN': int(tn),
            'FP': int(fp),
            'FN': int(fn),
            'TP': int(tp)
        }
    }
}

metadata_path = models_dir / 'model_metadata.json'
with open(metadata_path, 'w') as f:
    json.dump(metadata, f, indent=2, default=str)

print(f"   ✓ Metadata guardada: {metadata_path}")

# ==================== CONCLUSIÓN ====================

print("\n" + "=" * 80)
print("✅ REENTRENAMIENTO COMPLETADO EXITOSAMENTE")
print("=" * 80)

print(f"\n📊 Resumen Final:")
print(f"   • Registros totales: {len(df)}")
print(f"   • Accuracy en Training: {metrics_train['accuracy']*100:.2f}%")
print(f"   • Accuracy en Test: {metrics_test['accuracy']*100:.2f}%")
print(f"   • F1-Score: {metrics_test['f1']:.4f}")
print(f"   • Modelo guardado: {model_path}")
print(f"   • Metadata guardada: {metadata_path}")

if metrics_test['accuracy'] >= 0.80:
    print(f"\n🎉 EXCELENTE: El modelo está listo para producción")
elif metrics_test['accuracy'] >= 0.75:
    print(f"\n👍 BUENO: El modelo funciona correctamente")
else:
    print(f"\n⚠ AVISO: Considera agregar más datos para mejor precisión")

print(f"\n💡 Próximos pasos:")
print(f"   1. Reinicia el servidor Flask:")
print(f"      python app.py")
print(f"\n   2. El nuevo modelo se cargará automáticamente")
print(f"\n   3. Prueba el chatbot:")
print(f"      http://localhost:5000")
print(f"\n   4. Verifica las predicciones (deberían ser más precisas)")

print("=" * 80 + "\n")
