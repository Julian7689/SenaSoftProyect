# 🤖 Chatbot de Apoyo para Víctimas - SENASOFT

## 📋 Descripción

Aplicación web monolítica con chatbot inteligente de apoyo para víctimas o personas en situación de riesgo. Analiza los mensajes del usuario y determina el tipo de problema que enfrenta, ofreciendo respuestas predefinidas y orientación según el caso.

## 🎯 Características

- 🤖 **Chatbot inteligente** con clasificación de problemas
- 🌐 **Interfaz web integrada** (Frontend + Backend en un solo proyecto)
- 🧠 **IA para análisis de texto** y generación de respuestas empáticas
- 📱 **Diseño responsive** para móviles y desktop
- 🔒 **Privacidad y seguridad** de las conversaciones

### Categorías de problemas detectados:
- 🏠 Violencia doméstica
- 😰 Acoso
- 🧠 Problemas de salud mental
- 🚨 Emergencias de seguridad
- 💙 Ayuda social o psicológica

## 🏗️ Estructura del Proyecto (Monolítico)

```
proyecto_senasoft/
│
├── app.py                          # ⭐ Aplicación principal (punto de entrada)
│
├── static/                         # Frontend - Archivos estáticos
│   ├── css/                        # Estilos CSS
│   │   └── style.css
│   ├── js/                         # JavaScript del cliente
│   │   └── chat.js
│   └── images/                     # Imágenes, iconos
│
├── templates/                      # Frontend - Plantillas HTML
│   ├── index.html                  # Página principal del chat
│   ├── base.html                   # Template base
│   └── info.html                   # Página de información
│
├── src/                            # Backend - Lógica del negocio
│   ├── api/                        # Endpoints de la API
│   │   ├── __init__.py
│   │   └── routes.py               # Rutas Flask/FastAPI
│   │
│   ├── classification/             # Clasificación de mensajes
│   │   ├── __init__.py
│   │   ├── classifier.py           # Clasificador de categorías
│   │   └── train.py                # Entrenamiento del modelo
│   │
│   ├── chatbot/                    # Motor del chatbot
│   │   ├── __init__.py
│   │   ├── bot.py                  # Lógica principal del bot
│   │   └── conversation.py         # Manejo de sesiones
│   │
│   ├── responses/                  # Generación de respuestas
│   │   ├── __init__.py
│   │   ├── response_generator.py  # IA generativa
│   │   └── templates.py            # Respuestas predefinidas
│   │
│   └── utils/                      # Utilidades
│       ├── __init__.py
│       ├── text_processing.py     # Procesamiento de texto
│       └── logger.py              # Sistema de logs
│
├── data/                           # Datos
│   ├── raw/                        # Datos originales
│   │   └── dataset_comunidades_senasoft.csv
│   ├── processed/                  # Datos procesados
│   └── preprocessing/              # Scripts de preprocesamiento
│       └── processed.py
│
├── models/                         # Modelos de ML
│   ├── trained/                    # Modelos entrenados (.pkl, .pt)
│   └── checkpoints/                # Checkpoints de entrenamiento
│
├── config/                         # Configuración
│   ├── categories.json            # Definición de categorías
│   ├── resources.json             # Recursos de ayuda (líneas, contactos)
│   └── settings.py                # Configuración general
│
├── notebooks/                      # Análisis y experimentación
│   └── exploratory_analysis.ipynb
│
├── tests/                          # Tests
│   └── test_chatbot.py
│
├── logs/                           # Logs de la aplicación
│
├── requirements.txt                # Dependencias Python
├── .env.example                    # Ejemplo de variables de entorno
├── .gitignore
└── README.md
```

## 🚀 Instalación y Ejecución

### 1. Clonar/Preparar el proyecto
```bash
cd proyecto_senasoft
```

### 2. Crear entorno virtual
```bash
python -m venv venv

# Activar (Windows)
.\venv\Scripts\activate

# Activar (Linux/Mac)
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
```bash
# Copiar el archivo de ejemplo
copy .env.example .env

# Editar .env con tus credenciales (si usas IBM Watson, OpenAI, etc.)
```

### 5. Ejecutar la aplicación
```bash
python app.py
```

La aplicación estará disponible en: **http://localhost:5000**

## 💻 Tecnologías Utilizadas

### Backend
- **Flask** - Framework web minimalista
- **Python 3.8+**
- **Transformers/Hugging Face** - Modelos de NLP
- **scikit-learn** - Clasificación ML
- **pandas, numpy** - Procesamiento de datos

### Frontend
- **HTML5, CSS3, JavaScript**
- **Bootstrap 5** (opcional) - UI responsive
- **Fetch API** - Comunicación con backend

### IA (Opciones)
- **IBM Granite** - IA generativa
- **OpenAI GPT** - Alternativa
- **Modelos locales** - DistilBERT, etc.

## 📡 API Endpoints

```
GET  /                    -> Página principal del chat
POST /api/message         -> Enviar mensaje al chatbot
GET  /api/resources       -> Obtener recursos de ayuda
GET  /api/categories      -> Lista de categorías
POST /api/emergency       -> Reportar emergencia
```

##  Interfaz de Usuario

La interfaz incluye:
- **Chat interactivo** con historial de conversación
- **Indicadores de escritura** ("bot está escribiendo...")
- **Detección de urgencia** con alertas visuales
- **Recursos de ayuda** accesibles desde el chat
- **Diseño empático** con colores calmantes

##  Seguridad y Privacidad

- ✅ Conversaciones no se almacenan permanentemente
- ✅ Anonimización de datos sensibles
- ✅ Cifrado de comunicaciones (HTTPS en producción)
- ✅ Sin tracking de usuarios

## Recursos de Emergencia (Colombia)

- **123** - Línea de Emergencias Nacional
- **155** - Línea Púrpura (Violencia contra la mujer)
- **141** - ICBF (Bienestar Familiar)
- **106** - Línea de Salud Mental

## 🧪 Testing

```bash
# Ejecutar tests
pytest tests/

# Con cobertura
pytest --cov=src tests/
```

## 📦 Deployment

Para producción, considera:
- **Gunicorn** como servidor WSGI
- **Nginx** como reverse proxy
- **Docker** para containerización
- **Heroku/Railway/Render** para hosting simple

## 🤝 Contribución

Proyecto desarrollado para **SENASOFT 2025**

## ⚠️ Aviso Legal

Este chatbot es una **herramienta de apoyo** y NO reemplaza atención profesional, médica o legal. En caso de emergencia real, contacta inmediatamente a las autoridades locales (Línea 123).

## 📝 Licencia

[Definir licencia del proyecto]
