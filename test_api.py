"""
Script de prueba del API del chatbot
Prueba diferentes tipos de mensajes para verificar que el orquestador está trabajando
"""

import requests
import json
import time

# Configuración
API_URL = "http://localhost:5000/api/message"

# Mensajes de prueba
test_messages = [
    "Hola",
    "¿Cómo estás?",
    "Tengo problemas de conectividad en Bogotá",
    "¿Puedes hacer una predicción?",
    "Necesito mejorar los indicadores de educación en Antioquia",
    "Habla sobre conectividad",
    "¿Qué información necesitas sobre educación?",
    "Adiós",
]

def test_api():
    print("=" * 80)
    print("PROBANDO API DEL CHATBOT BOTI")
    print("=" * 80)
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n[TEST {i}] Mensaje: {message}")
        print("-" * 80)
        
        try:
            # Hacer request
            response = requests.post(
                API_URL,
                json={
                    "message": message,
                    "session_id": f"test_session_{i}"
                }
            )
            
            # Verificar status
            if response.status_code == 200:
                data = response.json()
                
                print(f"✓ Status: {response.status_code}")
                print(f"✓ Respuesta: {data.get('response', 'N/A')}")
                print(f"✓ Intención detectada: {data.get('intent', 'N/A')}")
                print(f"✓ Confianza: {data.get('intent_confidence', 'N/A'):.2%}")
                print(f"✓ Región extraída: {data.get('entities', {}).get('region', 'Ninguna')}")
                print(f"✓ Usando orquestador: {data.get('using_orchestrator', False)}")
                
                if data.get('prediction'):
                    print(f"✓ Predicción: {data.get('prediction')}")
                
            else:
                print(f"✗ Error: {response.status_code}")
                print(f"✗ Respuesta: {response.text}")
        
        except Exception as e:
            print(f"✗ Error de conexión: {str(e)}")
        
        time.sleep(1)  # Esperar entre requests
    
    print("\n" + "=" * 80)
    print("PRUEBA COMPLETADA")
    print("=" * 80)

if __name__ == '__main__':
    test_api()
