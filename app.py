"""
Aplicación principal del Chatbot de Apoyo para Víctimas
Aplicación monolítica con Flask que integra frontend y backend
"""
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from dotenv import load_dotenv
import os
import logging
from datetime import datetime

# Cargar variables de entorno
load_dotenv()

# Importar módulos propios (se crearán después)
# from src.chatbot.bot import ChatBot
# from src.api.routes import api_blueprint

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

# Inicializar el chatbot (comentado hasta crear la clase)
# chatbot = ChatBot()

# ==================== RUTAS DEL FRONTEND ====================

@app.route('/')
def index():
    """Página principal del chat"""
    return render_template('index.html')

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
        "session_id": "id-opcional-de-sesion"
    }
    
    Response JSON:
    {
        "response": "respuesta del bot",
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
        
        if not user_message:
            return jsonify({'error': 'Mensaje vacío'}), 400
        
        logger.info(f"Mensaje recibido: {user_message[:50]}...")
        
        # TODO: Procesar con el chatbot real
        # result = chatbot.process_message(user_message, session_id)
        
        # Respuesta temporal de ejemplo
        response = {
            'response': 'Gracias por escribir. Estoy aquí para ayudarte. ¿Puedes contarme más sobre tu situación?',
            'category': 'unknown',
            'urgency': 'low',
            'resources': [],
            'timestamp': datetime.now().isoformat()
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
    
    # Configuración del servidor
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'True') == 'True'
    
    logger.info(f"Iniciando servidor en http://{host}:{port}")
    logger.info(f"Modo debug: {debug}")
    
    app.run(host=host, port=port, debug=debug)
