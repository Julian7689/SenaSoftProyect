"""
Aplicación principal del Chatbot de Apoyo para Víctimas
Aplicación monolítica con Flask que integra frontend y backend
"""
import sys
import io
# Configurar UTF-8 para Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from dotenv import load_dotenv
import os
import logging
from datetime import datetime
import joblib
import numpy as np
import pandas as pd
from pathlib import Path

# Cargar variables de entorno
load_dotenv()

# Importar módulos propios
from src.chatbot.chatbot_orchestrator import ChatbotOrchestrator
try:
    import tensorflow as tf
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False

# Configuración de la aplicación
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['DEBUG'] = os.getenv('DEBUG', 'True') == 'True'

# CORS para permitir peticiones del frontend
CORS(app)

# Configuración de logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==================== CARGA DEL MODELO ML ====================
# Cargar el modelo UNA SOLA VEZ al iniciar la aplicación
ML_MODEL = None
MODEL_FEATURES = None
MODEL_LOADED = False

# ==================== ORQUESTADOR CONVERSACIONAL ====================
# Componente híbrido: NLP + Predicción + Generación
CHATBOT_ORCHESTRATOR = None
VAE_ENCODER = None
VAE_DECODER = None
VAE_SCALER = None
ORCHESTRATOR_READY = False

def load_ml_model():
    """Cargar el modelo de ML entrenado (se ejecuta una sola vez)"""
    global ML_MODEL, MODEL_FEATURES, MODEL_LOADED
    
    try:
        model_path = Path('PROYECTO SIUUU/models/education_mlp_pipeline.joblib')
        
        if model_path.exists():
            ML_MODEL = joblib.load(model_path)
            MODEL_LOADED = True
            
            # Definir features que el modelo espera (en el orden correcto)
            MODEL_FEATURES = [
                'poblacion_total', 'porcentaje_rural', 'estrato_promedio', 'tasa_pobreza',
                'num_instituciones', 'computadores_por_estudiante', 'salones_por_institucion',
                'docentes_por_institucion', 'cobertura_electrica', 'cobertura_4g',
                'dispositivos_promedio_hogar', 'tasa_aprobacion', 'tasa_desercion',
                'puntaje_pruebas'
            ]
            
            logger.info(f"✓ Modelo ML cargado correctamente desde {model_path}")
            logger.info(f"✓ Modelo espera {len(MODEL_FEATURES)} features")
            return True
        else:
            logger.warning(f"⚠ Archivo de modelo no encontrado en {model_path}")
            return False
    except Exception as e:
        logger.error(f"✗ Error cargando modelo ML: {str(e)}")
        return False

def load_orchestrator():
    """Cargar el orquestador conversacional con todos los componentes"""
    global CHATBOT_ORCHESTRATOR, VAE_ENCODER, VAE_DECODER, VAE_SCALER, ORCHESTRATOR_READY
    
    try:
        # Intentar cargar VAE (opcional)
        vae_encoder_path = Path('PROYECTO SIUUU/models/vae_encoder.h5')
        vae_decoder_path = Path('PROYECTO SIUUU/models/vae_decoder.h5')
        vae_scaler_path = Path('PROYECTO SIUUU/models/vae_scaler.pkl')
        
        if (TENSORFLOW_AVAILABLE and 
            vae_encoder_path.exists() and 
            vae_decoder_path.exists() and 
            vae_scaler_path.exists()):
            
            try:
                import tensorflow.keras as keras
                VAE_ENCODER = keras.models.load_model(str(vae_encoder_path))
                VAE_DECODER = keras.models.load_model(str(vae_decoder_path))
                VAE_SCALER = joblib.load(str(vae_scaler_path))
                logger.info("✓ Modelos VAE cargados correctamente")
            except Exception as e:
                logger.warning(f"⚠ No se pudieron cargar modelos VAE: {str(e)}")
                VAE_ENCODER = None
                VAE_DECODER = None
                VAE_SCALER = None
        else:
            if not TENSORFLOW_AVAILABLE:
                logger.info("ℹ TensorFlow no disponible - VAE no se cargará")
            else:
                logger.info("ℹ Modelos VAE no encontrados - procedeiendo sin ellos")

        CHATBOT_ORCHESTRATOR = ChatbotOrchestrator(
            ml_model=ML_MODEL,
            vae_encoder=VAE_ENCODER,
            vae_decoder=VAE_DECODER,
            vae_scaler=VAE_SCALER,
            vae_features=MODEL_FEATURES
        )
        ORCHESTRATOR_READY = True
        logger.info("✓ ChatbotOrchestrator inicializado correctamente")
        return True
        
    except Exception as e:
        logger.error(f"✗ Error inicializando orquestador: {str(e)}")
        ORCHESTRATOR_READY = False
        return False

# ==================== RUTAS DEL FRONTEND ====================

@app.route('/')
def index():
    """Página principal del chat"""
    return render_template('chat_simple.html')

@app.route('/info')
def info():
    """Página de información sobre recursos"""
    return render_template('info.html')
@app.route('/login')
def login():
    """Página de login de usuarios"""
    return render_template('login.html')
@app.route('/admin')
def admin_dashboard():
    """Panel de administración (provisional, protegido en cliente)"""
    return render_template('admin.html')
# ==================== API ENDPOINTS ====================
# ==================== API ENDPOINTS ====================

@app.route('/api/message', methods=['POST'])
def send_message():
    """
    Endpoint para recibir mensajes del usuario y obtener respuesta del chatbot
    
    Request JSON:
    {
        "message": "texto del mensaje",
        "session_id": "id-opcional-de-sesion",
        "user_data": { "feature1": value1, ... }  # opcional
    }
    
    Response JSON:
    {
        "response": "respuesta del bot",
        "intent": "intención_detectada",
        "category": "categoria_detectada",
        "urgency": "low|medium|high|critical",
        "resources": [...],
        "timestamp": "2025-10-21T10:30:00"
    }
    """
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        session_id = data.get('session_id', None)
        user_data = data.get('user_data', None)
        
        if not user_message:
            return jsonify({'error': 'Mensaje vacío'}), 400
        
        logger.info(f"Mensaje recibido: {user_message[:50]}...")
        logger.info(f"Estado del orquestador - READY: {ORCHESTRATOR_READY}, INSTANCE: {CHATBOT_ORCHESTRATOR is not None}")
        
        # Usar el orquestador si está disponible
        if ORCHESTRATOR_READY and CHATBOT_ORCHESTRATOR:
            try:
                logger.info("✓ Usando ChatbotOrchestrator para procesar mensaje")
                result = CHATBOT_ORCHESTRATOR.process_message(user_message, user_data)
                logger.info(f"✓ Respuesta del orquestador: {result['response'][:100]}...")
                
                response = {
                    'response': result['response'],
                    'intent': result['intent'],
                    'intent_confidence': result['intent_confidence'],
                    'entities': result['entities'],
                    'prediction': result['prediction'],
                    'improvements': result['improvements'],
                    'region': result['region'],
                    'timestamp': result['timestamp'],
                    'using_orchestrator': True
                }
                
                return jsonify(response), 200
            
            except Exception as e:
                logger.error(f"✗ Error en orquestador: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                # Fallback a respuesta simple
        else:
            logger.warning("⚠ Orquestador NO disponible, usando fallback")
        
        # Fallback: respuesta simple (sin orquestador)
        response = {
            'response': 'Gracias por escribir. Estoy aquí para ayudarte. ¿Puedes contarme más sobre tu situación?',
            'intent': 'general',
            'intent_confidence': 0.0,
            'category': 'unknown',
            'urgency': 'low',
            'resources': [],
            'timestamp': datetime.now().isoformat(),
            'using_orchestrator': False
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error procesando mensaje: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/api/resources', methods=['GET'])
def get_resources():
    """Obtener lista de recursos de ayuda disponibles"""
    try:
        # TODO: Cargar desde config/resources.json
        resources = {
            'emergency_contacts': {
                'policia': {'number': '123', 'name': 'Emergencias'},
                'violencia_mujer': {'number': '155', 'name': 'Línea Púrpura'},
                'salud_mental': {'number': '106', 'name': 'Salud Mental'}
            }
        }
        return jsonify(resources), 200
    except Exception as e:
        logger.error(f"Error obteniendo recursos: {str(e)}")
        return jsonify({'error': 'Error obteniendo recursos'}), 500

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Obtener lista de categorías de problemas"""
    try:
        # TODO: Cargar desde config/categories.json
        categories = [
            'violencia_domestica',
            'acoso',
            'salud_mental',
            'emergencia',
            'ayuda_social'
        ]
        return jsonify({'categories': categories}), 200
    except Exception as e:
        logger.error(f"Error obteniendo categorías: {str(e)}")
        return jsonify({'error': 'Error obteniendo categorías'}), 500

@app.route('/api/emergency', methods=['POST'])
def report_emergency():
    """Endpoint especial para situaciones de emergencia"""
    try:
        data = request.get_json()
        logger.critical(f"EMERGENCIA REPORTADA: {data}")
        
        response = {
            'message': 'Si estás en peligro inmediato, llama al 123',
            'emergency_number': '123',
            'status': 'emergency_detected'
        }
        return jsonify(response), 200
    except Exception as e:
        logger.error(f"Error en reporte de emergencia: {str(e)}")
        return jsonify({'error': 'Error procesando emergencia'}), 500

# ==================== ENDPOINT DE PREDICCIÓN ML ====================

@app.route('/api/predict', methods=['POST'])
def predict():
    """
    Endpoint para hacer predicciones con el modelo ML entrenado.
    
    Request JSON (ejemplo):
    {
        "poblacion_total": 16295,
        "porcentaje_rural": 8.66,
        "estrato_promedio": 2.54,
        ... (todos los 14 features)
    }
    
    Response JSON:
    {
        "success": true,
        "prediction": 0,
        "prediction_proba": [0.85, 0.15],
        "interpretation": "El indicador sugiere: Acceso limitado a internet"
    }
    """
    try:
        # Validar que el modelo esté cargado
        if not MODEL_LOADED or ML_MODEL is None:
            return jsonify({
                'success': False,
                'error': 'Modelo ML no disponible. Reinicia la aplicación.'
            }), 503
        
        # Obtener datos del request
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No se enviaron datos'
            }), 400
        
        # Construir vector de features en el orden correcto
        try:
            input_values = []
            missing_features = []
            
            for feature in MODEL_FEATURES:
                if feature in data:
                    try:
                        val = float(data[feature])
                        input_values.append(val)
                    except (ValueError, TypeError):
                        return jsonify({
                            'success': False,
                            'error': f'Valor inválido para feature "{feature}": {data[feature]}'
                        }), 400
                else:
                    missing_features.append(feature)
            
            if missing_features:
                return jsonify({
                    'success': False,
                    'error': f'Features faltantes: {", ".join(missing_features)}',
                    'required_features': MODEL_FEATURES
                }), 400
            
            # Preparar input como matriz 2D (el modelo espera (n_samples, n_features))
            X_input = np.array([input_values]).reshape(1, -1)
            
            # Hacer predicción
            prediction = ML_MODEL.predict(X_input)[0]
            
            # Obtener probabilidades si el modelo las soporta
            try:
                prediction_proba = ML_MODEL.predict_proba(X_input)[0]
                proba_list = prediction_proba.tolist()
            except:
                proba_list = [None, None]
            
            # Interpretación de la predicción
            interpretation_map = {
                0: "🔴 Sin acceso a internet - Se requieren recursos de conectividad",
                1: "🟢 Con acceso a internet - Buena cobertura digital"
            }
            
            interpretation = interpretation_map.get(int(prediction), "Predicción completada")
            
            # Log de la predicción
            logger.info(f"Predicción realizada: {prediction} (probabilidades: {proba_list})")
            
            response = {
                'success': True,
                'prediction': int(prediction),
                'prediction_proba': proba_list,
                'interpretation': interpretation,
                'timestamp': datetime.now().isoformat()
            }
            
            return jsonify(response), 200
        
        except Exception as e:
            logger.error(f"Error procesando features: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Error procesando datos: {str(e)}'
            }), 400
        
    except Exception as e:
        logger.error(f"Error en predicción ML: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error interno del servidor'
        }), 500

@app.route('/api/predict-batch', methods=['POST'])
def predict_batch():
    """
    Endpoint para hacer predicciones en lote (para múltiples registros).
    Útil para análisis masivo de datos.
    
    Request JSON:
    {
        "records": [
            { feature1: value1, ... },
            { feature1: value1, ... }
        ]
    }
    """
    try:
        if not MODEL_LOADED or ML_MODEL is None:
            return jsonify({
                'success': False,
                'error': 'Modelo ML no disponible'
            }), 503
        
        data = request.get_json()
        records = data.get('records', [])
        
        if not records or len(records) == 0:
            return jsonify({
                'success': False,
                'error': 'No records provided'
            }), 400
        
        predictions = []
        
        for idx, record in enumerate(records):
            try:
                input_values = []
                for feature in MODEL_FEATURES:
                    input_values.append(float(record.get(feature, 0)))
                
                X_input = np.array([input_values]).reshape(1, -1)
                pred = ML_MODEL.predict(X_input)[0]
                predictions.append({
                    'record_id': idx,
                    'prediction': int(pred)
                })
            except Exception as e:
                logger.warning(f"Error procesando record {idx}: {str(e)}")
                continue
        
        return jsonify({
            'success': True,
            'total_records': len(records),
            'predictions': predictions,
            'timestamp': datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"Error en predicción batch: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error interno del servidor'
        }), 500

# ==================== ENDPOINTS DEL ORQUESTADOR ====================

@app.route('/api/chat-intelligent', methods=['POST'])
def chat_intelligent():
    """
    Endpoint para chat inteligente con todos los componentes del orquestador
    (NLP + Predicción + Generación de mejoras)
    
    Request JSON:
    {
        "message": "Hola, soy de Bogotá",
        "user_data": {
            "poblacion_total": 16295,
            ... (todos los 14 features opcionales)
        }
    }
    
    Response JSON:
    {
        "response": "Respuesta inteligente del bot...",
        "intent": "saludar",
        "intent_confidence": 0.95,
        "entities": { "region": "Bogotá", ... },
        "prediction": { "executed": true, "prediction": 1, ... },
        "improvements": { "executed": true, "proposals": [...] },
        "timestamp": "..."
    }
    """
    try:
        if not ORCHESTRATOR_READY or CHATBOT_ORCHESTRATOR is None:
            return jsonify({
                'success': False,
                'error': 'Orquestador no disponible. Reinicia la aplicación.'
            }), 503
        
        data = request.get_json()
        user_message = data.get('message', '')
        user_data = data.get('user_data', None)
        
        if not user_message:
            return jsonify({'error': 'Mensaje vacío'}), 400
        
        # Procesar con el orquestador
        result = CHATBOT_ORCHESTRATOR.process_message(user_message, user_data)
        
        return jsonify(result), 200
    
    except Exception as e:
        logger.error(f"Error en chat inteligente: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error interno del servidor'
        }), 500

@app.route('/api/chat-history', methods=['GET'])
def chat_history():
    """Obtiene el historial de conversación del usuario actual"""
    try:
        if not ORCHESTRATOR_READY or CHATBOT_ORCHESTRATOR is None:
            return jsonify({'history': []}), 200
        
        history = CHATBOT_ORCHESTRATOR.get_conversation_history()
        
        return jsonify({
            'success': True,
            'count': len(history),
            'history': history,
            'timestamp': datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"Error obteniendo historial: {str(e)}")
        return jsonify({'error': 'Error obteniendo historial'}), 500

@app.route('/api/chat-reset', methods=['POST'])
def chat_reset():
    """Reinicia el contexto del usuario"""
    try:
        if ORCHESTRATOR_READY and CHATBOT_ORCHESTRATOR:
            CHATBOT_ORCHESTRATOR.reset_context()
        
        return jsonify({
            'success': True,
            'message': 'Contexto reiniciado',
            'timestamp': datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"Error reiniciando contexto: {str(e)}")
        return jsonify({'error': 'Error reiniciando contexto'}), 500

@app.route('/api/chat-export', methods=['GET'])
def chat_export():
    """Exporta la conversación para análisis"""
    try:
        if not ORCHESTRATOR_READY or CHATBOT_ORCHESTRATOR is None:
            return jsonify({'export': {}}), 200
        
        export = CHATBOT_ORCHESTRATOR.export_conversation()
        
        return jsonify({
            'success': True,
            'export': export,
            'timestamp': datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"Error exportando conversación: {str(e)}")
        return jsonify({'error': 'Error exportando conversación'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint para verificar el estado de la aplicación"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    }), 200

# ==================== MANEJO DE ERRORES ====================

@app.errorhandler(404)
def not_found(error):
    """Manejo de páginas no encontradas"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Manejo de errores internos"""
    logger.error(f"Error 500: {str(error)}")
    return jsonify({'error': 'Error interno del servidor'}), 500

# ==================== EJECUCIÓN ====================

if __name__ == '__main__':
    # Crear directorio de logs si no existe
    os.makedirs('logs', exist_ok=True)
    
    # ✓ CARGAR MODELO ML UNA SOLA VEZ al iniciar la aplicación
    logger.info("=" * 60)
    logger.info("INICIALIZANDO APLICACIÓN")
    logger.info("=" * 60)
    load_ml_model()
    
    # ✓ CARGAR ORQUESTADOR CONVERSACIONAL
    load_orchestrator()
    
    # Configuración del servidor
    host = os.getenv('HOST', '127.0.0.1')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False') == 'True'
    
    logger.info(f"Iniciando servidor en http://{host}:{port}")
    logger.info(f"Modo debug: {debug}")
    logger.info("=" * 60)
    
    app.run(host=host, port=port, debug=debug)
