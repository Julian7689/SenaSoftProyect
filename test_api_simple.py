"""
Script simple de prueba del API
Sin dependencias externas, solo usando urllib
"""

import urllib.request
import json
import time

API_URL = "http://localhost:5000/api/message"

test_messages = [
    "Hola",
    "Tengo problemas en Bogotá",
    "¿Hablas de educación?",
]

print("=" * 80)
print("PRUEBA DEL API DEL CHATBOT")
print("=" * 80)

for i, message in enumerate(test_messages, 1):
    print(f"\n[PRUEBA {i}] Mensaje: '{message}'")
    print("-" * 80)
    
    try:
        # Preparar datos
        data = json.dumps({
            "message": message,
            "session_id": f"test_{i}"
        }).encode('utf-8')
        
        # Hacer request
        req = urllib.request.Request(
            API_URL,
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            print(f"✓ Respuesta: {result.get('response')}")
            print(f"✓ Intención: {result.get('intent')}")
            print(f"✓ Región: {result.get('entities', {}).get('region', 'Ninguna')}")
            print(f"✓ Usando orquestador: {result.get('using_orchestrator', False)}")
    
    except Exception as e:
        print(f"✗ Error: {str(e)}")
    
    time.sleep(0.5)

print("\n" + "=" * 80)
print("PRUEBA COMPLETADA")
print("=" * 80)
