"""
Sistema de autenticación SIMULADO (en memoria)
Roles: 'admin' y 'user'
SIN conexión a base de datos - todo en sesión
"""

from typing import Dict, Optional, Tuple
import secrets
from datetime import datetime, timedelta

# Simulación en memoria
MOCK_USERS = {
    'admin@boti.com': {
        'password': 'admin123',
        'username': 'admin',
        'role': 'admin',
        'name': 'Administrador BOTI'
    },
    'user@boti.com': {
        'password': 'user123',
        'username': 'user1',
        'role': 'user',
        'name': 'Usuario Educativo'
    },
    'user2@boti.com': {
        'password': 'user123',
        'username': 'user2',
        'role': 'user',
        'name': 'María Rodríguez'
    }
}

# Sesiones activas (en memoria)
ACTIVE_SESSIONS = {}

# Consentimientos (en memoria)
USER_CONSENTS = {}


class MockAuthService:
    """Servicio de autenticación simulado"""
    
    @staticmethod
    def register_user(email: str, username: str, password: str, 
                     name: str) -> Dict:
        """Registrar nuevo usuario (simulado)"""
        
        if email in MOCK_USERS:
            return {'success': False, 'error': 'Email ya existe'}
        
        if any(u['username'] == username for u in MOCK_USERS.values()):
            return {'success': False, 'error': 'Username ya existe'}
        
        # Agregar usuario a memoria
        MOCK_USERS[email] = {
            'password': password,
            'username': username,
            'role': 'user',
            'name': name,
            'created_at': datetime.now().isoformat()
        }
        
        return {
            'success': True,
            'message': f'✓ Usuario {username} registrado exitosamente',
            'user': {
                'email': email,
                'username': username,
                'role': 'user'
            }
        }
    
    @staticmethod
    def login(email: str, password: str, 
             ip_address: str = '127.0.0.1') -> Dict:
        """Autenticar usuario y crear sesión"""
        
        if email not in MOCK_USERS:
            return {'success': False, 'error': 'Usuario no encontrado'}
        
        user = MOCK_USERS[email]
        
        if user['password'] != password:
            return {'success': False, 'error': 'Contraseña incorrecta'}
        
        # Crear sesión
        session_token = secrets.token_urlsafe(32)
        
        ACTIVE_SESSIONS[session_token] = {
            'user_id': email,
            'email': email,
            'username': user['username'],
            'role': user['role'],
            'name': user['name'],
            'login_at': datetime.now().isoformat(),
            'ip': ip_address,
            'expires_at': (datetime.now() + timedelta(days=7)).isoformat()
        }
        
        return {
            'success': True,
            'session_token': session_token,
            'user': {
                'email': email,
                'username': user['username'],
                'role': user['role'],
                'name': user['name']
            },
            'message': f'✓ Bienvenido {user["name"]}'
        }
    
    @staticmethod
    def verify_session(session_token: str) -> Optional[Dict]:
        """Verificar sesión válida"""
        
        if session_token not in ACTIVE_SESSIONS:
            return None
        
        session = ACTIVE_SESSIONS[session_token]
        
        # Verificar expiración
        expires = datetime.fromisoformat(session['expires_at'])
        if datetime.now() > expires:
            del ACTIVE_SESSIONS[session_token]
            return None
        
        return session
    
    @staticmethod
    def logout(session_token: str) -> Dict:
        """Cerrar sesión"""
        
        if session_token in ACTIVE_SESSIONS:
            user_info = ACTIVE_SESSIONS[session_token]
            del ACTIVE_SESSIONS[session_token]
            
            return {
                'success': True,
                'message': f'✓ Sesión cerrada'
            }
        
        return {'success': False, 'error': 'Sesión no encontrada'}
    
    @staticmethod
    def get_all_users() -> list:
        """Obtener lista de todos los usuarios (solo admin)"""
        
        users = []
        for email, user_data in MOCK_USERS.items():
            users.append({
                'email': email,
                'username': user_data['username'],
                'role': user_data['role'],
                'name': user_data['name'],
                'created_at': user_data.get('created_at', 'N/A')
            })
        
        return users
    
    @staticmethod
    def save_consent(email: str, consent_items: Dict, 
                    ip_address: str = '127.0.0.1') -> Dict:
        """Guardar consentimiento LSRPD del usuario"""
        
        # Validar items obligatorios
        if not consent_items.get('datos_personales'):
            return {
                'success': False,
                'error': 'Debes aceptar el tratamiento de datos personales'
            }
        
        if not consent_items.get('menores'):
            return {
                'success': False,
                'error': 'Debes confirmar tu mayoría de edad'
            }
        
        USER_CONSENTS[email] = {
            'items': consent_items,
            'saved_at': datetime.now().isoformat(),
            'ip_address': ip_address,
            'policy_version': '2.0-LSRPD'
        }
        
        return {
            'success': True,
            'message': '✓ Consentimiento registrado conforme a LSRPD 1581/2016'
        }
    
    @staticmethod
    def get_user_consent(email: str) -> Optional[Dict]:
        """Obtener consentimiento del usuario"""
        
        return USER_CONSENTS.get(email)


if __name__ == '__main__':
    print("="*80)
    print("🔐 SISTEMA DE AUTENTICACIÓN SIMULADO")
    print("="*80)
    
    auth = MockAuthService()
    
    # Prueba: Login
    print("\n1️⃣ Login como Admin...")
    result = auth.login('admin@boti.com', 'admin123')
    print(f"   {result['message']}")
    admin_token = result.get('session_token')
    
    # Prueba: Verificar sesión
    print("\n2️⃣ Verificando sesión...")
    session = auth.verify_session(admin_token)
    if session:
        print(f"   ✓ Sesión válida: {session['name']} ({session['role']})")
    
    # Prueba: Registro
    print("\n3️⃣ Registrando nuevo usuario...")
    result = auth.register_user('newuser@boti.com', 'newuser', 'pass123', 'Juan Pérez')
    print(f"   {result['message']}")
    
    # Prueba: Login usuario
    print("\n4️⃣ Login como usuario...")
    result = auth.login('newuser@boti.com', 'pass123')
    user_token = result.get('session_token')
    print(f"   {result['message']}")
    
    # Prueba: Consentimiento
    print("\n5️⃣ Registrando consentimiento LSRPD...")
    consent = auth.save_consent('newuser@boti.com', {
        'datos_personales': True,
        'menores': True,
        'tratamiento_anonimizado': True,
        'reportes_anonimizados': True,
        'comparticion_sponsors': False
    })
    print(f"   {consent['message']}")
    
    # Prueba: Obtener usuarios
    print("\n6️⃣ Listado de usuarios (simulado):")
    users = auth.get_all_users()
    for user in users:
        print(f"   • {user['username']} ({user['role']}) - {user['name']}")
    
    print("\n" + "="*80)
