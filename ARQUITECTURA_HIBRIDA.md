# 🎯 ARQUITECTURA - Sistema Híbrido de Chatbot Inteligente

## 📐 Arquitectura General

```
┌─────────────────────────────────────────────────────────────────┐
│                     USUARIO (Frontend)                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         Smart Chat Interface                            │  │
│  │  - HTML5 Chat UI                                        │  │
│  │  - JavaScript Event Handlers                            │  │
│  │  - Real-time Message Display                            │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                         ↓ HTTP/REST ↓
┌─────────────────────────────────────────────────────────────────┐
│                     Flask Application (app.py)                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              API Endpoints                              │  │
│  │  /api/message              (Legacy)                     │  │
│  │  /api/chat-intelligent     (Orquestador)                │  │
│  │  /api/predict              (MLP directo)                │  │
│  │  /api/chat-history         (Historial)                  │  │
│  │  /api/chat-export          (Exportar)                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                         ↓ Python ↓
┌─────────────────────────────────────────────────────────────────┐
│            ChatbotOrchestrator (chatbot_orchestrator.py)        │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   NLP Layer  │  │  Prediction  │  │ Improvement  │         │
│  │              │  │   Engine     │  │   Generator  │         │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤         │
│  │IntentDetector│→ │ML_MODEL(MLP) │→ │VAE_DECODER   │         │
│  │EntityExtract │  │              │  │              │         │
│  │ResponseGener │  │              │  │              │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│         ↑                              ↓                        │
│         └──────────────────────────────┘                        │
│              (Coordinated Flow)                                 │
└─────────────────────────────────────────────────────────────────┘
                         ↓                    ↓
         ┌─────────────────────┐    ┌──────────────────┐
         │  Trained Models     │    │  Data Storage    │
         ├─────────────────────┤    ├──────────────────┤
         │ MLP Pipeline        │    │ Conversation     │
         │ (joblib)            │    │ Logs (JSON)      │
         │                     │    │                  │
         │ VAE Encoder (h5)    │    │ Metadata         │
         │ VAE Decoder (h5)    │    │                  │
         │ Scaler (pkl)        │    │                  │
         └─────────────────────┘    └──────────────────┘
```

---

## 🔄 Flujo de Procesamiento Completo

### Escenario 1: Simple Chat
```
Usuario: "Hola"
   ↓
IntentDetector.detect("Hola")
   → intent: "saludar"
   → confidence: 95%
   ↓
EntityExtractor.extract("Hola")
   → entities: {}
   ↓
ResponseGenerator.generate("saludar", {}, None)
   → "¡Hola! Soy BOTI..."
   ↓
Response → Usuario
```

### Escenario 2: Predicción con Datos
```
Usuario: "Analiza mi región", user_data: {14 features}
   ↓
IntentDetector.detect(...)
   → intent: "prediccion"
   ↓
EntityExtractor.extract(...)
   → entities: {...}
   ↓
ML_MODEL.predict(user_data)
   → prediction: 1 (con acceso)
   → probability: 85%
   ↓
ResponseGenerator.generate("prediccion", entities, prediction_result)
   → Respuesta + resultado
   ↓
Response + Predicción → Usuario
```

### Escenario 3: Generación de Mejoras
```
Usuario: "¿Cómo mejorar?", user_data: {14 features}
   ↓
IntentDetector.detect(...)
   → intent: "mejora"
   ↓
EntityExtractor.extract(...)
   ↓
Ejecutar predicción (MLP)
   ↓
VAE_DECODER.predict(sampled_z)
   → 3 propuestas sintéticas
   ↓
ResponseGenerator.generate("mejora", ...)
   → Respuesta + propuestas
   ↓
Response + Improvements → Usuario
```

---

## 📦 Componentes Clave

### 1. **IntentDetector**
```python
class IntentDetector:
    intents = {
        'saludar': {'keywords': [...], 'patterns': [...]},
        'prediccion': {...},
        'mejora': {...},
        ...
    }
    
    def detect(message: str) → (intent: str, confidence: float)
```

**Intenciones soportadas**:
- saludar
- despedida
- ayuda
- prediccion
- conectividad
- educacion
- mejora
- reporte
- region

### 2. **EntityExtractor**
```python
class EntityExtractor:
    def extract(message: str) → Dict:
        - region: str|None
        - numbers: List[float]
        - keywords: List[str]
        - has_data_request: bool
```

**Entidades extraídas**:
- Regiones colombianas
- Números mencionados
- Palabras clave importantes
- Indicadores de solicitud de datos

### 3. **ResponseGenerator**
```python
class ResponseGenerator:
    templates = {
        'saludar': [...],
        'ayuda_inicio': [...],
        'prediccion_exito': [...],
        'prediccion_alerta': [...],
        ...
    }
    
    def generate(intent, entities, prediction, region) → str
```

### 4. **ChatbotOrchestrator**
```python
class ChatbotOrchestrator:
    def __init__(ml_model, vae_encoder, vae_decoder, vae_scaler, vae_features)
    
    def process_message(user_message, user_data) → Dict:
        1. Detectar intención
        2. Extraer entidades
        3. Actualizar contexto
        4. Ejecutar modelos (si necesario)
        5. Generar respuesta
        6. Registrar en historial
        7. Retornar respuesta completa
    
    def get_conversation_history() → List[Dict]
    def reset_context() → None
    def export_conversation() → Dict
```

---

## 🎓 Modelos ML Usados

### 1. **Modelo Predictivo (MLP)**
- **Archivo**: `PROYECTO SIUUU/models/education_mlp_pipeline.joblib`
- **Framework**: scikit-learn
- **Tipo**: Multi-layer Perceptron Classifier
- **Input**: 14 features educativos
- **Output**: 0/1 (sin/con acceso a internet)
- **Accuracy**: ~85-95% (según datos)

**Features requeridos** (14):
```python
[
    'poblacion_total', 'porcentaje_rural', 'estrato_promedio',
    'tasa_pobreza', 'num_instituciones', 'computadores_por_estudiante',
    'salones_por_institucion', 'docentes_por_institucion',
    'cobertura_electrica', 'cobertura_4g',
    'dispositivos_promedio_hogar', 'tasa_aprobacion',
    'tasa_desercion', 'puntaje_pruebas'
]
```

### 2. **Modelo Generativo (VAE)**
- **Archivos**:
  - `PROYECTO SIUUU/models/vae_encoder.h5` (compresión)
  - `PROYECTO SIUUU/models/vae_decoder.h5` (generación)
  - `PROYECTO SIUUU/models/vae_scaler.pkl` (normalización)

- **Framework**: TensorFlow/Keras
- **Input**: 14 features (escalados)
- **Latent Dim**: 8
- **Output**: 14 features mejores (sintéticas)
- **Uso**: Generar propuestas de mejora

**Arquitectura**:
```
Encoder: Input(14) → Dense(64) → Dense(32) → Dense(16) → Latent(8)
Decoder: Latent(8) → Dense(16) → Dense(32) → Dense(64) → Output(14)
Loss: Reconstruction MSE + KL Divergence
```

---

## 🔌 Interfaz de API

### Request/Response Standard

**Request**:
```json
{
    "message": "Texto del usuario",
    "user_data": {
        "poblacion_total": 16295,
        "porcentaje_rural": 8.66,
        ... (11 features más)
    }
}
```

**Response**:
```json
{
    "response": "Respuesta contextualizada del bot",
    "intent": "saludar",
    "intent_confidence": 0.95,
    "entities": {
        "region": "Bogotá",
        "numbers": [16295],
        "keywords": ["internet"],
        "has_data_request": false
    },
    "prediction": {
        "executed": true,
        "prediction": 1,
        "probability_with_access": 0.85,
        "interpretation": "Con acceso a internet"
    },
    "improvements": {
        "executed": true,
        "n_proposals": 3,
        "proposals": [
            {
                "proposal_id": 1,
                "strength": 30.0,
                "features": {...}
            }
        ]
    },
    "region": "Bogotá",
    "timestamp": "2025-01-15T10:30:00"
}
```

---

## 📂 Estructura de Archivos Relevantes

```
proyecto_senasoft/
├── app.py                              # Aplicación principal (modificada)
├── requirements_updated.txt            # Dependencias (incluyendo TensorFlow)
├── train_vae_model.py                  # Script para entrenar VAE
├── test_hybrid_system.py               # Suite de pruebas
├── GUIA_INICIO_RAPIDO.md               # Esta guía
│
├── src/
│   └── chatbot/
│       ├── __init__.py
│       └── chatbot_orchestrator.py     # Orquestador principal (NUEVO)
│
├── static/
│   ├── css/
│   │   └── smart-chat.css              # Estilos del chat (NUEVO)
│   └── js/
│       ├── chat.js                     # Chat original
│       ├── ml-predictor.js             # Predicción ML
│       └── smart-chat-interface.js     # Interfaz inteligente (NUEVO)
│
├── templates/
│   └── index.html                      # Chat UI (usar smart-chat-interface.js)
│
├── PROYECTO SIUUU/
│   └── models/
│       ├── education_mlp_pipeline.joblib
│       ├── vae_encoder.h5              # Generado por train_vae_model.py
│       ├── vae_decoder.h5              # Generado por train_vae_model.py
│       ├── vae_scaler.pkl              # Generado por train_vae_model.py
│       └── vae_metadata.json           # Generado por train_vae_model.py
│
└── logs/
    └── app.log                         # Logs de la aplicación
```

---

## 🚀 Deployment Checklist

- [ ] Python 3.8+ instalado
- [ ] `pip install -r requirements_updated.txt` ejecutado
- [ ] `python train_vae_model.py` ejecutado (genera modelos VAE)
- [ ] `python test_hybrid_system.py` pasado exitosamente
- [ ] `python app.py` inicia sin errores
- [ ] http://localhost:5000 accesible
- [ ] Chat responde a mensajes
- [ ] Predicciones funcionan en /admin
- [ ] Exportación de historial funciona

---

## 📊 Monitoreo

### Métricas a Monitorear
1. **Intent Detection Accuracy**: % de intenciones detectadas correctamente
2. **Response Time**: Tiempo promedio de respuesta (< 1s)
3. **Model Prediction Confidence**: Confianza promedio de predicciones
4. **VAE Generation Quality**: Validez de propuestas generadas
5. **User Satisfaction**: Feedback en conversaciones

### Logs Importantes
```bash
# Ver último error
tail -20 logs/app.log

# Intenciones detectadas
grep "Intención detectada" logs/app.log

# Predicciones ejecutadas
grep "Predicción realizada" logs/app.log

# Mejoras generadas
grep "mejoras" logs/app.log | grep -i "generando"
```

---

## 🎨 Personalización

### Agregar Nueva Intención
En `chatbot_orchestrator.py`:
```python
self.intents['nueva_intencion'] = {
    'keywords': ['palabra1', 'palabra2'],
    'patterns': [r'regex_pattern']
}
```

### Agregar Nuevo Template de Respuesta
```python
self.templates['nueva_intencion'] = [
    "Primera respuesta posible",
    "Segunda respuesta posible"
]
```

### Modificar Arquitectura VAE
En `train_vae_model.py`:
```python
latent_dim = 16  # En lugar de 8
# VAE aprenderá representaciones más complejas
```

---

## 🔐 Consideraciones de Seguridad

1. **Input Validation**: Todos los inputs se validan en NLP
2. **Error Handling**: Errores se capturan y loguean sin exponer detalles
3. **Modelo Privacy**: Modelos son locales, no se envían datos a servidores externos
4. **Sanitization**: Mensajes se limpian antes de procesamiento

---

## ✅ Casos de Uso Validados

| Caso de Uso | Status | Descripción |
|------------|--------|-------------|
| Chat simple | ✅ | Usuario saluda, bot responde |
| Predicción | ✅ | Usuario da datos, bot predice |
| Extracción de región | ✅ | Bot identifica ubicación automáticamente |
| Mejora generativa | ✅ | Bot genera propuestas de mejora |
| Historial | ✅ | Conversación se registra |
| Exportación | ✅ | Datos exportables como JSON |
| Multi-idioma | ⚠️ | Parcial (solo español por ahora) |
| Persistencia BD | ❌ | Futuro |

---

**Documento creado**: 2025-01-15  
**Versión**: 1.0 (Sistema Híbrido Completo)  
**Estado**: ✅ Listo para Producción
