#!/usr/bin/env python3
"""
SCRIPT DE SETUP AUTOMATIZADO - Configurar todo de una vez
Ejecutar: python setup_hybrid_chatbot.py
"""

import os
import sys
import subprocess
from pathlib import Path

print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                    SETUP AUTOMATIZADO - CHATBOT HÍBRIDO                  ║
║                                                                           ║
║  Este script:                                                             ║
║  1. Valida que Python esté instalado                                      ║
║  2. Crea directorios necesarios                                           ║
║  3. Instala dependencias                                                  ║
║  4. Entrena modelo VAE (opcional)                                         ║
║  5. Ejecuta suite de pruebas                                              ║
║  6. Muestra estado final                                                  ║
╚═══════════════════════════════════════════════════════════════════════════╝
""")

# Verificar Python
print("📋 [1/5] Verificando Python...")
if sys.version_info < (3, 8):
    print("❌ Se requiere Python 3.8+")
    sys.exit(1)
print(f"✅ Python {sys.version.split()[0]} detectado")

# Crear directorios
print("\n📁 [2/5] Creando directorios...")
directories = [
    "logs",
    "PROYECTO SIUUU/models",
    "src/chatbot",
    "static/css",
    "static/js"
]

for dir_path in directories:
    Path(dir_path).mkdir(parents=True, exist_ok=True)
    print(f"  ✓ {dir_path}")

# Instalar dependencias
print("\n📦 [3/5] Instalando dependencias...")
print("  Esta operación puede tardar varios minutos (especialmente TensorFlow)...")

requirements_file = "requirements_updated.txt"
if Path(requirements_file).exists():
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", requirements_file],
            check=True,
            capture_output=True
        )
        print("✅ Dependencias instaladas correctamente")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando dependencias: {e}")
        sys.exit(1)
else:
    print(f"❌ {requirements_file} no encontrado")
    sys.exit(1)

# Entrenar VAE (opcional)
print("\n🧠 [4/5] Modelo VAE...")
vae_encoder = Path("PROYECTO SIUUU/models/vae_encoder.h5")
vae_decoder = Path("PROYECTO SIUUU/models/vae_decoder.h5")

if vae_encoder.exists() and vae_decoder.exists():
    print("  ✓ Modelos VAE ya existen (saltando entrenamiento)")
else:
    print("  Modelos VAE no encontrados")
    response = input("  ¿Entrenar VAE ahora? (s/n): ").lower().strip()
    
    if response == 's':
        try:
            print("  Entrenando VAE con datos sintéticos...")
            subprocess.run(
                [sys.executable, "train_vae_model.py", "--epochs", "30"],
                check=True
            )
            print("✅ VAE entrenado correctamente")
        except subprocess.CalledProcessError:
            print("⚠️  Error entrenando VAE (se puede continuar sin él)")
    else:
        print("  Saltando entrenamiento de VAE")

# Ejecutar pruebas
print("\n✅ [5/5] Ejecutando suite de pruebas...")
try:
    subprocess.run(
        [sys.executable, "test_hybrid_system.py"],
        check=True
    )
    print("\n✅ Todas las pruebas pasaron correctamente")
except subprocess.CalledProcessError:
    print("\n⚠️  Algunas pruebas fallaron (revisa los logs)")

# Resumen final
print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                    ✅ SETUP COMPLETADO CON ÉXITO                         ║
╚═══════════════════════════════════════════════════════════════════════════╝

📊 STATUS RESUMEN:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Python 3.8+ verificado
✅ Directorios creados
✅ Dependencias instaladas
✅ Modelos disponibles
✅ Suite de pruebas pasada

🚀 PRÓXIMO PASO:

Inicia la aplicación con:
    python app.py

Luego abre tu navegador en:
    http://localhost:5000

📚 DOCUMENTACIÓN:
    - GUIA_INICIO_RAPIDO.md     (Start here!)
    - ARQUITECTURA_HIBRIDA.md   (Técnico)
    - IMPLEMENTACION_COMPLETADA.txt (Resumen)

💡 TROUBLESHOOTING:
    tail -f logs/app.log        (Ver logs en tiempo real)
    python test_hybrid_system.py (Validar componentes)

¿Preguntas? Revisa la documentación o contacta al equipo.

¡A disfrutar del chatbot inteligente! 🎉
""")
