#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test para verificar que el bot mantiene contexto en conversaciones multi-turno
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.chatbot.chatbot_orchestrator import ChatbotOrchestrator

def test_conversation_context():
    """Test de conversación multi-turno con contexto"""
    
    print("\n" + "="*70)
    print("TEST DE CONTEXTO EN CONVERSACIONES MULTI-TURNO")
    print("="*70 + "\n")
    
    # Inicializar orquestador
    orchestrator = ChatbotOrchestrator()
    
    # Simular conversación del screenshot del usuario
    test_messages = [
        "Hola necesito ayuda en educación",
        "necesito que me ayudes a mejorar la conectividad en mi zona",
        "Bogotá",
        "no tengo internet porque acá es monte necesito estudiar",
        "¿qué puedo hacer para mejorar?"
    ]
    
    print("SIMULANDO CONVERSACIÓN MULTI-TURNO:\n")
    
    for i, user_msg in enumerate(test_messages, 1):
        print(f"\n{'─'*70}")
        print(f"[TURNO {i}] USUARIO: {user_msg}")
        print(f"{'─'*70}")
        
        # Procesar mensaje
        result = orchestrator.process_message(user_msg)
        
        # Mostrar análisis
        print(f"✓ Intención detectada: {result['intent']} (confianza: {result['intent_confidence']:.2%})")
        print(f"✓ Región extraída: {result['entities']['region'] or 'No especificada'}")
        print(f"✓ Keywords: {result['entities']['keywords']}")
        
        # Mostrar respuesta del bot
        print(f"\n🤖 BOT RESPONDE:")
        print(f"   {result['response']}")
        
        # Mostrar contexto guardado
        history = orchestrator.get_conversation_history()
        print(f"\n📝 HISTORIAL GUARDADO ({len(history)} mensajes):")
        if history:
            for msg in history:
                print(f"   - [{msg['intent']}] {msg['user_message'][:50]}...")
    
    print("\n" + "="*70)
    print("ANÁLISIS FINAL")
    print("="*70)
    
    # Exportar conversación completa
    export = orchestrator.export_conversation()
    print(f"\n✓ Región del usuario detectada: {export['user_region']}")
    print(f"✓ Total de mensajes procesados: {export['conversation_count']}")
    print(f"\n✓ RESULTADO: {'CONTEXTO MANTENIDO ✅' if export['user_region'] else 'CONTEXTO PERDIDO ❌'}")
    
    # Mostrar flujo de intenciones
    print(f"\n📊 FLUJO DE INTENCIONES EN CONVERSACIÓN:")
    for i, msg in enumerate(export['history'], 1):
        region_info = f" (región: {msg['entities']['region']})" if msg['entities']['region'] else ""
        print(f"   {i}. {msg['intent']}{region_info}")
    
    print("\n" + "="*70 + "\n")

if __name__ == '__main__':
    try:
        test_conversation_context()
        print("✅ Test completado exitosamente")
    except Exception as e:
        print(f"❌ Error en test: {str(e)}")
        import traceback
        traceback.print_exc()
