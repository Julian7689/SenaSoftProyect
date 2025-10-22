# 🤖 GUÍA DE INTEGRACIÓN ML CON FLASK - CHATBOT BOTI

## ✅ ESTADO DE LA INTEGRACIÓN

La integración del modelo de Machine Learning `education_mlp_pipeline.joblib` con la aplicación Flask ha sido completada exitosamente.

---

## 📦 CAMBIOS REALIZADOS

### 1️⃣ **Backend Flask (`app.py`)**

#### Nuevas Importaciones:
```python
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
```

#### Funciones Agregadas:
- **`load_ml_model()`** - Carga el modelo UNA SOLA VEZ al iniciar la aplicación
  - Ruta: `PROYECTO SIUUU/models/education_mlp_pipeline.joblib`
  - Define los 14 features esperados en el orden correcto
  - Maneja errores si el archivo no existe

#### Endpoints Nuevos:

##### ✅ `POST /api/predict`
Realiza predicción individual sobre acceso a internet.

**Request JSON:**
```json
{
    "poblacion_total": 16295,
    "porcentaje_rural": 8.66,
    "estrato_promedio": 2.54,
    "tasa_pobreza": 54.49,
    "num_instituciones": 59,
    "computadores_por_estudiante": 1.34,
    "salones_por_institucion": 24,
    "docentes_por_institucion": 78,
    "cobertura_electrica": 89.94,
    "cobertura_4g": 42.64,
    "dispositivos_promedio_hogar": 1.96,
    "tasa_aprobacion": 62.50,
    "tasa_desercion": 36.06,
    "puntaje_pruebas": 354.19
}
```

**Response JSON (éxito):**
```json
{
    "success": true,
    "prediction": 0,
    "prediction_proba": [0.85, 0.15],
    "interpretation": "🔴 Sin acceso a internet - Se requieren recursos de conectividad",
    "timestamp": "2025-10-22T14:30:00.123456"
}
```

**Response JSON (error):**
```json
{
    "success": false,
    "error": "Features faltantes: feature1, feature2",
    "required_features": [...]
}
```

##### ✅ `POST /api/predict-batch`
Realiza predicciones en lote para múltiples registros.

**Request JSON:**
```json
{
    "records": [
        { "poblacion_total": 16295, ... },
        { "poblacion_total": 20000, ... }
    ]
}
```

**Response JSON:**
```json
{
    "success": true,
    "total_records": 2,
    "predictions": [
        {"record_id": 0, "prediction": 0},
        {"record_id": 1, "prediction": 1}
    ],
    "timestamp": "2025-10-22T14:30:00.123456"
}
```

---

### 2️⃣ **Frontend JavaScript (`ml-predictor.js`)**

Nuevo archivo: `static/js/ml-predictor.js`

#### Funciones Principales Expuestas:
```javascript
window.mlPredictor.makePrediction()      // Ejecuta predicción
window.mlPredictor.clearForm()           // Limpia formulario
window.mlPredictor.exportResult()        // Descarga resultado JSON
window.mlPredictor.loadExampleData()     // Carga datos de ejemplo
```

#### Features:
- ✓ Validación de campos en cliente
- ✓ Manejo de errores con alertas
- ✓ Visualización de probabilidades
- ✓ Exportación de resultados
- ✓ Carga de datos de ejemplo
- ✓ Tooltips explicativos
- ✓ Animaciones suaves
- ✓ Responsive design

---

### 3️⃣ **Frontend HTML (`templates/admin.html`)**

#### Nueva Sección:
```html
<div class="ml-prediction-section">
    <!-- Formulario con 14 campos de entrada -->
    <!-- Botones de acción -->
    <!-- Área de resultados -->
</div>
```

#### Campos del Formulario:
1. Población Total
2. Porcentaje Rural (%)
3. Estrato Promedio
4. Tasa de Pobreza (%)
5. Número de Instituciones
6. Computadores por Estudiante
7. Salones por Institución
8. Docentes por Institución
9. Cobertura Eléctrica (%)
10. Cobertura 4G (%)
11. Dispositivos por Hogar (Promedio)
12. Tasa de Aprobación (%)
13. Tasa de Deserción (%)
14. Puntaje de Pruebas

#### Estilos Nuevos (CSS):
- `.ml-prediction-section` - Contenedor principal
- `.ml-form` - Grid de formulario responsivo
- `.ml-input` - Campos de entrada estilizados
- `.result-container` - Contenedor de resultados
- `.probability-bars` - Visualización de probabilidades
- Animaciones: `fadeInUp`, `slideInUp`, `slideInDown`, `spin`

---

### 4️⃣ **Dependencias (`requirements.txt`)**

Agregada:
```
joblib>=1.3.0
```

---

## 🚀 CÓMO USAR

### Iniciando la Aplicación

1. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

2. **Ejecutar la aplicación:**
```bash
python app.py
```

Deberías ver en los logs:
```
============================================================
INICIALIZANDO APLICACIÓN
============================================================
✓ Modelo ML cargado correctamente desde PROYECTO SIUUU/models/education_mlp_pipeline.joblib
✓ Modelo espera 14 features
Iniciando servidor en http://0.0.0.0:5000
============================================================
```

### Accediendo a la Interfaz

1. Abre el navegador: `http://localhost:5000/admin`
2. Deberías ver (requiere autenticación simulada):
   - Dashboard con casos y alarmas (secciones existentes)
   - **Nueva Sección: "Predicción con Machine Learning"**

### Realizando Predicciones

**Opción 1: Interfaz Web**
1. Navega a la sección "🤖 Predicción con Machine Learning"
2. Haz clic en "📋 Cargar Ejemplo" para llenar datos de prueba
3. Haz clic en "🚀 Hacer Predicción"
4. Observa el resultado con interpretación y probabilidades

**Opción 2: API REST**
```bash
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "poblacion_total": 16295,
    "porcentaje_rural": 8.66,
    "estrato_promedio": 2.54,
    "tasa_pobreza": 54.49,
    "num_instituciones": 59,
    "computadores_por_estudiante": 1.34,
    "salones_por_institucion": 24,
    "docentes_por_institucion": 78,
    "cobertura_electrica": 89.94,
    "cobertura_4g": 42.64,
    "dispositivos_promedio_hogar": 1.96,
    "tasa_aprobacion": 62.50,
    "tasa_desercion": 36.06,
    "puntaje_pruebas": 354.19
  }'
```

---

## 🧪 PRUEBAS

### Test 1: Predicción Exitosa
```python
import requests

data = {
    "poblacion_total": 16295,
    "porcentaje_rural": 8.66,
    "estrato_promedio": 2.54,
    "tasa_pobreza": 54.49,
    "num_instituciones": 59,
    "computadores_por_estudiante": 1.34,
    "salones_por_institucion": 24,
    "docentes_por_institucion": 78,
    "cobertura_electrica": 89.94,
    "cobertura_4g": 42.64,
    "dispositivos_promedio_hogar": 1.96,
    "tasa_aprobacion": 62.50,
    "tasa_desercion": 36.06,
    "puntaje_pruebas": 354.19
}

response = requests.post('http://localhost:5000/api/predict', json=data)
print(response.json())
# Expected: {"success": true, "prediction": 0 o 1, ...}
```

### Test 2: Validación de Features Faltantes
```python
data = {"poblacion_total": 16295}  # Faltan features
response = requests.post('http://localhost:5000/api/predict', json=data)
print(response.json())
# Expected: {"success": false, "error": "Features faltantes: ..."}
```

### Test 3: Predicción en Lote
```python
data = {
    "records": [
        {
            "poblacion_total": 16295, "porcentaje_rural": 8.66,
            ... (todos los 14 features)
        },
        {
            "poblacion_total": 20000, "porcentaje_rural": 10.0,
            ... (todos los 14 features)
        }
    ]
}

response = requests.post('http://localhost:5000/api/predict-batch', json=data)
print(response.json())
# Expected: {"success": true, "predictions": [...]}
```

---

## 📊 CARACTERÍSTICAS DEL MODELO

El modelo `education_mlp_pipeline.joblib` es un **MLP (Multi-Layer Perceptron) entrenado con:**

- **Target:** `acceso_a_internet` (binario: 0 = No, 1 = Sí)
- **Features:** 14 indicadores educativos y sociodemográficos
- **Arquitectura:** Red neuronal con múltiples capas ocultas
- **Preprocesamiento:** StandardScaler para variables numéricas, OneHotEncoder para categóricas
- **Rendimiento:** Validado en conjunto de test con stratified k-fold

---

## ⚙️ CONFIGURACIÓN

### Variables de Entorno (`.env`)

Puedes configurar en `.env`:
```
HOST=0.0.0.0
PORT=5000
DEBUG=True
LOG_LEVEL=INFO
SECRET_KEY=tu-clave-secreta
```

### Rutas de Archivos

- **Modelo:** `PROYECTO SIUUU/models/education_mlp_pipeline.joblib`
- **Logs:** `logs/app.log`
- **Frontend:** `templates/admin.html`
- **JavaScript:** `static/js/ml-predictor.js`

---

## 🔍 ESTRUCTURA DE CARPETAS DESPUÉS DE LA INTEGRACIÓN

```
proyecto_senasoft/
├── app.py                          ✅ Modificado (con ML endpoints)
├── requirements.txt                ✅ Modificado (joblib agregado)
├── static/
│   ├── js/
│   │   ├── admin.js               ✓ Sin cambios
│   │   ├── chat.js                ✓ Sin cambios
│   │   ├── auth.js                ✓ Sin cambios
│   │   ├── ux-enhancements.js     ✓ Sin cambios
│   │   └── ml-predictor.js        ✨ NUEVO
│   └── css/
│       └── style.css              ✓ Sin cambios
├── templates/
│   ├── admin.html                 ✅ Modificado (nueva sección ML)
│   ├── index.html                 ✓ Sin cambios
│   └── ...
├── logs/
│   └── app.log                    📝 Se creará al ejecutar
├── PROYECTO SIUUU/
│   └── models/
│       └── education_mlp_pipeline.joblib  (Modelo entrenado)
└── ML_INTEGRATION_GUIDE.md        📖 Este archivo
```

---

## 📝 LOGS

Después de ejecutar, verifica los logs:

```bash
tail -f logs/app.log
```

Deberías ver:
```
2025-10-22 14:30:00,123 - __main__ - INFO - ✓ Modelo ML cargado correctamente...
2025-10-22 14:30:05,456 - __main__ - INFO - Predicción realizada: 0 (probabilidades: [0.85, 0.15])
```

---

## 🐛 TROUBLESHOOTING

### Error: "Modelo ML no disponible"
**Solución:** Verifica que exista el archivo:
```bash
ls "PROYECTO SIUUU/models/education_mlp_pipeline.joblib"
```

### Error: "Features faltantes"
**Solución:** Asegúrate de enviar exactamente estos 14 features en el orden correcto

### Error: "Valores inválidos"
**Solución:** Verifica que todos los valores sean números válidos dentro de los rangos:
- Porcentajes: 0-100
- Estrato: 1-6
- Puntaje: 0-500
- Otros: >= 0

### ImportError: joblib not found
**Solución:** Instala la dependencia:
```bash
pip install joblib
```

---

## ✨ MEJORAS FUTURAS

1. **Autenticación mejorada:** Sistema real de login/roles
2. **Base de datos:** Almacenar historial de predicciones
3. **Graficas:** Análisis visual de predicciones
4. **Exportación:** CSV, Excel, PDF de resultados
5. **Caching:** Redis para optimizar respuestas
6. **Explicabilidad:** SHAP values para interpretar predicciones
7. **Multi-lenguaje:** Soporte para múltiples idiomas
8. **Mobile:** Aplicación móvil con Flutter/React Native

---

## 📞 CONTACTO Y SOPORTE

Para reportar problemas o sugerencias, contacta al equipo de desarrollo.

---

## 📄 ARCHIVOS MODIFICADOS

| Archivo | Cambios | Líneas |
|---------|---------|--------|
| `app.py` | Imports, load_ml_model(), /api/predict, /api/predict-batch | +150 |
| `requirements.txt` | Agregado joblib | +1 |
| `templates/admin.html` | Estilos ML, formulario, botones | +400 |
| `static/js/ml-predictor.js` | NUEVO - módulo completo | +600 |

**Total de cambios:** ~1150 líneas de código nuevo/modificado

---

## ✅ CHECKLIST DE VALIDACIÓN

- [x] Modelo cargado correctamente al iniciar
- [x] Endpoint `/api/predict` funcional
- [x] Endpoint `/api/predict-batch` funcional
- [x] Formulario con 14 campos en admin.html
- [x] Validación de entrada en cliente
- [x] Validación de entrada en servidor
- [x] Visualización de resultados
- [x] Manejo de errores
- [x] Responsivo en móvil
- [x] Tooltips explicativos
- [x] Animaciones suaves
- [x] Funcionalidad export
- [x] Funcionalidad clear form
- [x] Botón load example
- [x] Documentación completa

---

**Versión:** 1.0.0  
**Fecha:** Octubre 22, 2025  
**Estado:** ✅ COMPLETADO
