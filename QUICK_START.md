# 🚀 INSTRUCCIONES DE INICIO RÁPIDO

## ⚡ Inicio en 3 Pasos

### 1️⃣ Instalar Dependencias
```bash
pip install -r requirements.txt
```

**Requisitos principales:**
- Flask
- Flask-CORS
- python-dotenv
- numpy
- pandas
- joblib
- requests (para testing)

### 2️⃣ Iniciar el Servidor
```bash
cd c:\Users\AdminSena\proyecto_senasoft
python app.py
```

**Esperado:**
```
========================================================
INICIALIZANDO APLICACIÓN
========================================================
✓ Modelo ML cargado correctamente
✓ ChatbotOrchestrator inicializado correctamente
Iniciando servidor en http://127.0.0.1:5000
========================================================
```

### 3️⃣ Acceder a la Aplicación
```
http://localhost:5000/auth/login
```

---

## 🔑 Credenciales de Prueba

### Usuario Regular
```
Email:    user@boti.com
Password: user123
```
→ Acceso a Chat y Consentimiento LSRPD

### Administrador
```
Email:    admin@boti.com
Password: admin123
```
→ Acceso directo a Dashboard Admin

---

## 📱 Flujo de Usuario Paso a Paso

### Para Usuarios Regulares:

1. **Login** (`/auth/login`)
   - Ingresa: user@boti.com / user123
   - Click en "Iniciar Sesión"

2. **Consentimiento LSRPD** (`/user/consent`)
   - Lee la política de privacidad
   - Checkea items obligatorios:
     ✓ Datos personales (REQUERIDO)
     ✓ Menores de edad (REQUERIDO)
   - Click en "Aceptar y Continuar"

3. **Chat** (`/user/chat`)
   - Crear nueva conversación
   - Escribir mensajes
   - Ver respuestas del bot
   - Múltiples conversaciones soportadas

### Para Administradores:

1. **Login** (`/auth/login`)
   - Ingresa: admin@boti.com / admin123
   - Click en "Iniciar Sesión"

2. **Dashboard Admin** (`/admin/dashboard`)
   - Ver métricas en tiempo real
   - Gráficos por región
   - Lista de usuarios
   - Auto-refresco cada 30 segundos

---

## 🧪 Testing Automatizado

### Ejecutar Suite de Tests

```bash
python test_multi_user_system.py
```

**Qué valida:**
- ✅ Login de usuario
- ✅ Login de admin
- ✅ Verificación de sesión
- ✅ Consentimiento LSRPD
- ✅ Crear conversación
- ✅ Enviar mensajes
- ✅ Obtener historial
- ✅ Listar conversaciones
- ✅ Dashboard admin
- ✅ Logout

**Esperado:**
```
========================================================
RESUMEN DE RESULTADOS
========================================================
✅ Login Usuario
✅ Verificar Sesión
✅ Consentimiento LSRPD
✅ Crear Conversación
✅ Enviar Mensaje
✅ Obtener Historial
✅ Listar Conversaciones
✅ Dashboard Admin
✅ Logout

Total: 10/10 tests pasados (100%)
```

---

## 🌐 Rutas Disponibles

### Frontend
| Ruta | Descripción | Tipo |
|------|-------------|------|
| `/auth/login` | Página de login | GET |
| `/user/consent` | Consentimiento LSRPD | GET |
| `/user/chat` | Chat principal | GET |
| `/admin/dashboard` | Panel administrador | GET |
| `/info` | Información de recursos | GET |

### API - Autenticación
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/auth/login` | Login usuario |
| POST | `/api/auth/register` | Registrar usuario |
| GET | `/api/auth/verify` | Verificar sesión |
| POST | `/api/auth/logout` | Logout |
| GET/POST | `/api/auth/consent` | LSRPD consent |

### API - Chat
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/chat/conversations` | Listar conversaciones |
| POST | `/api/chat/conversation/create` | Crear conversación |
| GET | `/api/chat/conversation/<id>/history` | Historial |
| POST | `/api/chat/conversation/<id>/message` | Enviar mensaje |
| GET | `/api/chat/conversation/<id>/delete` | Eliminar |

### API - Admin
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/admin/dashboard-data` | Datos dashboard |
| GET | `/api/admin/users` | Lista de usuarios |

---

## 💾 Almacenamiento de Datos

**IMPORTANTE:** Todos los datos se guardan en **MEMORIA** y se pierden al reiniciar.

### Ubicación de Datos en Memoria:
- **Usuarios:** `MOCK_USERS` en `src/auth/mock_auth.py`
- **Sesiones:** `ACTIVE_SESSIONS` en `src/auth/mock_auth.py`
- **Consentimientos:** `USER_CONSENTS` en `src/auth/mock_auth.py`
- **Conversaciones:** `CONVERSATIONS_STORAGE` en `src/conversation/mock_store.py`
- **Contexto:** `CONTEXT_STORAGE` en `src/conversation/mock_store.py`

### Para convertir a BD Real:
Reemplaza los módulos mock con versiones de BD:
```python
# Actual (en memoria)
from src.auth.mock_auth import MockAuthService

# Futuro (con BD)
from src.auth.db_auth import DatabaseAuthService
```

---

## 🔧 Solución de Problemas

### Error: "ModuleNotFoundError: No module named 'flask'"
```bash
pip install flask flask-cors python-dotenv
```

### Error: "Connection refused" al conectar a /api/auth/login
- ✓ Asegurate que el servidor esté corriendo (`python app.py`)
- ✓ Usa la URL correcta: `http://localhost:5000`
- ✓ No `http://127.0.0.1:5000` (pueden tener diferencias)

### Error: "Session token not found"
- ✓ Primero debes hacer login en `/auth/login`
- ✓ Obtén el token en la respuesta JSON
- ✓ Este se pasa automáticamente en el navegador

### Las conversaciones desaparecieron tras reiniciar
- ✓ Esto es esperado (almacenamiento en memoria)
- ✓ Para persistencia, usa una base de datos real
- Ver sección "Próximos Pasos"

### Dashboard admin muestra "Sin datos"
- ✓ Primero crea algunas conversaciones como usuario
- ✓ Luego accede como admin para ver métricas

---

## 📊 Estructura del Proyecto

```
proyecto_senasoft/
├── app.py                              # 🔴 APP PRINCIPAL
├── requirements.txt
│
├── src/
│   ├── auth/
│   │   └── mock_auth.py                # 🟢 Autenticación Mock
│   ├── conversation/
│   │   └── mock_store.py               # 🟢 Conversaciones Mock
│   ├── api/
│   │   └── routes_mock.py              # 🟢 Rutas API
│   ├── chatbot/
│   │   └── chatbot_orchestrator.py     # Orquestador
│   └── ...
│
├── templates/
│   ├── auth/
│   │   └── login.html                  # 🟢 Login Page
│   ├── user/
│   │   ├── consent.html                # 🟢 Consent LSRPD
│   │   └── chat.html                   # 🟢 Chat Page
│   ├── admin/
│   │   └── dashboard.html              # 🟢 Admin Dashboard
│   └── ...
│
├── test_multi_user_system.py           # 🟢 Test Suite
├── MULTI_USER_SYSTEM_GUIDE.md          # 📖 Documentación
└── QUICK_START.md                      # 📖 Este archivo
```

🟢 = Archivos nuevos para sistema multi-usuario

---

## 🎓 Ejemplo: Login y Chat Completo

### Cliente JavaScript (Frontend)
```javascript
// 1. Login
const loginResponse = await fetch('/api/auth/login', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        email: 'user@boti.com',
        password: 'user123'
    })
});

const loginData = await loginResponse.json();
const token = loginData.session_token; // Se guarda automáticamente en cookies

// 2. Aceptar consentimiento
const consentResponse = await fetch('/api/auth/consent', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        consent_items: {
            datos_personales: true,
            menores: true
        }
    })
});

// 3. Crear conversación
const createResponse = await fetch('/api/chat/conversation/create', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({title: 'Mi primera conversación'})
});

const createData = await createResponse.json();
const convId = createData.conversation_id;

// 4. Enviar mensaje
const messageResponse = await fetch(`/api/chat/conversation/${convId}/message`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        message: 'Hola, necesito ayuda'
    })
});

const messageData = await messageResponse.json();
console.log(messageData.response); // Respuesta del bot
```

---

## ✨ Características Destacadas

- 🔐 **Autenticación sin BD** - Usuarios pre-cargados
- 📋 **LSRPD Compliance** - Consentimiento obligatorio
- 💬 **Multi-Conversación** - Múltiples chats por usuario
- 🎯 **Rol-Based Access** - Admin vs User
- 📊 **Dashboard Vivo** - Métricas en tiempo real
- 🚀 **API Completa** - 15+ endpoints
- 🧪 **Tests Incluidos** - Suite de validación
- 📱 **Responsive Design** - Funciona en móvil

---

## 📞 Support

Para más información:
- Ver: `MULTI_USER_SYSTEM_GUIDE.md`
- Revisar logs: `logs/app.log`
- Ejecutar tests: `python test_multi_user_system.py`

---

**¡Sistema listo para usar! 🎉**
