"""
Rutas API simuladas (SIN base de datos)
Maneja autenticación, consentimiento, chat y admin
"""

from flask import Blueprint, request, jsonify, session, render_template
from src.auth.mock_auth import MockAuthService
from src.conversation.mock_store import MockConversationStore

# Blueprints
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')
admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# Variables globales para almacenamiento
_auth_service = MockAuthService()
_conversation_store = MockConversationStore()

def get_token_from_request():
    """Extrae token del header Authorization o de la sesión"""
    # Primero intenta desde header Authorization: Bearer <token>
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header[7:]
    
    # Si no, intenta desde sesión
    return session.get('session_token')


# ==================== RUTAS DE AUTENTICACIÓN ====================

@auth_bp.route('/register', methods=['POST'])
def register():
    """Registrar nuevo usuario"""
    data = request.get_json()
    
    result = MockAuthService.register_user(
        email=data.get('email'),
        username=data.get('username'),
        password=data.get('password'),
        name=data.get('name')
    )
    
    return jsonify(result), 201 if result['success'] else 400


@auth_bp.route('/login', methods=['POST'])
def login():
    """Iniciar sesión"""
    data = request.get_json()
    
    result = MockAuthService.login(
        email=data.get('email'),
        password=data.get('password'),
        ip_address=request.remote_addr
    )
    
    if result['success']:
        # Guardar token en sesión
        session['session_token'] = result['session_token']
    
    return jsonify(result), 200 if result['success'] else 401


@auth_bp.route('/verify', methods=['GET'])
def verify_session():
    """Verificar sesión activa"""
    token = get_token_from_request()
    
    if not token:
        return jsonify({'success': False, 'error': 'No hay sesión activa'}), 401
    
    user_info = MockAuthService.verify_session(token)
    
    if user_info:
        return jsonify({'success': True, 'user': user_info}), 200
    else:
        session.clear()
        return jsonify({'success': False, 'error': 'Sesión expirada'}), 401


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Cerrar sesión"""
    token = get_token_from_request()
    
    if token:
        result = MockAuthService.logout(token)
        session.clear()
        return jsonify(result), 200
    
    return jsonify({'success': False, 'error': 'No hay sesión activa'}), 400


@auth_bp.route('/consent', methods=['POST'])
def save_consent():
    """Guardar consentimiento LSRPD"""
    data = request.get_json()
    token = get_token_from_request()
    
    if not token:
        return jsonify({'success': False, 'error': 'No autenticado'}), 401
    
    user_info = MockAuthService.verify_session(token)
    if not user_info:
        return jsonify({'success': False, 'error': 'Sesión inválida'}), 401
    
    result = MockAuthService.save_consent(
        email=user_info['email'],
        consent_items=data.get('items', {}),
        ip_address=request.remote_addr
    )
    
    return jsonify(result), 200 if result['success'] else 400


@auth_bp.route('/consent', methods=['GET'])
def get_consent():
    """Obtener consentimiento del usuario"""
    token = get_token_from_request()
    
    if not token:
        return jsonify({'success': False, 'error': 'No autenticado'}), 401
    
    user_info = MockAuthService.verify_session(token)
    if not user_info:
        return jsonify({'success': False, 'error': 'Sesión inválida'}), 401
    
    consent = MockAuthService.get_user_consent(user_info['email'])
    
    return jsonify({
        'success': True,
        'consent': consent
    }), 200


# ==================== RUTAS DE CHAT ====================

@chat_bp.route('/conversations', methods=['GET'])
def get_conversations():
    """Obtener conversaciones del usuario"""
    token = get_token_from_request()
    
    if not token:
        return jsonify({'success': False, 'error': 'No autenticado'}), 401
    
    user_info = MockAuthService.verify_session(token)
    if not user_info:
        return jsonify({'success': False, 'error': 'Sesión inválida'}), 401
    
    conversations = _conversation_store.get_user_conversations(user_info['email'])
    
    return jsonify({
        'success': True,
        'conversations': conversations
    }), 200


@chat_bp.route('/conversation/create', methods=['POST'])
def create_conversation():
    """Crear nueva conversación"""
    token = get_token_from_request()
    
    if not token:
        return jsonify({'success': False, 'error': 'No autenticado'}), 401
    
    user_info = MockAuthService.verify_session(token)
    if not user_info:
        return jsonify({'success': False, 'error': 'Sesión inválida'}), 401
    
    data = request.get_json()
    
    result = _conversation_store.create_conversation(
        user_email=user_info['email'],
        title=data.get('title'),
        topic=data.get('topic')
    )
    
    return jsonify(result), 201 if result['success'] else 400


@chat_bp.route('/conversation/<conv_id>/history', methods=['GET'])
def get_history(conv_id):
    """Obtener historial de conversación"""
    token = get_token_from_request()
    
    if not token:
        return jsonify({'success': False, 'error': 'No autenticado'}), 401
    
    user_info = MockAuthService.verify_session(token)
    if not user_info:
        return jsonify({'success': False, 'error': 'Sesión inválida'}), 401
    
    messages = _conversation_store.get_conversation_history(
        user_email=user_info['email'],
        conv_id=conv_id
    )
    
    return jsonify({
        'success': True,
        'messages': messages
    }), 200


@chat_bp.route('/conversation/<conv_id>/message', methods=['POST'])
def send_message(conv_id):
    """Enviar mensaje en conversación"""
    token = get_token_from_request()
    
    if not token:
        return jsonify({'success': False, 'error': 'No autenticado'}), 401
    
    user_info = MockAuthService.verify_session(token)
    if not user_info:
        return jsonify({'success': False, 'error': 'Sesión inválida'}), 401
    
    data = request.get_json()
    user_message = data.get('message')
    
    # Agregar mensaje del usuario
    _conversation_store.add_message(
        user_email=user_info['email'],
        conv_id=conv_id,
        sender='user',
        content=user_message,
        entities=data.get('entities', {})
    )
    
    # Simular respuesta del bot (con contexto)
    from src.chatbot.chatbot_orchestrator import ChatbotOrchestrator
    orchestrator = ChatbotOrchestrator()
    
    chat_result = orchestrator.process_message(user_message)
    
    bot_response = chat_result.get('response', '✓ Mensaje recibido')
    
    # Agregar respuesta del bot
    _conversation_store.add_message(
        user_email=user_info['email'],
        conv_id=conv_id,
        sender='bot',
        content=bot_response,
        intent=chat_result.get('intent'),
        entities=chat_result.get('entities', {})
    )
    
    # Guardar contexto
    if chat_result.get('entities', {}).get('region'):
        _conversation_store.set_context(
            user_info['email'], conv_id, 'region',
            chat_result['entities']['region']
        )
    
    return jsonify({
        'success': True,
        'bot_response': bot_response,
        'intent': chat_result.get('intent')
    }), 200


@chat_bp.route('/conversation/<conv_id>/delete', methods=['DELETE'])
def delete_conversation(conv_id):
    """Eliminar conversación"""
    token = get_token_from_request()
    
    if not token:
        return jsonify({'success': False, 'error': 'No autenticado'}), 401
    
    user_info = MockAuthService.verify_session(token)
    if not user_info:
        return jsonify({'success': False, 'error': 'Sesión inválida'}), 401
    
    result = _conversation_store.delete_conversation(
        user_email=user_info['email'],
        conv_id=conv_id
    )
    
    return jsonify(result), 200 if result['success'] else 400


# ==================== RUTAS ADMIN ====================

@admin_bp.route('/dashboard-data', methods=['GET'])
def get_dashboard_data():
    """Obtener datos del dashboard (solo admin)"""
    token = get_token_from_request()
    
    if not token:
        return jsonify({'success': False, 'error': 'No autenticado'}), 401
    
    user_info = MockAuthService.verify_session(token)
    if not user_info:
        return jsonify({'success': False, 'error': 'Sesión inválida'}), 401
    
    if user_info['role'] != 'admin':
        return jsonify({'success': False, 'error': 'No tienes permisos'}), 403
    
    # Datos simulados (en tiempo real)
    import random
    from datetime import datetime, timedelta
    
    data = {
        'timestamp': datetime.now().isoformat(),
        'metrics': {
            'usuarios_activos': random.randint(45, 120),
            'conversaciones_totales': random.randint(200, 500),
            'niños_conectados': random.randint(2000, 3500),
            'horas_educativas': random.randint(12000, 25000),
            'familias_acceso': random.randint(800, 1500),
            'gigas_distribuidos': random.randint(4000, 8000)
        },
        'regiones': {
            'Bogotá': {'usuarios': 45, 'conectados': 850},
            'Medellín': {'usuarios': 32, 'conectados': 620},
            'Cali': {'usuarios': 28, 'conectados': 480},
            'Barranquilla': {'usuarios': 15, 'conectados': 250},
            'Otros': {'usuarios': 30, 'conectados': 400}
        },
        'sponsors': [
            {
                'nombre': 'Claro',
                'zonas': 8,
                'beneficiados': 250,
                'gigas': 2500
            },
            {
                'nombre': 'Movistar',
                'zonas': 6,
                'beneficiados': 180,
                'gigas': 1800
            },
            {
                'nombre': 'Bancolombia',
                'zonas': 4,
                'beneficiados': 120,
                'gigas': 1000
            }
        ]
    }
    
    return jsonify({
        'success': True,
        'data': data
    }), 200


@admin_bp.route('/users', methods=['GET'])
def get_users():
    """Obtener lista de usuarios (solo admin)"""
    token = get_token_from_request()
    
    if not token:
        return jsonify({'success': False, 'error': 'No autenticado'}), 401
    
    user_info = MockAuthService.verify_session(token)
    if not user_info:
        return jsonify({'success': False, 'error': 'Sesión inválida'}), 401
    
    if user_info['role'] != 'admin':
        return jsonify({'success': False, 'error': 'No tienes permisos'}), 403
    
    users = MockAuthService.get_all_users()
    
    return jsonify({
        'success': True,
        'users': users
    }), 200
