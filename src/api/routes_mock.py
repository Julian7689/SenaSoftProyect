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
    # Si se solicita el bot script simple, usarlo para respuestas deterministas
    use_simple = bool(data.get('simple_script', False))
    if use_simple:
        from src.chatbot.simple_script_bot import SimpleScriptBot
        orchestrator = SimpleScriptBot()
    else:
        from src.chatbot.chatbot_orchestrator import ChatbotOrchestrator
        orchestrator = ChatbotOrchestrator()

    # Cargar historial previo de la conversación en la memoria del orchestrator
    try:
        history = _conversation_store.get_conversation_history(
            user_email=user_info['email'],
            conv_id=conv_id
        )
        # conversation_history returns list of messages dicts
        orchestrator.conversation_memory.load_from_store(history)
    except Exception:
        # Si falla cargar el historial, continuar sin memoria previa
        pass

    # Pasar correo y conv_id para que el bot simple mantenga estado
    try:
        chat_result = orchestrator.process_message(user_message, user_email=user_info['email'], conv_id=conv_id)
    except TypeError:
        # Orchestrator antiguo no acepta esos parámetros
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
        # Guardar región en el contexto del store
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
    
    # Intentar alimentar las gráficas desde el dataset CSV sintético
    import csv
    from datetime import datetime
    from pathlib import Path

    csv_path = Path('PROYECTO SIUUU/data/raw/synthetic_education_dataset.csv')

    if not csv_path.exists():
        # Fallback: mantener comportamiento simulado si no se encuentra el CSV
        from datetime import datetime, timedelta
        import random
        data = {
            'timestamp': datetime.now().isoformat(),
            'total_users': 0,
            'total_conversations': 0,
            'children_connected': 0,
            'active_sponsors': 0,
            'regions_covered': 0,
            'total_consents': 0,
            'users_by_region': {},
            'admin_count': 0,
            'user_count': 0,
            'latest_users': [],
            'consent_rate': 0,
            'avg_messages_per_conversation': 0,
            'subsidy_coverage': 0,
            'user_satisfaction': 'N/A'
        }
        return jsonify({'success': True, 'data': data}), 200

    # Lista de regiones sintéticas para asignar filas
    regions = [
        'Bogotá', 'Antioquia', 'Magdalena', 'Atlántico', 'Córdoba',
        'Cundinamarca', 'Tolima', 'Cauca', 'Nariño', 'Huila', 'Meta',
        'Bolívar', 'Sucre', 'Norte de Santander', 'Santander'
    ]

    users_by_region = {r: 0 for r in regions}
    total_rows = 0
    acceso_count = 0
    # Collect sample rows to create latest_users
    latest_users = []

    try:
        with open(csv_path, newline='', encoding='utf-8') as fh:
            reader = csv.DictReader(fh)
            for i, row in enumerate(reader):
                total_rows += 1
                # Parse acceso_a_internet (expect 0/1)
                acceso = int(float(row.get('acceso_a_internet', 0))) if row.get('acceso_a_internet') not in (None, '') else 0
                if acceso == 1:
                    acceso_count += 1

                # Assign region round-robin to have distributed buckets
                region = regions[i % len(regions)]
                users_by_region[region] = users_by_region.get(region, 0) + 1

                # Build a synthetic user record for a small sample
                if len(latest_users) < 8:
                    username = f'user_{i+1}'
                    email = f'user_{i+1}@example.com'
                    role = 'admin' if (i % 50 == 0) else 'user'
                    consent = True if acceso == 1 else False
                    latest_users.append({
                        'username': username,
                        'email': email,
                        'role': role,
                        'conversation_count': (i % 6),
                        'consent': consent
                    })

        total_users = total_rows
        total_conversations = int(total_users * 0.35)
        children_connected = acceso_count
        active_sponsors = 3
        regions_covered = len([r for r, v in users_by_region.items() if v > 0])
        total_consents = sum(1 for u in latest_users if u.get('consent'))
        admin_count = sum(1 for u in latest_users if u.get('role') == 'admin')
        user_count = max(0, total_users - admin_count)
        consent_rate = int((acceso_count / total_users) * 100) if total_users else 0
        avg_messages_per_conversation = round((total_users * 2.3) / max(1, total_conversations), 2)
        subsidy_coverage = int((acceso_count / total_users) * 100) if total_users else 0
        user_satisfaction = f"{round(7.5 + (consent_rate/50),1)}/10"

        # Calcular estadísticas del dataset para gráficas adicionales
        # Re-lectura ligera para obtener columnas numéricas necesarias
        puntajes = []
        coberturas = []
        sample_scatter = []
        max_scatter = 1000
        with open(csv_path, newline='', encoding='utf-8') as fh2:
            reader2 = csv.DictReader(fh2)
            for idx, r in enumerate(reader2):
                try:
                    p = float(r.get('puntaje_pruebas') or 0)
                    c4 = float(r.get('cobertura_4G') or 0)
                except Exception:
                    continue
                puntajes.append(p)
                coberturas.append(c4)
                if len(sample_scatter) < max_scatter:
                    sample_scatter.append({'x': c4, 'y': p})

        # Histogram simple sin numpy
        hist_bins = 10
        puntaje_min = min(puntajes) if puntajes else 0
        puntaje_max = max(puntajes) if puntajes else 0
        bin_width = (puntaje_max - puntaje_min) / hist_bins if puntaje_max > puntaje_min else 1
        bins = []
        counts = [0] * hist_bins
        for i in range(hist_bins):
            start = puntaje_min + i * bin_width
            end = start + bin_width
            bins.append(f"{round(start,1)}-{round(end,1)}")

        for val in puntajes:
            if bin_width <= 0:
                counts[0] += 1
            else:
                idx_bin = int((val - puntaje_min) / bin_width)
                if idx_bin == hist_bins:
                    idx_bin = hist_bins - 1
                counts[idx_bin] += 1

        avg_puntaje = round(sum(puntajes) / len(puntajes), 2) if puntajes else 0
        avg_cobertura = round(sum(coberturas) / len(coberturas), 2) if coberturas else 0


        data = {
            'timestamp': datetime.now().isoformat(),
            'total_users': total_users,
            'total_conversations': total_conversations,
            'children_connected': children_connected,
            'active_sponsors': active_sponsors,
            'regions_covered': regions_covered,
            'total_consents': total_consents,
            'users_by_region': users_by_region,
            'admin_count': admin_count,
            'user_count': user_count,
            'latest_users': latest_users,
            'consent_rate': consent_rate,
            'avg_messages_per_conversation': avg_messages_per_conversation,
            'subsidy_coverage': subsidy_coverage,
            'user_satisfaction': user_satisfaction
        }

        # Agregar estadísticas del dataset
        data['dataset_stats'] = {
            'puntaje_hist': {'bins': bins, 'counts': counts},
            'scatter_sample': sample_scatter,
            'avg_puntaje': avg_puntaje,
            'avg_cobertura_4g': avg_cobertura
        }

        return jsonify({'success': True, 'data': data}), 200

    except Exception as e:
        # Si hay cualquier fallo al leer el CSV, devolvemos datos simulados mínimos
        from datetime import datetime
        data = {
            'timestamp': datetime.now().isoformat(),
            'total_users': 0,
            'total_conversations': 0,
            'children_connected': 0,
            'active_sponsors': 0,
            'regions_covered': 0,
            'total_consents': 0,
            'users_by_region': {},
            'admin_count': 0,
            'user_count': 0,
            'latest_users': [],
            'consent_rate': 0,
            'avg_messages_per_conversation': 0,
            'subsidy_coverage': 0,
            'user_satisfaction': 'N/A',
            'error': str(e)
        }
        return jsonify({'success': True, 'data': data}), 200


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
