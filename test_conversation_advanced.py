#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test avanzado: Valida que ConversationMemory mantiene contexto perfectamente
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from src.chatbot.conversation_memory import ConversationMemory
from src.chatbot.chatbot_orchestrator import ChatbotOrchestrator


def test_memory_persistence():
    """Prueba que la memoria rastrea región y no la olvida"""
    
    print("\n" + "="*80)
    print("TEST 1: PERSISTENCIA DE REGIÓN")
    print("="*80 + "\n")
    
    memory = ConversationMemory("test_user_1")
    
    # Mensaje 1: Saludar
    memory.add_message(
        user_message="Hola necesito ayuda",
        intent="saludar",
        confidence=0.95,
        entities={'region': None, 'keywords': ['ayuda']}
    )
    print("✓ M1: Usuario saluda")
    print(f"  Región después M1: {memory.confirmed_region}")
    
    # Mensaje 2: Menciona región
    memory.add_message(
        user_message="Soy de Bogotá",
        intent="region",
        confidence=0.99,
        entities={'region': 'Bogotá', 'keywords': []}
    )
    print("✓ M2: Usuario menciona Bogotá")
    print(f"  Región después M2: {memory.confirmed_region} ✅ GRABADA PERMANENTEMENTE")
    
    # Mensaje 3: No menciona región (pero sistema debe recordar)
    memory.add_message(
        user_message="Necesito conectividad",
        intent="conectividad",
        confidence=0.85,
        entities={'region': None, 'keywords': ['conectividad']}
    )
    print("✓ M3: Usuario habla de conectividad (sin mencionar región)")
    print(f"  Región después M3: {memory.confirmed_region} ✅ SE MANTIENE")
    
    # Mensaje 4: Más contexto
    memory.add_message(
        user_message="No tengo internet",
        intent="conectividad",
        confidence=0.88,
        entities={'region': None, 'keywords': ['internet']}
    )
    print("✓ M4: Usuario dice 'no tengo internet'")
    print(f"  Región después M4: {memory.confirmed_region} ✅ SIGUE SIENDO BOGOTÁ")
    
    # Verificación final
    context = memory.get_context_summary()
    print("\n📊 CONTEXTO FINAL:")
    print(f"  - Región confirmada: {context['confirmed_region']}")
    print(f"  - Problema principal: {context['primary_problem']}")
    print(f"  - Keywords acumuladas: {context['keywords']}")
    print(f"  - Etapa: {context['stage']}")
    print(f"  - Total mensajes: {context['message_count']}")
    
    assert context['confirmed_region'] == 'Bogotá', "❌ Región se perdió!"
    print("\n✅ TEST 1 PASÓ: Región se mantiene permanentemente\n")


def test_no_repeat_questions():
    """Prueba que no repite preguntas"""
    
    print("="*80)
    print("TEST 2: NO REPETIR PREGUNTAS")
    print("="*80 + "\n")
    
    memory = ConversationMemory("test_user_2")
    
    # Simular que el bot preguntó por región
    memory.add_message(
        user_message="¿Cuál es tu región?",
        intent="ayuda",
        confidence=0.8,
        entities={'region': None, 'keywords': []},
        is_question=True,
        question_topic='region'
    )
    print("✓ Bot preguntó: '¿Cuál es tu región?'")
    print(f"  Pregunta registrada en 'asked_about': {'region' in memory.asked_about}")
    
    # Usuario responde
    memory.add_message(
        user_message="Medellín",
        intent="region",
        confidence=0.99,
        entities={'region': 'Medellín', 'keywords': []}
    )
    print("✓ Usuario responde: 'Medellín'")
    
    # Verificar que NO deberíamos volver a preguntar
    should_ask_region = memory.should_ask_for_region()
    print(f"  ¿Deberíamos preguntar por región de nuevo? {should_ask_region}")
    
    assert should_ask_region == False, "❌ Error: debería NO preguntar por región"
    print("\n✅ TEST 2 PASÓ: No repite preguntas sobre región\n")


def test_problem_tracking():
    """Prueba que rastrea problema principal"""
    
    print("="*80)
    print("TEST 3: RASTREO DE PROBLEMA PRINCIPAL")
    print("="*80 + "\n")
    
    memory = ConversationMemory("test_user_3")
    
    # Usuario menciona conectividad
    memory.add_message(
        user_message="Tengo problemas de conectividad",
        intent="conectividad",
        confidence=0.92,
        entities={'region': None, 'keywords': ['conectividad', 'internet']}
    )
    print("✓ M1: Usuario menciona conectividad")
    print(f"  Problema principal: {memory.primary_problem} ✅")
    
    # Usuario menciona educación después
    memory.add_message(
        user_message="También necesito mejorar educación",
        intent="educacion",
        confidence=0.85,
        entities={'region': None, 'keywords': ['educación', 'escuela']}
    )
    print("✓ M2: Usuario también menciona educación")
    print(f"  Problema SIGUE siendo: {memory.primary_problem} ✅ (el primero es prioridad)")
    
    context = memory.get_context_summary()
    print(f"\n📊 Intenciones en secuencia: {context['intents_sequence']}")
    print(f"📊 Problema principal: {context['primary_problem']}")
    print(f"📊 Todas las keywords: {context['keywords']}")
    
    assert memory.primary_problem == 'conectividad', "❌ Problema principal se perdió"
    print("\n✅ TEST 3 PASÓ: Rastrea problema principal correctamente\n")


def test_full_conversation_flow():
    """Simula conversación completa como la del screenshot"""
    
    print("="*80)
    print("TEST 4: FLUJO COMPLETO DE CONVERSACIÓN")
    print("="*80 + "\n")
    
    orchestrator = ChatbotOrchestrator()
    
    messages = [
        ("Hola necesito ayuda en educación", "M1: Saludo + educación"),
        ("Necesito que me ayudes a mejorar la conectividad en mi zona", "M2: Conectividad"),
        ("Bogotá", "M3: Región"),
        ("No tengo internet porque acá es monte", "M4: Problema especifico"),
        ("¿Qué puedo hacer para mejorar?", "M5: Solicitar soluciones"),
    ]
    
    for msg, label in messages:
        print(f"\n{label}")
        print(f"  Usuario: {msg}")
        
        result = orchestrator.process_message(msg)
        
        print(f"  Intención: {result['intent']}")
        print(f"  Bot: {result['response']}")
        
        # Mostrar contexto actual
        memory_context = orchestrator.conversation_memory.get_context_summary()
        print(f"  [Contexto] Región: {memory_context['confirmed_region']}, "
              f"Problema: {memory_context['primary_problem']}, "
              f"Stage: {memory_context['stage']}")
    
    # Verificación final
    final_context = orchestrator.conversation_memory.get_context_summary()
    print(f"\n📊 CONTEXTO FINAL DESPUÉS DE 5 MENSAJES:")
    print(f"  - Región: {final_context['confirmed_region']}")
    print(f"  - Problema: {final_context['primary_problem']}")
    print(f"  - Keywords: {final_context['keywords']}")
    print(f"  - Etapa: {final_context['stage']}")
    
    assert final_context['confirmed_region'] == 'Bogotá', "❌ Región se perdió en conversación"
    assert final_context['primary_problem'] in ['conectividad', 'ayuda'], "❌ Problema se perdió"
    
    print("\n✅ TEST 4 PASÓ: Conversación completa mantiene contexto\n")


if __name__ == '__main__':
    try:
        print("\n" + "🧪"*40)
        print("SUITE DE TESTS: VALIDACIÓN DE MEMORIA CONVERSACIONAL")
        print("🧪"*40)
        
        test_memory_persistence()
        test_no_repeat_questions()
        test_problem_tracking()
        test_full_conversation_flow()
        
        print("="*80)
        print("✅ TODOS LOS TESTS PASARON")
        print("="*80)
        print("\n✨ El chatbot MANTIENE CONTEXTO PERFECTAMENTE ✨\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FALLÓ: {str(e)}\n")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}\n")
        import traceback
        traceback.print_exc()
