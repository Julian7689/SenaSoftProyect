

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

print("=" * 80)
print("📊 RECOPILACIÓN DE DATOS DE ENTRENAMIENTO")
print("=" * 80)


print("\n1️⃣ Generando datos de regiones colombianas...")


new_training_data = {
    'region': [
        'Atlantico', 'Cordoba', 'Magdalena', 'Bolivar', 'Sucre',
        'Cesar', 'La Guajira', 'Cundinamarca', 'Tolima', 'Huila',
        'Cauca', 'Nariño', 'Meta', 'Arauca', 'Norte Santander'
    ],
    
    'poblacion_total': [
        2500000, 1800000, 1300000, 2100000, 900000,
        1400000, 1000000, 3500000, 1500000, 1200000,
        1600000, 1800000, 1100000, 300000, 1500000
    ],
    
    'porcentaje_rural': [
        25.3, 45.2, 60.1, 35.8, 52.0,
        40.5, 70.2, 30.1, 48.3, 55.0,
        65.2, 58.5, 42.0, 68.5, 52.3
    ],
    
    'estrato_promedio': [
        2.8, 2.2, 2.1, 2.5, 2.3,
        2.4, 2.0, 3.2, 2.6, 2.4,
        2.1, 2.2, 2.7, 2.1, 2.5
    ],
    
    'tasa_pobreza': [
        35.2, 48.5, 55.3, 40.1, 50.2,
        45.3, 60.2, 28.5, 42.1, 48.5,
        52.3, 50.1, 38.5, 55.2, 45.8
    ],
    
    'num_instituciones': [
        450, 320, 210, 380, 180,
        250, 180, 550, 280, 220,
        300, 320, 200, 80, 250
    ],
    
    'computadores_por_estudiante': [
        0.45, 0.28, 0.15, 0.35, 0.20,
        0.25, 0.12, 0.65, 0.30, 0.22,
        0.18, 0.20, 0.40, 0.10, 0.28
    ],
    
    'salones_por_institucion': [
        12.5, 10.2, 8.5, 11.0, 9.3,
        10.5, 7.8, 14.2, 11.5, 10.0,
        9.2, 10.1, 12.0, 6.5, 10.8
    ],
    
    'docentes_por_institucion': [
        35.2, 28.5, 22.1, 30.5, 25.3,
        27.5, 20.3, 40.2, 32.1, 28.5,
        24.5, 26.3, 34.0, 18.5, 29.2
    ],
    
    'cobertura_electrica': [
        95.2, 82.3, 65.1, 78.5, 72.0,
        80.5, 55.2, 98.5, 85.3, 75.8,
        68.2, 72.5, 88.0, 45.2, 82.3
    ],
    
    'cobertura_4g': [
        78.5, 52.3, 35.2, 65.0, 48.5,
        55.2, 25.3, 88.5, 62.3, 45.2,
        38.5, 42.0, 72.5, 20.1, 58.3
    ],
    
    'dispositivos_promedio_hogar': [
        1.8, 1.2, 0.8, 1.5, 1.0,
        1.3, 0.7, 2.2, 1.5, 1.2,
        0.9, 1.1, 1.7, 0.6, 1.4
    ],
    
    'tasa_aprobacion': [
        72.3, 65.2, 55.8, 68.5, 60.2,
        64.5, 52.3, 78.5, 70.2, 63.5,
        58.2, 61.0, 75.0, 50.1, 66.3
    ],
    
    'tasa_desercion': [
        12.5, 22.3, 35.2, 18.5, 28.5,
        24.3, 38.5, 8.2, 15.3, 22.5,
        28.3, 25.2, 10.5, 35.2, 20.1
    ],
    
    'puntaje_pruebas': [
        380.5, 320.2, 250.1, 355.0, 290.5,
        315.2, 245.8, 420.5, 375.2, 305.1,
        265.3, 285.5, 395.0, 235.2, 325.8
    ],
    
    # TARGET: 1 = Con acceso a internet, 0 = Sin acceso adecuado
    'tiene_internet': [
        1, 0, 0, 1, 0,
        1, 0, 1, 1, 0,
        0, 0, 1, 0, 1
    ]
}

# Crear DataFrame
df = pd.DataFrame(new_training_data)

print(f"\n✓ Datos generados: {len(df)} regiones")
print(f"✓ Features: {len(df.columns)-1} indicadores educativos")
print(f"✓ Target (tiene_internet): Balanceado {sum(df['tiene_internet'])} con acceso, {len(df)-sum(df['tiene_internet'])} sin acceso")

# ==================== PASO 2: CREAR DIRECTORIO ====================

print("\n2️⃣ Creando directorio de datos...")

data_dir = Path('data')
data_dir.mkdir(parents=True, exist_ok=True)

print(f"✓ Directorio creado: {data_dir}")

# ==================== PASO 3: GUARDAR DATOS ====================

print("\n3️⃣ Guardando datos...")

output_path = data_dir / 'new_training_data.csv'
df.to_csv(output_path, index=False, encoding='utf-8')

print(f"✓ Datos guardados en: {output_path}")

# ==================== PASO 4: MOSTRAR ESTADÍSTICAS ====================

print("\n4️⃣ Estadísticas de los datos:")
print("\n" + "="*80)
print(df.to_string(index=False))
print("="*80)

# ==================== PASO 5: RESUMEN ====================

print("\n" + "="*80)
print("✅ RECOPILACIÓN DE DATOS COMPLETADA")
print("="*80)

print(f"\n📊 Resumen:")
print(f"   • Total de registros: {len(df)}")
print(f"   • Regiones colombianas: {df['region'].nunique()}")
print(f"   • Con acceso a internet: {sum(df['tiene_internet'])} ({sum(df['tiene_internet'])/len(df)*100:.1f}%)")
print(f"   • Sin acceso adecuado: {len(df)-sum(df['tiene_internet'])} ({(len(df)-sum(df['tiene_internet']))/len(df)*100:.1f}%)")
print(f"   • Archivo: {output_path}")

print(f"\n💡 Próximo paso:")
print(f"   python retrain_ml_model.py")

print("="*80 + "\n")
