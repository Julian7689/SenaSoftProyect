#!/usr/bin/env python3
"""
Script de Testing para Sistema Multi-Usuario BOTI
Valida autenticación, consentimiento, chat y admin
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:5000"

class BOTITester:
    def __init__(self):
        self.session_token = None
        self.user_email = None
        self.conversation_id = None
        self.results = []
    
    def print_test(self, name, passed, message=""):
        """Registra resultado de test"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"\n{status} | {name}")
        if message:
            print(f"      {message}")
        self.results.append((name, passed))
    
    def test_login_user(self):
        """Test: Login como usuario regular"""
        print("\n" + "="*60)
        print("TEST 1: LOGIN USUARIO REGULAR")
        print("="*60)
        
        try:
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": "user@boti.com",
                "password": "user123"
            })
            
            data = response.json()
            passed = data.get('success') and 'session_token' in data
            
            if passed:
                self.session_token = data['session_token']
                self.user_email = data['user']['email']
            
            self.print_test(
                "Login Usuario",
                passed,
                f"Token: {self.session_token[:20]}..." if passed else data.get('error', 'Unknown error')
            )
            
            return passed
        except Exception as e:
            self.print_test("Login Usuario", False, str(e))
            return False
    
    def test_login_admin(self):
        """Test: Login como admin"""
        print("\n" + "="*60)
        print("TEST 2: LOGIN ADMIN")
        print("="*60)
        
        try:
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": "admin@boti.com",
                "password": "admin123"
            })
            
            data = response.json()
            passed = data.get('success') and data['user']['role'] == 'admin'
            
            admin_token = data.get('session_token') if passed else None
            
            self.print_test(
                "Login Admin",
                passed,
                f"Role: {data['user']['role']}" if passed else data.get('error')
            )
            
            return admin_token if passed else None
        except Exception as e:
            self.print_test("Login Admin", False, str(e))
            return None
    
    def test_verify_session(self):
        """Test: Verificar sesión activa"""
        print("\n" + "="*60)
        print("TEST 3: VERIFICAR SESIÓN")
        print("="*60)
        
        try:
            headers = {"Authorization": f"Bearer {self.session_token}"} if self.session_token else {}
            response = requests.get(f"{BASE_URL}/api/auth/verify", headers=headers)
            
            data = response.json()
            passed = data.get('success') and data['user']['email'] == self.user_email
            
            self.print_test(
                "Verificar Sesión",
                passed,
                f"Usuario: {data['user']['email']}" if passed else data.get('error')
            )
            
            return passed
        except Exception as e:
            self.print_test("Verificar Sesión", False, str(e))
            return False
    
    def test_consent_lsrpd(self):
        """Test: Guardar consentimiento LSRPD"""
        print("\n" + "="*60)
        print("TEST 4: CONSENTIMIENTO LSRPD")
        print("="*60)
        
        try:
            consent_data = {
                "consent_items": {
                    "datos_personales": True,  # REQUERIDO
                    "menores": True,            # REQUERIDO
                    "tratamiento_anonimizado": True,
                    "reportes_anonimizados": False,
                    "comparticion_sponsors": False
                }
            }
            
            headers = {"Authorization": f"Bearer {self.session_token}"}
            response = requests.post(f"{BASE_URL}/api/auth/consent", 
                                    json=consent_data, 
                                    headers=headers)
            
            data = response.json()
            passed = data.get('success')
            
            self.print_test(
                "Consentimiento LSRPD",
                passed,
                f"Items aceptados: {len(consent_data['consent_items'])}" if passed else data.get('error')
            )
            
            return passed
        except Exception as e:
            self.print_test("Consentimiento LSRPD", False, str(e))
            return False
    
    def test_create_conversation(self):
        """Test: Crear nueva conversación"""
        print("\n" + "="*60)
        print("TEST 5: CREAR CONVERSACIÓN")
        print("="*60)
        
        try:
            headers = {"Authorization": f"Bearer {self.session_token}"}
            response = requests.post(f"{BASE_URL}/api/chat/conversation/create",
                                    json={"title": "Test Conversation"},
                                    headers=headers)
            
            data = response.json()
            passed = data.get('success') and 'conversation_id' in data
            
            if passed:
                self.conversation_id = data['conversation_id']
            
            self.print_test(
                "Crear Conversación",
                passed,
                f"ID: {self.conversation_id}" if passed else data.get('error')
            )
            
            return passed
        except Exception as e:
            self.print_test("Crear Conversación", False, str(e))
            return False
    
    def test_send_message(self):
        """Test: Enviar mensaje en conversación"""
        print("\n" + "="*60)
        print("TEST 6: ENVIAR MENSAJE")
        print("="*60)
        
        try:
            if not self.conversation_id:
                self.print_test("Enviar Mensaje", False, "No hay conversación activa")
                return False
            
            headers = {"Authorization": f"Bearer {self.session_token}"}
            response = requests.post(
                f"{BASE_URL}/api/chat/conversation/{self.conversation_id}/message",
                json={"message": "Hola, soy de Bogotá"},
                headers=headers
            )
            
            data = response.json()
            passed = data.get('success')
            
            self.print_test(
                "Enviar Mensaje",
                passed,
                f"Respuesta bot: {data.get('response', '')[:50]}..." if passed else data.get('error')
            )
            
            return passed
        except Exception as e:
            self.print_test("Enviar Mensaje", False, str(e))
            return False
    
    def test_get_history(self):
        """Test: Obtener historial de conversación"""
        print("\n" + "="*60)
        print("TEST 7: OBTENER HISTORIAL")
        print("="*60)
        
        try:
            if not self.conversation_id:
                self.print_test("Obtener Historial", False, "No hay conversación activa")
                return False
            
            headers = {"Authorization": f"Bearer {self.session_token}"}
            response = requests.get(
                f"{BASE_URL}/api/chat/conversation/{self.conversation_id}/history",
                headers=headers
            )
            
            data = response.json()
            passed = data.get('success') and len(data.get('messages', [])) > 0
            
            message_count = len(data.get('messages', []))
            self.print_test(
                "Obtener Historial",
                passed,
                f"Mensajes: {message_count}" if passed else data.get('error')
            )
            
            return passed
        except Exception as e:
            self.print_test("Obtener Historial", False, str(e))
            return False
    
    def test_get_conversations(self):
        """Test: Obtener lista de conversaciones"""
        print("\n" + "="*60)
        print("TEST 8: LISTAR CONVERSACIONES")
        print("="*60)
        
        try:
            headers = {"Authorization": f"Bearer {self.session_token}"}
            response = requests.get(f"{BASE_URL}/api/chat/conversations", headers=headers)
            
            data = response.json()
            passed = data.get('success')
            
            conv_count = len(data.get('conversations', []))
            self.print_test(
                "Listar Conversaciones",
                passed,
                f"Total conversaciones: {conv_count}" if passed else data.get('error')
            )
            
            return passed
        except Exception as e:
            self.print_test("Listar Conversaciones", False, str(e))
            return False
    
    def test_admin_dashboard(self):
        """Test: Obtener datos del dashboard admin"""
        print("\n" + "="*60)
        print("TEST 9: DASHBOARD ADMIN")
        print("="*60)
        
        # Primero, login como admin
        try:
            admin_response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": "admin@boti.com",
                "password": "admin123"
            })
            
            admin_data = admin_response.json()
            if not admin_data.get('success'):
                self.print_test("Dashboard Admin", False, "No se pudo hacer login como admin")
                return False
            
            admin_token = admin_data['session_token']
            
            # Obtener datos del dashboard
            headers = {"Authorization": f"Bearer {admin_token}"}
            response = requests.get(f"{BASE_URL}/api/admin/dashboard-data", headers=headers)
            
            data = response.json()
            passed = data.get('success') and 'data' in data
            
            if passed:
                dashboard = data['data']
                message = (f"Usuarios: {dashboard.get('total_users')}, "
                          f"Conversaciones: {dashboard.get('total_conversations')}")
            else:
                message = data.get('error', 'Error desconocido')
            
            self.print_test("Dashboard Admin", passed, message)
            
            return passed
        except Exception as e:
            self.print_test("Dashboard Admin", False, str(e))
            return False
    
    def test_logout(self):
        """Test: Logout de usuario"""
        print("\n" + "="*60)
        print("TEST 10: LOGOUT")
        print("="*60)
        
        try:
            headers = {"Authorization": f"Bearer {self.session_token}"}
            response = requests.post(f"{BASE_URL}/api/auth/logout", headers=headers)
            
            data = response.json()
            passed = data.get('success')
            
            self.print_test(
                "Logout",
                passed,
                data.get('message', '') if passed else data.get('error')
            )
            
            return passed
        except Exception as e:
            self.print_test("Logout", False, str(e))
            return False
    
    def run_all_tests(self):
        """Ejecutar todos los tests"""
        print("\n" + "🤖" * 30)
        print("BOTI MULTI-USER SYSTEM - TEST SUITE")
        print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("🤖" * 30)
        
        try:
            # Test de usuario
            self.test_login_user()
            self.test_verify_session()
            self.test_consent_lsrpd()
            self.test_create_conversation()
            self.test_send_message()
            self.test_get_history()
            self.test_get_conversations()
            self.test_logout()
            
            # Test de admin
            self.test_login_admin()
            self.test_admin_dashboard()
            
        except Exception as e:
            print(f"\n❌ Error general: {str(e)}")
        
        # Resumen
        print("\n" + "="*60)
        print("RESUMEN DE RESULTADOS")
        print("="*60)
        
        passed = sum(1 for _, result in self.results if result)
        total = len(self.results)
        percentage = (passed / total * 100) if total > 0 else 0
        
        for name, result in self.results:
            status = "✅" if result else "❌"
            print(f"{status} {name}")
        
        print(f"\nTotal: {passed}/{total} tests pasados ({percentage:.1f}%)")
        print(f"Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60 + "\n")
        
        return percentage == 100

if __name__ == "__main__":
    print("\n⏳ Esperando a que el servidor esté listo...")
    print("   (Asegúrate de ejecutar: python app.py)")
    time.sleep(2)
    
    tester = BOTITester()
    success = tester.run_all_tests()
    
    exit(0 if success else 1)
