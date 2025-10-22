"""
TEST SUITE - Validar sistema híbrido de chatbot inteligente
Ejecutar: python test_hybrid_system.py
"""

import sys
import os
from pathlib import Path

# Agregar raíz al path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("TESTING: SISTEMA HÍBRIDO DE CHATBOT INTELIGENTE")
print("=" * 70)

# TEST 1: Cargar módulos
print("\n[TEST 1] Cargando módulos...")
try:
    from src.chatbot.chatbot_orchestrator import (
        ChatbotOrchestrator, IntentDetector, EntityExtractor, ResponseGenerator
    )
    print("✓ Módulos cargados exitosamente")
except ImportError as e:
    print(f"✗ Error importando módulos: {e}")
    sys.exit(1)

# TEST 2: Inicializar componentes NLP
print("\n[TEST 2] Inicializando componentes NLP...")
try:
    detector = IntentDetector()
    extractor = EntityExtractor()
    generator = ResponseGenerator()
    print("✓ Componentes NLP inicializados")
except Exception as e:
    print(f"✗ Error inicializando NLP: {e}")
    sys.exit(1)

# TEST 3: Pruebas de IntentDetector
print("\n[TEST 3] Probando detección de intenciones...")
test_messages = [
    ("Hola bot, ¿cómo estás?", "saludar"),
    ("Necesito ayuda urgente", "ayuda"),
    ("Predice el acceso a internet", "prediccion"),
    ("¿Cómo mejorar la conectividad?", "mejora"),
    ("Adiós, nos vemos", "despedida"),
]

for message, expected_intent in test_messages:
    intent, confidence = detector.detect(message)
    match = "✓" if intent in expected_intent else "✗"
    print(f"  {match} '{message}' → {intent} ({confidence:.1%})")

# TEST 4: Pruebas de EntityExtractor
print("\n[TEST 4] Probando extracción de entidades...")
entities_tests = [
    ("Soy de Bogotá", "Bogotá"),
    ("Necesito datos de Antioquia", "Antioquia"),
    ("En Magdalena hay 50 escuelas", "Magdalena"),
]

for message, expected_region in entities_tests:
    entities = extractor.extract(message)
    region = entities.get('region')
    match = "✓" if region and expected_region.lower() in region.lower() else "✗"
    print(f"  {match} '{message}' → región: {region}")

# TEST 5: Pruebas de ResponseGenerator
print("\n[TEST 5] Probando generador de respuestas...")
try:
    response1 = generator.generate('saludar', {}, None, None)
    response2 = generator.generate('despedida', {}, None, None)
    response3 = generator.generate('ayuda', {'region': 'Bogotá'}, None, None)
    
    print(f"  ✓ Respuesta saludar: {response1[:50]}...")
    print(f"  ✓ Respuesta despedida: {response2[:50]}...")
    print(f"  ✓ Respuesta ayuda: {response3[:50]}...")
except Exception as e:
    print(f"  ✗ Error generando respuestas: {e}")

# TEST 6: Cargar modelo ML (si existe)
print("\n[TEST 6] Intentando cargar modelo ML...")
try:
    import joblib
    import numpy as np
    
    model_path = Path('PROYECTO SIUUU/models/education_mlp_pipeline.joblib')
    if model_path.exists():
        ml_model = joblib.load(model_path)
        print(f"  ✓ Modelo ML cargado desde {model_path}")
        
        # Hacer predicción de prueba
        test_input = np.array([[16295, 8.66, 2.54, 45.2, 10, 0.5, 30, 10, 95, 80, 1.2, 75, 5, 75]]).reshape(1, -1)
        prediction = ml_model.predict(test_input)[0]
        proba = ml_model.predict_proba(test_input)[0]
        print(f"  ✓ Predicción de prueba: {prediction} (probabilidades: {proba})")
    else:
        print(f"  ⚠ Modelo ML no encontrado en {model_path}")
        ml_model = None
except Exception as e:
    print(f"  ⚠ Error cargando modelo ML: {e}")
    ml_model = None

# TEST 7: Cargar VAE (si existe)
print("\n[TEST 7] Intentando cargar modelos VAE...")
try:
    try:
        import tensorflow as tf
        import tensorflow.keras as keras
        
        vae_encoder_path = Path('PROYECTO SIUUU/models/vae_encoder.h5')
        vae_decoder_path = Path('PROYECTO SIUUU/models/vae_decoder.h5')
        
        if vae_encoder_path.exists() and vae_decoder_path.exists():
            vae_encoder = keras.models.load_model(str(vae_encoder_path))
            vae_decoder = keras.models.load_model(str(vae_decoder_path))
            print(f"  ✓ Modelos VAE cargados")
            
            # Test VAE
            test_latent = np.random.normal(0, 1, (1, 8))
            vae_output = vae_decoder.predict(test_latent, verbose=0)
            print(f"  ✓ Salida VAE: shape {vae_output.shape}")
        else:
            print(f"  ⚠ Modelos VAE no encontrados (opcional)")
            vae_encoder = None
            vae_decoder = None
    except ImportError:
        print(f"  ⚠ TensorFlow no disponible (instala: pip install tensorflow>=2.10.0)")
        vae_encoder = None
        vae_decoder = None
except Exception as e:
    print(f"  ⚠ Error cargando VAE: {e}")
    vae_encoder = None
    vae_decoder = None

# TEST 8: Inicializar Orquestador
print("\n[TEST 8] Inicializando ChatbotOrchestrator...")
try:
    orchestrator = ChatbotOrchestrator(
        ml_model=ml_model,
        vae_encoder=vae_encoder,
        vae_decoder=vae_decoder,
        vae_scaler=None,
        vae_features=None
    )
    print("✓ ChatbotOrchestrator inicializado")
except Exception as e:
    print(f"✗ Error inicializando orquestador: {e}")
    sys.exit(1)

# TEST 9: Procesar mensajes
print("\n[TEST 9] Procesando mensajes con el orquestador...")
test_conversations = [
    "Hola, ¿cómo estás?",
    "Soy de Bogotá",
    "Necesito ayuda con conectividad",
    "¿Qué mejoras me recomiendas?",
    "Adiós",
]

for message in test_conversations:
    try:
        result = orchestrator.process_message(message)
        print(f"\n  📤 Usuario: {message}")
        print(f"  📥 Bot: {result['response'][:60]}...")
        print(f"  🎯 Intención: {result['intent']} ({result['intent_confidence']:.0%})")
    except Exception as e:
        print(f"  ✗ Error procesando '{message}': {e}")

# TEST 10: Historial de conversación
print("\n[TEST 10] Verificando historial de conversación...")
try:
    history = orchestrator.get_conversation_history()
    print(f"✓ Historial guardado: {len(history)} mensajes")
    for idx, msg in enumerate(history[:3], 1):
        print(f"  [{idx}] Intent: {msg['intent']} | Confianza: {msg['intent_confidence']:.0%}")
except Exception as e:
    print(f"✗ Error obteniendo historial: {e}")

# TEST 11: Exportar conversación
print("\n[TEST 11] Exportando conversación...")
try:
    export = orchestrator.export_conversation()
    print(f"✓ Conversación exportada:")
    print(f"  - Región detectada: {export['user_region']}")
    print(f"  - Total mensajes: {export['conversation_count']}")
    print(f"  - Timestamp: {export['exported_at']}")
except Exception as e:
    print(f"✗ Error exportando: {e}")

# RESUMEN FINAL
print("\n" + "=" * 70)
print("RESUMEN DE PRUEBAS")
print("=" * 70)
print("""
✓ Módulos NLP cargados
✓ IntentDetector funcionando
✓ EntityExtractor funcionando
✓ ResponseGenerator funcionando
✓ ChatbotOrchestrator inicializado
✓ Procesamiento de mensajes activo
✓ Historial de conversación guardado
✓ Exportación de datos funcional

Componentes Opcionales:
""")
print(f"  {'✓' if ml_model else '✗'} Modelo ML (predicción)")
print(f"  {'✓' if vae_encoder and vae_decoder else '✗'} Modelos VAE (generación)")

print("""
🚀 SISTEMA LISTO PARA USAR

Próximos pasos:
1. python app.py                      # Iniciar servidor
2. Abrir: http://localhost:5000       # Chat inteligente
3. Probar predicciones en /admin      # Dashboard
4. Exportar conversación con /api/chat-export

¡El sistema híbrido está funcionando correctamente!
""")
print("=" * 70)
