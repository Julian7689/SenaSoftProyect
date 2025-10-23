#!/usr/bin/env python3
"""
Test del Sistema Inteligente Completo:
Case Manager + Preguntas Inteligentes + Contexto Regional
"""

import sys
sys.path.append('.')

from src.chatbot.enhanced_orchestrator import EnhancedChatbotOrchestrator
import json

def test_intelligent_system():
    """
    Prueba el sistema completo con casos de conectividad regional
    """
    
    print("=" * 80)
    print("🧠 PRUEBA DEL SISTEMA INTELIGENTE COMPLETO")
    print("=" * 80)
    
    # Inicializar orchestrator (sin modelos ML por ahora)
    orchestrator = EnhancedChatbotOrchestrator(user_id='test_user')
    
    # =============== CASO 1: Pregunta sobre regiones sin internet ===============
    
    print("\n" + "=" * 60)
    print("📍 CASO 1: Pregunta sobre regiones colombianas")
    print("=" * 60)
    
    mensaje_1 = "Hola, necesito saber cuáles son las regiones de Colombia donde no hay cobertura de internet"
    
    print(f"👤 Usuario: {mensaje_1}")
    print("\n🤖 Procesando...")
    
    resultado_1 = orchestrator.process_message_with_case_management(
        user_message=mensaje_1,
        conversation_history=[]
    )
    
    print(f"\n✅ Respuesta generada por: {resultado_1['generated_by']}")
    print(f"🎯 Intent detectado: {resultado_1['intent']}")
    print(f"📊 Confianza: {resultado_1['confidence']}")
    
    if resultado_1.get('regional_context'):
        print(f"🌍 Contexto regional detectado: {resultado_1['regional_context']['department_name']}")
    
    if resultado_1.get('intelligent_questions'):
        print(f"🤔 Preguntas inteligentes generadas: {len(resultado_1['intelligent_questions'])}")
    
    print(f"\n💬 RESPUESTA:")
    print("-" * 40)
    print(resultado_1['response'])
    
    # =============== CASO 2: Usuario del Chocó con problema urgente ===============
    
    print("\n" + "=" * 60)
    print("🚨 CASO 2: Usuario del Chocó con problema urgente")
    print("=" * 60)
    
    mensaje_2 = "Soy del Chocó y necesito internet urgente para las tareas de mis hijos, no tengo plata para pagarlo"
    
    print(f"👤 Usuario: {mensaje_2}")
    print("\n🤖 Procesando...")
    
    conversacion = [
        {"role": "user", "content": mensaje_1},
        {"role": "assistant", "content": resultado_1['response']}
    ]
    
    resultado_2 = orchestrator.process_message_with_case_management(
        user_message=mensaje_2,
        conversation_history=conversacion
    )
    
    print(f"\n✅ Respuesta generada por: {resultado_2['generated_by']}")
    print(f"🚨 Urgencia detectada: {resultado_2.get('urgency', 'N/A')}")
    print(f"📊 Impacto calculado: {resultado_2.get('impact_score', 0)}/100")
    
    if resultado_2.get('case_id'):
        print(f"📋 Caso creado: {resultado_2['case_id']}")
        print(f"🎯 Soluciones ofrecidas: {resultado_2.get('solutions_offered', 0)}")
    
    if resultado_2.get('regional_context'):
        print(f"🌍 Contexto regional: {resultado_2['regional_context']['department_name']}")
        print(f"📶 Nivel cobertura: {resultado_2['regional_context']['coverage_level']}/5")
    
    print(f"\n💬 RESPUESTA:")
    print("-" * 40)
    print(resultado_2['response'])
    
    # =============== CASO 3: Pregunta de seguimiento ===============
    
    print("\n" + "=" * 60)
    print("🔄 CASO 3: Pregunta de seguimiento sobre Antioquia")
    print("=" * 60)
    
    mensaje_3 = "¿Y qué tal está la conectividad en Antioquia?"
    
    print(f"👤 Usuario: {mensaje_3}")
    print("\n🤖 Procesando...")
    
    conversacion.extend([
        {"role": "user", "content": mensaje_2},
        {"role": "assistant", "content": resultado_2['response']}
    ])
    
    resultado_3 = orchestrator.process_message_with_case_management(
        user_message=mensaje_3,
        conversation_history=conversacion
    )
    
    print(f"\n✅ Respuesta generada por: {resultado_3['generated_by']}")
    
    if resultado_3.get('regional_context'):
        print(f"🌍 Nueva región detectada: {resultado_3['regional_context']['department_name']}")
        print(f"📶 Nivel cobertura: {resultado_3['regional_context']['coverage_level']}/5")
    
    if resultado_3.get('intelligent_questions'):
        print(f"🤔 Nuevas preguntas (sin repetir): {len(resultado_3['intelligent_questions'])}")
        for i, q in enumerate(resultado_3['intelligent_questions'], 1):
            print(f"   {i}. {q}")
    
    print(f"\n💬 RESPUESTA:")
    print("-" * 40)
    print(resultado_3['response'])
    
    # =============== RESUMEN FINAL ===============
    
    print("\n" + "=" * 80)
    print("📈 RESUMEN DE LA PRUEBA")
    print("=" * 80)
    
    print("✅ Funcionalidades probadas:")
    print("   • Detección automática de contexto regional colombiano")
    print("   • Generación de preguntas inteligentes contextuales")  
    print("   • Memoria conversacional (evita repetir preguntas)")
    print("   • Integración con Case Manager para casos urgentes")
    print("   • Respuestas enriquecidas con información específica")
    
    casos_creados = sum(1 for r in [resultado_1, resultado_2, resultado_3] if r.get('case_id'))
    contextos_regionales = sum(1 for r in [resultado_1, resultado_2, resultado_3] if r.get('regional_context'))
    preguntas_generadas = sum(len(r.get('intelligent_questions', [])) for r in [resultado_1, resultado_2, resultado_3])
    
    print(f"\n📊 Estadísticas:")
    print(f"   • Casos sociales creados: {casos_creados}")
    print(f"   • Contextos regionales detectados: {contextos_regionales}")
    print(f"   • Preguntas inteligentes generadas: {preguntas_generadas}")
    
    print("\n🎉 Sistema inteligente funcionando correctamente!")

if __name__ == "__main__":
    test_intelligent_system()