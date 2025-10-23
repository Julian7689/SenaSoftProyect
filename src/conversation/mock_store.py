"""
Almacenamiento simulado de conversaciones (en memoria)
Múltiples conversaciones por usuario con contexto completo
"""

from typing import Dict, List, Optional
from datetime import datetime
import uuid

# Almacenamiento en memoria
CONVERSATIONS_STORAGE = {}  # {user_email: {conv_id: [...messages...]}}
CONTEXT_STORAGE = {}  # {user_email: {conv_id: context_dict}}


class MockConversationStore:
    """Gestor simulado de conversaciones"""
    
    @staticmethod
    def create_conversation(user_email: str, title: str = None, 
                           topic: str = None) -> Dict:
        """Crear nueva conversación"""
        
        if user_email not in CONVERSATIONS_STORAGE:
            CONVERSATIONS_STORAGE[user_email] = {}
            CONTEXT_STORAGE[user_email] = {}
        
        conv_id = str(uuid.uuid4())[:8]
        
        CONVERSATIONS_STORAGE[user_email][conv_id] = {
            'id': conv_id,
            'title': title or f'Chat {datetime.now().strftime("%Y-%m-%d %H:%M")}',
            'topic': topic,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'messages': []
        }
        
        CONTEXT_STORAGE[user_email][conv_id] = {
            'region': None,
            'problem': None,
            'keywords': [],
            'stage': 'initial'
        }
        
        return {
            'success': True,
            'conversation_id': conv_id,
            'message': '✓ Nueva conversación creada'
        }
    
    @staticmethod
    def add_message(user_email: str, conv_id: str, sender: str,
                   content: str, intent: str = None, 
                   entities: Dict = None) -> Dict:
        """Agregar mensaje a conversación"""
        
        if user_email not in CONVERSATIONS_STORAGE:
            return {'success': False, 'error': 'Usuario no tiene conversaciones'}
        
        if conv_id not in CONVERSATIONS_STORAGE[user_email]:
            return {'success': False, 'error': 'Conversación no encontrada'}
        
        message = {
            'id': len(CONVERSATIONS_STORAGE[user_email][conv_id]['messages']) + 1,
            'sender': sender,
            'content': content,
            'intent': intent,
            'entities': entities or {},
            'timestamp': datetime.now().isoformat()
        }
        
        CONVERSATIONS_STORAGE[user_email][conv_id]['messages'].append(message)
        CONVERSATIONS_STORAGE[user_email][conv_id]['updated_at'] = datetime.now().isoformat()
        
        return {
            'success': True,
            'message_id': message['id']
        }
    
    @staticmethod
    def get_conversation_history(user_email: str, conv_id: str, 
                                 limit: int = 100) -> List[Dict]:
        """Obtener historial de conversación"""
        
        if user_email not in CONVERSATIONS_STORAGE:
            return []
        
        if conv_id not in CONVERSATIONS_STORAGE[user_email]:
            return []
        
        messages = CONVERSATIONS_STORAGE[user_email][conv_id]['messages']
        return messages[-limit:]
    
    @staticmethod
    def get_user_conversations(user_email: str) -> List[Dict]:
        """Obtener lista de conversaciones del usuario"""
        
        if user_email not in CONVERSATIONS_STORAGE:
            return []
        
        convs = []
        for conv_id, conv_data in CONVERSATIONS_STORAGE[user_email].items():
            convs.append({
                'conversation_id': conv_id,
                'title': conv_data['title'],
                'topic': conv_data['topic'],
                'created_at': conv_data['created_at'],
                'updated_at': conv_data['updated_at'],
                'message_count': len(conv_data['messages'])
            })
        
        # Ordenar por fecha actualización (más reciente primero)
        return sorted(convs, key=lambda x: x['updated_at'], reverse=True)
    
    @staticmethod
    def set_context(user_email: str, conv_id: str, key: str, 
                   value: str) -> Dict:
        """Guardar variable de contexto"""
        
        if user_email not in CONTEXT_STORAGE:
            CONTEXT_STORAGE[user_email] = {}
        
        if conv_id not in CONTEXT_STORAGE[user_email]:
            CONTEXT_STORAGE[user_email][conv_id] = {}
        
        CONTEXT_STORAGE[user_email][conv_id][key] = value
        
        return {'success': True}
    
    @staticmethod
    def get_context(user_email: str, conv_id: str) -> Dict:
        """Obtener contexto de conversación"""
        
        if user_email not in CONTEXT_STORAGE:
            return {}
        
        return CONTEXT_STORAGE[user_email].get(conv_id, {})
    
    @staticmethod
    def delete_conversation(user_email: str, conv_id: str) -> Dict:
        """Eliminar conversación"""
        
        if user_email in CONVERSATIONS_STORAGE:
            if conv_id in CONVERSATIONS_STORAGE[user_email]:
                del CONVERSATIONS_STORAGE[user_email][conv_id]
                if conv_id in CONTEXT_STORAGE.get(user_email, {}):
                    del CONTEXT_STORAGE[user_email][conv_id]
                
                return {'success': True, 'message': '✓ Conversación eliminada'}
        
        return {'success': False, 'error': 'Conversación no encontrada'}


if __name__ == '__main__':
    print("="*80)
    print("💬 ALMACENAMIENTO SIMULADO DE CONVERSACIONES")
    print("="*80)
    
    store = MockConversationStore()
    
    # Prueba: Crear conversación
    print("\n1️⃣ Creando conversación...")
    result = store.create_conversation('user@boti.com', 'Mi primer chat')
    conv_id = result['conversation_id']
    print(f"   {result['message']} (ID: {conv_id})")
    
    # Prueba: Agregar mensajes
    print("\n2️⃣ Agregando mensajes...")
    
    store.add_message('user@boti.com', conv_id, 'user', 
                     'Hola, necesito ayuda con conectividad')
    print("   ✓ Usuario: 'Hola, necesito ayuda con conectividad'")
    
    store.add_message('user@boti.com', conv_id, 'bot',
                     'Claro, estoy aquí para ayudarte. ¿De qué región eres?')
    print("   ✓ Bot: 'Claro, estoy aquí para ayudarte. ¿De qué región eres?'")
    
    store.add_message('user@boti.com', conv_id, 'user', 'Soy de Bogotá')
    print("   ✓ Usuario: 'Soy de Bogotá'")
    
    # Prueba: Guardar contexto
    print("\n3️⃣ Guardando contexto...")
    store.set_context('user@boti.com', conv_id, 'region', 'Bogotá')
    store.set_context('user@boti.com', conv_id, 'problem', 'conectividad')
    print("   ✓ Contexto guardado (región: Bogotá, problema: conectividad)")
    
    # Prueba: Obtener historial
    print("\n4️⃣ Historial de conversación:")
    messages = store.get_conversation_history('user@boti.com', conv_id)
    for msg in messages:
        sender = "👤 TÚ" if msg['sender'] == 'user' else "🤖 BOTI"
        print(f"   {sender}: {msg['content']}")
    
    # Prueba: Crear más conversaciones
    print("\n5️⃣ Creando más conversaciones...")
    result2 = store.create_conversation('user@boti.com', 'Duda sobre educación', 'educacion')
    conv_id2 = result2['conversation_id']
    print(f"   ✓ Conversación 2 creada (ID: {conv_id2})")
    
    store.add_message('user@boti.com', conv_id2, 'user', '¿Cómo mejoro educación en mi región?')
    print("   ✓ Mensaje agregado")
    
    # Prueba: Obtener todas las conversaciones
    print("\n6️⃣ Conversaciones del usuario:")
    convs = store.get_user_conversations('user@boti.com')
    for i, conv in enumerate(convs, 1):
        print(f"   {i}. {conv['title']}")
        print(f"      ID: {conv['conversation_id']}")
        print(f"      Mensajes: {conv['message_count']}")
        print(f"      Actualizado: {conv['updated_at'][:10]}")
    
    print("\n" + "="*80)
