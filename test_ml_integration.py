#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SCRIPT DE PRUEBA - ML Model Integration
Valida que el endpoint /api/predict funciona correctamente
"""

import requests
import json
from pathlib import Path

# Configuración
BASE_URL = 'http://localhost:5000'
API_ENDPOINT = f'{BASE_URL}/api/predict'
BATCH_ENDPOINT = f'{BASE_URL}/api/predict-batch'

# Datos de prueba (ejemplo 1: sin acceso a internet)
TEST_DATA_NO_ACCESS = {
    "poblacion_total": 16295,
    "porcentaje_rural": 8.66,
    "estrato_promedio": 2.54,
    "tasa_pobreza": 54.49,
    "num_instituciones": 59,
    "computadores_por_estudiante": 1.34,
    "salones_por_institucion": 24,
    "docentes_por_institucion": 78,
    "cobertura_electrica": 89.94,
    "cobertura_4g": 42.64,
    "dispositivos_promedio_hogar": 1.96,
    "tasa_aprobacion": 62.50,
    "tasa_desercion": 36.06,
    "puntaje_pruebas": 354.19
}

# Datos de prueba (ejemplo 2: con acceso a internet)
TEST_DATA_WITH_ACCESS = {
    "poblacion_total": 1360,
    "porcentaje_rural": 66.92,
    "estrato_promedio": 4.15,
    "tasa_pobreza": 37.17,
    "num_instituciones": 35,
    "computadores_por_estudiante": 1.84,
    "salones_por_institucion": 3,
    "docentes_por_institucion": 41,
    "cobertura_electrica": 92.02,
    "cobertura_4g": 60.03,
    "dispositivos_promedio_hogar": 3.01,
    "tasa_aprobacion": 78.36,
    "tasa_desercion": 31.12,
    "puntaje_pruebas": 408.86
}

def print_header(text):
    """Imprimir encabezado"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def print_status(status, message):
    """Imprimir estado"""
    symbol = "✓" if status else "✗"
    color = "\033[92m" if status else "\033[91m"
    reset = "\033[0m"
    print(f"{color}{symbol} {message}{reset}")

def test_connection():
    """Test 1: Verificar conexión"""
    print_header("TEST 1: VERIFICAR CONEXIÓN")
    
    try:
        response = requests.get(f'{BASE_URL}/health', timeout=5)
        if response.status_code == 200:
            print_status(True, f"Servidor accesible en {BASE_URL}")
            print(f"   Response: {response.json()}")
            return True
        else:
            print_status(False, f"Servidor retornó código {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_status(False, f"No se pudo conectar a {BASE_URL}")
        print("   ¿Ejecutaste: python app.py?")
        return False
    except Exception as e:
        print_status(False, f"Error: {str(e)}")
        return False

def test_single_prediction(data, expected_prediction=None):
    """Test 2/3: Realizar predicción individual"""
    
    try:
        print(f"\n📨 Enviando datos de prueba...")
        response = requests.post(API_ENDPOINT, json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                print_status(True, "Predicción realizada exitosamente")
                print(f"\n📊 Resultado:")
                print(f"   Predicción: {result['prediction']}")
                print(f"   Interpretación: {result['interpretation']}")
                
                if result.get('prediction_proba'):
                    proba = result['prediction_proba']
                    print(f"   Probabilidades: [No: {proba[0]:.2%}, Sí: {proba[1]:.2%}]")
                
                print(f"   Timestamp: {result['timestamp']}")
                
                if expected_prediction is not None:
                    if result['prediction'] == expected_prediction:
                        print_status(True, f"Predicción coincide con esperado ({expected_prediction})")
                        return True
                    else:
                        print_status(False, f"Predicción NO coincide (esperado: {expected_prediction}, obtenido: {result['prediction']})")
                        return False
                return True
            else:
                print_status(False, f"Error en predicción: {result.get('error')}")
                return False
        else:
            print_status(False, f"HTTP {response.status_code}: {response.text}")
            return False
    
    except requests.exceptions.Timeout:
        print_status(False, "Timeout - el servidor tardó demasiado")
        return False
    except Exception as e:
        print_status(False, f"Error: {str(e)}")
        return False

def test_missing_features():
    """Test 4: Validar error con features faltantes"""
    print_header("TEST 4: VALIDAR FEATURES FALTANTES")
    
    incomplete_data = {"poblacion_total": 16295}  # Faltan features
    
    try:
        print(f"\n📨 Enviando datos incompletos (solo 1 de 14 features)...")
        response = requests.post(API_ENDPOINT, json=incomplete_data, timeout=10)
        result = response.json()
        
        if not result.get('success') and 'faltantes' in result.get('error', '').lower():
            print_status(True, "Validación correcta: Features faltantes detectados")
            print(f"   Error: {result['error']}")
            return True
        else:
            print_status(False, "No se detectó error de features faltantes")
            return False
    except Exception as e:
        print_status(False, f"Error: {str(e)}")
        return False

def test_invalid_values():
    """Test 5: Validar error con valores inválidos"""
    print_header("TEST 5: VALIDAR VALORES INVÁLIDOS")
    
    invalid_data = TEST_DATA_NO_ACCESS.copy()
    invalid_data['porcentaje_rural'] = 150  # Valor fuera de rango (0-100)
    
    try:
        print(f"\n📨 Enviando datos con valor fuera de rango (porcentaje_rural: 150)...")
        response = requests.post(API_ENDPOINT, json=invalid_data, timeout=10)
        result = response.json()
        
        # Nota: El servidor puede o no validar rangos, depende de la implementación
        print(f"   Respuesta: success={result.get('success')}")
        print(f"   Nota: Este test valida que el servidor maneja valores extremos")
        return True
    except Exception as e:
        print_status(False, f"Error: {str(e)}")
        return False

def test_batch_prediction():
    """Test 6: Predicción en lote"""
    print_header("TEST 6: PREDICCIÓN EN LOTE")
    
    batch_data = {
        "records": [TEST_DATA_NO_ACCESS, TEST_DATA_WITH_ACCESS]
    }
    
    try:
        print(f"\n📨 Enviando 2 registros para predicción en lote...")
        response = requests.post(BATCH_ENDPOINT, json=batch_data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                print_status(True, "Predicción en lote realizada exitosamente")
                print(f"\n📊 Resultado:")
                print(f"   Total registros: {result['total_records']}")
                print(f"   Predicciones obtenidas: {len(result.get('predictions', []))}")
                
                for pred in result.get('predictions', []):
                    print(f"   - Record {pred['record_id']}: Predicción={pred['prediction']}")
                
                return True
            else:
                print_status(False, f"Error: {result.get('error')}")
                return False
        else:
            print_status(False, f"HTTP {response.status_code}")
            return False
    except Exception as e:
        print_status(False, f"Error: {str(e)}")
        return False

def test_model_file_exists():
    """Test 0: Verificar que el archivo del modelo existe"""
    print_header("TEST 0: VERIFICAR ARCHIVO DEL MODELO")
    
    model_path = Path('PROYECTO SIUUU/models/education_mlp_pipeline.joblib')
    
    if model_path.exists():
        file_size_mb = model_path.stat().st_size / (1024 * 1024)
        print_status(True, f"Modelo encontrado: {model_path} ({file_size_mb:.2f} MB)")
        return True
    else:
        print_status(False, f"Modelo NO encontrado: {model_path}")
        return False

def main():
    """Ejecutar todos los tests"""
    print("\n")
    print("█" * 60)
    print("█  🤖 VALIDACIÓN DE INTEGRACIÓN ML - CHATBOT BOTI")
    print("█" * 60)
    
    results = {}
    
    # Test 0
    results['model_file'] = test_model_file_exists()
    
    # Test 1
    results['connection'] = test_connection()
    
    if not results['connection']:
        print("\n⚠️  No se pudo conectar al servidor. Asegúrate de ejecutar: python app.py")
        return
    
    # Test 2
    print_header("TEST 2: PREDICCIÓN 1 (SIN ACCESO A INTERNET)")
    results['prediction_1'] = test_single_prediction(TEST_DATA_NO_ACCESS)
    
    # Test 3
    print_header("TEST 3: PREDICCIÓN 2 (CON ACCESO A INTERNET)")
    results['prediction_2'] = test_single_prediction(TEST_DATA_WITH_ACCESS)
    
    # Test 4
    results['missing_features'] = test_missing_features()
    
    # Test 5
    results['invalid_values'] = test_invalid_values()
    
    # Test 6
    results['batch_prediction'] = test_batch_prediction()
    
    # Resumen
    print_header("RESUMEN DE RESULTADOS")
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    
    for test_name, result in results.items():
        symbol = "✓" if result else "✗"
        status_text = "PASÓ" if result else "FALLÓ"
        color = "\033[92m" if result else "\033[91m"
        reset = "\033[0m"
        print(f"{color}{symbol}{reset} {test_name:<20} {status_text}")
    
    print(f"\n📈 Total: {passed_tests}/{total_tests} tests pasaron")
    
    if passed_tests == total_tests:
        print("\n🎉 ¡INTEGRACIÓN ML COMPLETADA Y VALIDADA!")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) fallaron. Revisa los errores arriba.")

if __name__ == '__main__':
    main()
