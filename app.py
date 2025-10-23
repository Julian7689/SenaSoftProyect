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

from flask import Flask, render_template, request, jsonify, session, redirect
from flask_cors import CORS
from dotenv import load_dotenv
import os
import logging
from datetime import datetime
from typing import Dict, List
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
import traceback
import re

# Cargar variables de entorno
load_dotenv()

# Importar módulos propios
from src.chatbot.chatbot_orchestrator import ChatbotOrchestrator
from src.chatbot.enhanced_orchestrator import EnhancedChatbotOrchestrator  # ← NUEVO
from src.chatbot.conversation_memory import ConversationMemory
from src.auth.mock_auth import MockAuthService
from src.conversation.mock_store import MockConversationStore
from src.api.routes_mock import auth_bp, chat_bp, admin_bp

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

# ==================== INICIALIZAR SERVICIOS MOCK ====================
auth_service = MockAuthService()
conversation_store = MockConversationStore()

# ==================== ORQUESTADOR CONVERSACIONAL ====================
# Componente híbrido: NLP + Predicción + Generación
CHATBOT_ORCHESTRATOR = None
VAE_ENCODER = None
VAE_DECODER = None
VAE_SCALER = None
ORCHESTRATOR_READY = False

# Memoria de conversaciones por sesión (en memoria). Clave: session_id
CONVERSATION_MEMORIES = {}

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
    """Cargar el orquestador conversacional mejorado con Case Manager"""
    global CHATBOT_ORCHESTRATOR, VAE_ENCODER, VAE_DECODER, VAE_SCALER, ORCHESTRATOR_READY
    
    try:

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


        try:
            CHATBOT_ORCHESTRATOR = EnhancedChatbotOrchestrator(
                ml_model=ML_MODEL,
                vae_encoder=VAE_ENCODER,
                vae_decoder=VAE_DECODER,
                vae_scaler=VAE_SCALER,
                vae_features=MODEL_FEATURES
            )

            # Actualizar variables globales
            globals()['CHATBOT_ORCHESTRATOR'] = CHATBOT_ORCHESTRATOR
            globals()['ORCHESTRATOR_READY'] = True
            ORCHESTRATOR_READY = True
            logger.info("✓ EnhancedChatbotOrchestrator inicializado (con Case Manager)")
            logger.info("✅ Case Manager ACTIVO - Ahora detecta urgencia y busca soluciones")
            return True

        except Exception as e_inner:
            # Si falla la inicialización del Enhanced, hacer fallback a la versión base
            logger.warning(f"⚠️ No fue posible inicializar EnhancedChatbotOrchestrator: {str(e_inner)}")
            logger.debug(traceback.format_exc())

            try:
                # Crear un orquestador base (degradado) que aun permita NLP y predicciones ML
                CHATBOT_ORCHESTRATOR = ChatbotOrchestrator(
                    ml_model=ML_MODEL,
                    vae_encoder=None,
                    vae_decoder=None,
                    vae_scaler=None,
                    vae_features=MODEL_FEATURES
                )

                # Marcar como degradado para que el código pueda saberlo
                setattr(CHATBOT_ORCHESTRATOR, 'degraded', True)

                globals()['CHATBOT_ORCHESTRATOR'] = CHATBOT_ORCHESTRATOR
                globals()['ORCHESTRATOR_READY'] = True
                ORCHESTRATOR_READY = True
                logger.warning("⚠️ Orquestador inicializado en modo DEGRADADO (sin Case Manager / VAE)")
                return True

            except Exception as e_fallback:
                logger.error(f"✗ Error inicializando orquestador fallback: {str(e_fallback)}")
                logger.debug(traceback.format_exc())
                ORCHESTRATOR_READY = False
                globals()['CHATBOT_ORCHESTRATOR'] = None
                return False

    except Exception as e:
        logger.error(f"✗ Error inesperado inicializando orquestador: {str(e)}")
        logger.debug(traceback.format_exc())
        ORCHESTRATOR_READY = False
        globals()['CHATBOT_ORCHESTRATOR'] = None
        return False

# ==================== RUTAS DEL FRONTEND ====================

@app.route('/')
def index():
    """Redirigir a login si no hay sesión"""
    return redirect('/auth/login')

@app.route('/auth/login')
def login():
    """Página de login de usuarios"""
    return render_template('auth/login.html')

@app.route('/user/consent')
def consent():
    """Página de consentimiento LSRPD (obligatorio antes del chat)"""
    return render_template('user/consent.html')

@app.route('/user/chat')
def user_chat():
    """Página de chat para usuarios"""
    return render_template('user/chat.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    """Panel de administración para admins"""
    return render_template('admin/dashboard.html')

@app.route('/info')
def info():
    """Página de información sobre recursos"""
    return render_template('info.html')
# ==================== API ENDPOINTS ====================
# ==================== API ENDPOINTS ====================

@app.route('/api/message', methods=['POST'])
def send_message():
    """
    Endpoint mejorado para recibir mensajes Y gestionar casos sociales
    
    Request JSON:
    {
        "message": "texto del mensaje",
        "session_id": "id-opcional-de-sesion",
        "conversation_history": [...]  # histórico de conversación
    }
    
    Response JSON:
    {
        "response": "respuesta del bot",
        "case_id": "CASE_... o null",
        "urgency": "low|medium|high|critical",
        "solutions_offered": 0,
        "requires_action": false,
        "generated_by": "generative_model|case_manager"
    }
    """
    try:
        data = request.get_json() or {}
        user_message = data.get('message', '')
        session_id = data.get('session_id', None)
        # Normalizar session_id
        if not session_id:
            session_id = 'anonymous_' + (request.remote_addr or 'local')

        # Asegurar memoria por sesión
        memory = CONVERSATION_MEMORIES.get(session_id)
        if not memory:
            memory = ConversationMemory(user_id=session_id)
            CONVERSATION_MEMORIES[session_id] = memory

        # Asignar memoria al orquestador para mantener contexto entre llamadas
        if CHATBOT_ORCHESTRATOR:
            CHATBOT_ORCHESTRATOR.conversation_memory = memory
            CHATBOT_ORCHESTRATOR.response_generator.set_conversation_memory(memory)
            CHATBOT_ORCHESTRATOR.user_id = session_id
        conversation_history = data.get('conversation_history', [])
        user_data = data.get('user_data', {}) or {}
        consent = bool(data.get('consent', False))
        auto_activate_case = bool(data.get('auto_activate_case', False))

        if not user_message:
            return jsonify({'error': 'Mensaje vacío'}), 400

        logger.info(f"📨 Mensaje recibido: {user_message[:50]}...")

        if not ORCHESTRATOR_READY or CHATBOT_ORCHESTRATOR is None:
            logger.error("Orquestador no disponible al procesar mensaje")
            return jsonify({'error': 'Orquestador no disponible. Reinicia la aplicación.'}), 503

        try:
            logger.info("✅ Procesando mensaje con orquestador")
            # Si el cliente pide el bot simple, usarlo (modo determinista)
            if data.get('simple_script'):
                try:
                    from src.chatbot.simple_script_bot import SimpleScriptBot
                    bot = SimpleScriptBot()
                    conv_id = data.get('conversation_id')
                    email_like = session_id

                    # Persistir mensaje del usuario en conversation_store si conv_id está presente
                    if conv_id:
                        try:
                            conversation_store.add_message(user_email=email_like, conv_id=conv_id, sender='user', content=user_message, entities={})
                        except Exception:
                            pass

                    result = bot.process_message(user_message, user_email=email_like, conv_id=conv_id)

                    # Persistir respuesta del bot en conversation_store si conv_id está presente
                    if conv_id and isinstance(result, dict):
                        try:
                            conversation_store.add_message(user_email=email_like, conv_id=conv_id, sender='bot', content=result.get('response', ''), entities=result.get('entities', {}))
                        except Exception:
                            pass

                except Exception:
                    logger.exception('Error iniciando SimpleScriptBot, fallback a orquestador')
                    result = CHATBOT_ORCHESTRATOR.process_message(user_message, user_data)

            else:
                # Usar process_message_with_case_management si existe, sino process_message
                if hasattr(CHATBOT_ORCHESTRATOR, 'process_message_with_case_management'):
                    result = CHATBOT_ORCHESTRATOR.process_message_with_case_management(
                        user_message=user_message,
                        conversation_history=conversation_history
                    )
                else:
                    result = CHATBOT_ORCHESTRATOR.process_message(user_message, user_data)

            # Guardar interacción
            add_message_to_log(
                user_id=session_id or 'anonymous',
                role='user',
                content=user_message,
                metadata={'intent': result.get('intent')}
            )

            add_message_to_log(
                user_id=session_id or 'anonymous',
                role='assistant',
                content=result.get('response', ''),
                metadata={'generated_by': result.get('generated_by')}
            )

           
          
            region_confirmed = False
            try:
                region_confirmed = bool(getattr(memory, 'region_confirmed_by_user', False))
            except Exception:
                region_confirmed = False

            # Protección adicional: no ejecutar predict_and_plan hasta que la conversación
            # esté en una etapa adecuada (analyzing/proposing) o hasta que tengamos
            # el conjunto completo de features en user_data. Esto evita ofrecer
            # automáticamente soluciones antes de haber clarificado región/problema.
            can_run_predict = False
            try:
                convo_stage = getattr(memory, 'conversation_stage', None)
                # Ejecutar predict sólo en etapas de análisis o propuestas
                if convo_stage in ('analyzing', 'proposing'):
                    can_run_predict = True
            except Exception:
                convo_stage = None

            # También permitir ejecución si user_data contiene todas las features requeridas
            required_features = [
                'poblacion_total', 'porcentaje_rural', 'estrato_promedio',
                'tasa_pobreza', 'num_instituciones', 'computadores_por_estudiante',
                'salones_por_institucion', 'docentes_por_institucion',
                'cobertura_electrica', 'cobertura_4g',
                'dispositivos_promedio_hogar', 'tasa_aprobacion',
                'tasa_desercion', 'puntaje_pruebas'
            ]

            has_all_features = isinstance(user_data, dict) and all(f in user_data for f in required_features)

            if MODEL_LOADED and ML_MODEL is not None and isinstance(user_data, dict) and consent and (
                    (region_confirmed or bool(user_data.get('region'))) and (can_run_predict or has_all_features)):
                try:
                    plan = CHATBOT_ORCHESTRATOR.predict_and_plan(user_data)
                    if plan and plan.get('executed'):
                        result['prediction'] = {
                            'prediction': plan.get('prediction'),
                            'probability_with_access': plan.get('probability_with_access'),
                            'interpretation': plan.get('interpretation')
                        }
                        result['action_plan'] = plan.get('action_plan')
                        result['auto_activate_recommended'] = plan.get('auto_activate_recommended', False)

                        add_message_to_log(
                            user_id=session_id or 'anonymous',
                            role='assistant',
                            content='Se ofreció plan de acción basado en predicción ML',
                            metadata={'prediction': plan.get('prediction'), 'action_plan': plan.get('action_plan')}
                        )

                        # response_long
                        response_long = result.get('response', '') + '\n\nPlan de acción sugerido:\n'
                        for i, step in enumerate(plan.get('action_plan', []), start=1):
                            response_long += f"{i}. {step}\n"
                        result['response_long'] = response_long

                        
                        if (plan.get('prediction') == 0 and plan.get('auto_activate_recommended')
                                and auto_activate_case and consent
                                and isinstance(CHATBOT_ORCHESTRATOR, EnhancedChatbotOrchestrator)):
                            try:
                                cm = CHATBOT_ORCHESTRATOR.case_manager
                                problem_analysis = cm.analyze_conversation(
                                    user_id=session_id or 'anonymous',
                                    message=user_message,
                                    conversation_history=conversation_history
                                )
                                case = cm.create_case(session_id or 'anonymous', problem_analysis)
                                solutions = cm.find_matching_solutions(case)
                                activated = False
                                activation_info = None
                                if solutions:
                                    sol = solutions[0]
                                    activated = cm.activate_solution(case, sol)
                                    activation_info = {
                                        'solution_id': sol.solution_id,
                                        'solution_type': sol.type.value,
                                        'sponsor': sol.sponsor_name,
                                        'activated': activated
                                    }
                                result['case_activated'] = activated
                                result['case_id'] = case.case_id
                                result['activated_solution'] = activation_info
                                add_message_to_log(
                                    user_id=session_id or 'anonymous',
                                    role='assistant',
                                    content=f"Caso {case.case_id} creado y activación: {activated}",
                                    metadata={'activation_info': activation_info}
                                )
                            except Exception:
                                logger.exception('Error al intentar auto-activar caso')

                except Exception:
                    logger.exception('Error al ejecutar predict_and_plan')

            sanitized = sanitize_result_no_emoji(result)
            return jsonify(sanitized), 200

        except AttributeError as ae:
            logger.warning(f"Fallo por AttributeError en orquestador: {ae}")
            logger.debug(traceback.format_exc())
            try:
                base_result = CHATBOT_ORCHESTRATOR.process_message(user_message, user_data)
                add_message_to_log(
                    user_id=session_id or 'anonymous',
                    role='assistant',
                    content=base_result.get('response', ''),
                    metadata={'generated_by': 'fallback_base'}
                )
                return jsonify(base_result), 200
            except Exception:
                logger.exception('Fallback base falló')
                return jsonify({'error': 'Error procesando mensaje'}), 500

        except Exception as e:
            logger.exception(f"Error procesando con orquestador: {e}")
            return jsonify({'error': 'Error interno del servidor'}), 500

    except Exception as e:
        logger.exception(f"Error procesando mensaje: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500
        
    except Exception as e:
        logger.error(f" Error procesando mensaje: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500


def add_message_to_log(user_id: str, role: str, content: str, metadata: Dict = None):
    """Guardar mensaje en log (expandible a BD real)"""
    try:
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'role': role,
            'content': content[:200],  # Truncar para logging
            'metadata': metadata or {}
        }
        logger.info(f"{role.upper()}: {log_entry}")
    except Exception as e:
        logger.warning(f"Error logging message: {e}")


### Utilities: emoji stripping and sanitization #################################
emoji_pattern = re.compile('[\U0001F600-\U0001F64F'  # emoticons
                           '\U0001F300-\U0001F5FF'  # symbols & pictographs
                           '\U0001F680-\U0001F6FF'  # transport & map
                           '\U0001F1E0-\U0001F1FF'  # flags
                           '\u2600-\u26FF'          # misc symbols
                           '\u2700-\u27BF]+', flags=re.UNICODE)

def strip_emojis(text: str) -> str:
    if not isinstance(text, str):
        return text
    return emoji_pattern.sub('', text).strip()

def sanitize_result_no_emoji(result: Dict) -> Dict:
    """Remove emojis from textual fields to produce a cleaner message for UI."""
    if not isinstance(result, dict):
        return result
    if 'response' in result:
        result['response'] = strip_emojis(result.get('response', ''))
    if 'response_long' in result:
        result['response_long'] = strip_emojis(result.get('response_long', ''))
    if 'action_plan' in result and isinstance(result['action_plan'], list):
        result['action_plan'] = [strip_emojis(s) for s in result['action_plan']]
    if 'improvements' in result and isinstance(result['improvements'], dict):
        for p in result['improvements'].get('proposals', []):
            if isinstance(p, dict) and 'summary' in p:
                p['summary'] = strip_emojis(p.get('summary', ''))
    return result

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

# ==================== ENDPOINTS DE GESTIÓN DE CASOS (NUEVO) ====================

@app.route('/api/case/<case_id>/activate', methods=['POST'])
def activate_case(case_id):
    """
    Endpoint para activar una solución de caso
    
    Request JSON:
    {
        "solution_index": 0,  # opcional, default 0
        "user_data": {
            "phone": "310-...",
            "location": {...},
            "consent": true
        }
    }
    """
    try:
        if not ORCHESTRATOR_READY or not isinstance(CHATBOT_ORCHESTRATOR, EnhancedChatbotOrchestrator):
            return jsonify({'error': 'Case Manager no disponible'}), 503
        
        data = request.get_json() or {}
        solution_index = data.get('solution_index', 0)
        user_data = data.get('user_data', {})
        
        result = CHATBOT_ORCHESTRATOR.activate_case_solution(
            case_id=case_id,
            user_data=user_data,
            solution_index=solution_index
        )
        
        if result['success']:
            logger.info(f" Caso {case_id} activado con éxito")
            return jsonify(result), 200
        else:
            logger.warning(f" Error activando caso {case_id}")
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f" Error en activate_case: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/case/<case_id>/status', methods=['GET'])
def get_case_status(case_id):
    """Obtener estado de un caso"""
    try:
        if not ORCHESTRATOR_READY or not isinstance(CHATBOT_ORCHESTRATOR, EnhancedChatbotOrchestrator):
            return jsonify({'error': 'Case Manager no disponible'}), 503
        
        status = CHATBOT_ORCHESTRATOR.get_case_status(case_id)
        
        if 'error' in status:
            return jsonify(status), 404
        
        return jsonify(status), 200
    
    except Exception as e:
        logger.error(f"Error obteniendo estado del caso: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/user/<user_id>/cases', methods=['GET'])
def get_user_cases(user_id):
    """Obtener todos los casos de un usuario"""
    try:
        if not ORCHESTRATOR_READY or not isinstance(CHATBOT_ORCHESTRATOR, EnhancedChatbotOrchestrator):
            return jsonify({'error': 'Case Manager no disponible'}), 503
        
        cases = CHATBOT_ORCHESTRATOR.get_user_cases(user_id)
        
        return jsonify({
            'user_id': user_id,
            'total_cases': len(cases),
            'cases': cases
        }), 200
    
    except Exception as e:
        logger.error(f"Error obteniendo casos del usuario: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/case/<case_id>/impact', methods=['GET'])
def get_case_impact(case_id):
    """Obtener reporte de impacto de un caso"""
    try:
        if not ORCHESTRATOR_READY or not isinstance(CHATBOT_ORCHESTRATOR, EnhancedChatbotOrchestrator):
            return jsonify({'error': 'Case Manager no disponible'}), 503
        
        report = CHATBOT_ORCHESTRATOR.generate_impact_report(case_id)
        
        if 'error' in report:
            return jsonify(report), 404
        
        return jsonify(report), 200
    
    except Exception as e:
        logger.error(f"Error generando reporte de impacto: {str(e)}")
        return jsonify({'error': str(e)}), 500


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

        if not MODEL_LOADED or ML_MODEL is None:
            return jsonify({
                'success': False,
                'error': 'Modelo ML no disponible. Reinicia la aplicación.'
            }), 503

        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No se enviaron datos'
            }), 400
        
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
            

            X_input = np.array([input_values]).reshape(1, -1)
            

            prediction = ML_MODEL.predict(X_input)[0]

            try:
                prediction_proba = ML_MODEL.predict_proba(X_input)[0]
                proba_list = prediction_proba.tolist()
            except:
                proba_list = [None, None]
            
            # Interpretación de la predicción
            interpretation_map = {
                0: "🔴Sin acceso a internet - Se requieren recursos de conectividad",
                1: "Con acceso a internet - Buena cobertura digital"
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



@app.route('/api/chat-intelligent', methods=['POST'])
def chat_intelligent():
   
    try:
        if not ORCHESTRATOR_READY or CHATBOT_ORCHESTRATOR is None:
            return jsonify({
                'success': False,
                'error': 'Orquestador no disponible. Reinicia la aplicación.'
            }), 503
        
        data = request.get_json() or {}
        user_message = data.get('message', '')
        user_data = data.get('user_data', {}) or {}
        consent = bool(data.get('consent', False))

        if not user_message:
            return jsonify({'error': 'Mensaje vacío'}), 400

        # Procesar mensaje con orquestador
        result = CHATBOT_ORCHESTRATOR.process_message(user_message, user_data)

        # Ejecutar predicción y plan si hay consentimiento y modelo
        try:
            if MODEL_LOADED and ML_MODEL is not None and consent and isinstance(user_data, dict):
                plan = CHATBOT_ORCHESTRATOR.predict_and_plan(user_data)
                if plan and plan.get('executed'):
                    result['prediction'] = {
                        'prediction': plan.get('prediction'),
                        'probability_with_access': plan.get('probability_with_access')
                    }
                    result['action_plan'] = plan.get('action_plan')

                    # Trazabilidad
                    add_message_to_log(
                        user_id='system',
                        role='assistant',
                        content='Plan de acción generado desde chat_intelligent',
                        metadata={'prediction': plan.get('prediction')}
                    )

                    # response_long
                    long_text = result.get('response', '') + '\n\nPlan de acción sugerido:\n'
                    for i, step in enumerate(plan.get('action_plan', []), start=1):
                        long_text += f"{i}. {step}\n"
                    result['response_long'] = long_text
        except Exception:
            logger.debug('Error ejecutando predict_and_plan en chat_intelligent', exc_info=True)

        sanitized = sanitize_result_no_emoji(result)
        return jsonify(sanitized), 200
    
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



@app.errorhandler(404)
def not_found(error):
    """Manejo de páginas no encontradas"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Manejo de errores internos"""
    logger.error(f"Error 500: {str(error)}")
    return jsonify({'error': 'Error interno del servidor'}), 500



if __name__ == '__main__':

    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(admin_bp)

    os.makedirs('logs', exist_ok=True)
    
    logger.info("=" * 60)
    logger.info("INICIALIZANDO APLICACIÓN")
    logger.info("=" * 60)
    load_ml_model()

    load_orchestrator()

    host = os.getenv('HOST', '127.0.0.1')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False') == 'True'
    
    logger.info(f"Iniciando servidor en http://{host}:{port}")
    logger.info(f"Modo debug: {debug}")
    logger.info("=" * 60)
    
    app.run(host=host, port=port, debug=debug)
