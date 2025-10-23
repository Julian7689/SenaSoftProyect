# 🤖 Sistema Multi-Usuario BOTI - Guía de Implementación

## 📋 Resumen Ejecutivo

Se ha implementado un **sistema completo multi-usuario** para el chatbot BOTI con autenticación LSRPD, gestión de conversaciones y panel de administración. **TODO está simulado en memoria** - no hay base de datos real.

---

## 🎯 Flujo de Usuario

```
┌─────────────┐
│  LOGIN PAGE │  (templates/auth/login.html)
│  Credenciales │
└──────┬──────┘
       │
       ├──→ Admin: token_admin123
       │    └─→ /admin/dashboard (panel de métricas)
       │
       └──→ User: token_user123
            └─→ /user/consent (consentimiento LSRPD)
                 └─→ /user/chat (interfaz de chat)
```

---

## 🔐 Demostración: Credenciales Pre-cargadas

### Admin
```
Email: admin@boti.com
Password: admin123
Rol: admin
```

### Usuario Regular
```
Email: user@boti.com
Password: user123
Rol: user
```

---

## 📂 Estructura de Archivos Creados

### 1. **Servicios Mock** (Sin Base de Datos)

#### `src/auth/mock_auth.py`
```
Clase: MockAuthService
├── register_user(email, username, password, name)
├── login(email, password, ip_address)
├── verify_session(session_token)
├── logout(session_token)
├── save_consent(email, consent_items, ip_address)
└── get_user_consent(email)

Almacenamiento Global (en memoria):
├── MOCK_USERS: {email: {password, username, role, name}}
├── ACTIVE_SESSIONS: {token: {user_id, email, role, expires_at}}
└── USER_CONSENTS: {email: {items, saved_at, policy_version}}
```

**Validación LSRPD:**
- 2 items OBLIGATORIOS:
  1. Datos personales (Artículo 6, Ley 1581/2016)
  2. Menores (Artículo 7 - confirmación edad/consentimiento)
- 3 items OPCIONALES
- No guarda datos reales, solo simula

#### `src/conversation/mock_store.py`
```
Clase: MockConversationStore
├── create_conversation(user_email, title, topic)
├── add_message(user_email, conv_id, sender, content, intent, entities)
├── get_conversation_history(user_email, conv_id, limit=100)
├── get_user_conversations(user_email)
├── set_context(user_email, conv_id, key, value)
├── get_context(user_email, conv_id)
└── delete_conversation(user_email, conv_id)

Almacenamiento Global (en memoria):
├── CONVERSATIONS_STORAGE: {user_email: {conv_id: {messages: [...]}}}
└── CONTEXT_STORAGE: {user_email: {conv_id: {region, problem, keywords}}}
```

### 2. **Rutas API** 

#### `src/api/routes_mock.py` (350 líneas)

**Blueprint: `auth_bp` (/api/auth/**)**
```python
POST /api/auth/register
  Input: {email, username, password, name}
  Output: {success, user_id, message}

POST /api/auth/login
  Input: {email, password}
  Output: {success, session_token, user: {email, username, role}}

GET /api/auth/verify
  Output: {success, user: {email, username, role}, session_active}

POST /api/auth/logout
  Output: {success, message}

GET/POST /api/auth/consent
  Input (POST): {consent_items: {datos_personales, menores, ...}}
  Output: {success, message}
```

**Blueprint: `chat_bp` (/api/chat/**)**
```python
GET /api/chat/conversations
  Output: {success, conversations: [{conversation_id, title, message_count}]}

POST /api/chat/conversation/create
  Input: {title}
  Output: {success, conversation_id}

GET /api/chat/conversation/<id>/history
  Output: {success, messages: [{sender, content, timestamp}]}

POST /api/chat/conversation/<id>/message
  Input: {message}
  Output: {success, response, bot_intent}
  → Integra ChatbotOrchestrator

GET /api/chat/conversation/<id>/delete
  Output: {success}
```

**Blueprint: `admin_bp` (/api/admin/**)**
```python
GET /api/admin/dashboard-data
  Output: {success, data: {
    total_users: int,
    total_conversations: int,
    children_connected: int,
    active_sponsors: int,
    regions_covered: int,
    users_by_region: {region: count},
    latest_users: [...]
  }}

GET /api/admin/users
  Output: {success, users: [{email, role, conversations, consent}]}
```

### 3. **Páginas HTML**

#### `templates/auth/login.html` (200 líneas)
- Formulario de login con email/password
- Credenciales demo mostradas
- Estilos gradiente púrpura
- Redirección automática según rol
- JavaScript para enviar credenciales a `/api/auth/login`

#### `templates/user/consent.html` (350 líneas)
- ✅ **LSRPD Compliance Page**
- 5 checkboxes con referencias legales
- 2 OBLIGATORIOS (datos personales + menores)
- 3 OPCIONALES (anonimizado, reportes, sponsors)
- Validación JavaScript (deshabilita botón hasta que items requeridos estén checked)
- Envía datos a `/api/auth/consent`
- Redirige a `/user/chat` tras éxito

#### `templates/user/chat.html` (500 líneas)
- **Interfaz de Chat Multi-Conversación**
- Sidebar izquierdo con lista de conversaciones
- Área principal con mensajes
- Input de mensajes en la base
- Botón "Nuevo Chat" para crear conversación
- Carga automática de conversaciones del usuario
- Envía mensajes a `/api/chat/conversation/<id>/message`
- Muestra respuestas del orquestador conversacional

#### `templates/admin/dashboard.html` (550 líneas)
- **Panel de Administración**
- Tarjetas de estadísticas (6 KPIs principales)
- Gráficos con Chart.js
  - Usuarios por Región (bar chart)
  - Distribución de Roles (doughnut chart)
- Tabla de últimos usuarios registrados
- Tabla de estadísticas detalladas
- Auto-refresco cada 30 segundos
- Botón de logout para admins

---

## 🔄 Flujo de Datos

### 1. **Registro / Login**
```
Usuario ingresa credenciales
    ↓
POST /api/auth/login
    ↓
MockAuthService.login() valida en MOCK_USERS
    ↓
Genera session_token (UUID + hora expiración)
    ↓
Guarda en ACTIVE_SESSIONS
    ↓
Retorna token al cliente
```

### 2. **Consentimiento LSRPD**
```
Usuario ve /user/consent
    ↓
Lee políticas privacidad y checkea items
    ↓
POST /api/auth/consent con items seleccionados
    ↓
MockAuthService.save_consent() valida items REQUERIDOS
    ↓
Guarda en USER_CONSENTS (sin datos reales)
    ↓
Redirige a /user/chat
```

### 3. **Chat Multi-Conversación**
```
Usuario accede /user/chat
    ↓
GET /api/chat/conversations carga lista
    ↓
Usuario selecciona o crea nueva conversación
    ↓
GET /api/chat/conversation/<id>/history carga mensajes
    ↓
Usuario escribe y presiona enviar
    ↓
POST /api/chat/conversation/<id>/message
    ↓
Routes llama ChatbotOrchestrator.process_message()
    ↓
Respuesta guardada en CONVERSATIONS_STORAGE
    ↓
Se muestra en chat
```

### 4. **Admin Dashboard**
```
Admin accede /admin/dashboard
    ↓
GET /api/admin/dashboard-data
    ↓
Routes genera datos simulados desde MOCK_USERS y CONVERSATIONS_STORAGE
    ↓
Retorna JSON con métricas
    ↓
Charts.js grafica datos en navegador
```

---

## 🧪 Testing Manual

### 1. **Iniciar Servidor**
```bash
cd c:\Users\AdminSena\proyecto_senasoft
python app.py
```

### 2. **Login como Usuario**
- URL: http://localhost:5000/auth/login
- Email: user@boti.com
- Password: user123
- Redirección esperada: /user/consent

### 3. **Aceptar Consentimiento LSRPD**
- Checkear items obligatorios (datos personales + menores)
- Clickear "Aceptar y Continuar"
- Redirección esperada: /user/chat

### 4. **Usar Chat**
- Crear nueva conversación con botón "+ Nuevo Chat"
- Escribir mensaje
- Ver respuesta del bot
- Ver contexto mantenido

### 5. **Login como Admin**
- URL: http://localhost:5000/auth/login
- Email: admin@boti.com
- Password: admin123
- Acceso directo a /admin/dashboard

### 6. **Dashboard Admin**
- Ver métricas de usuarios, conversaciones, etc.
- Gráficos muestran datos simulados
- Botón "🔄 Actualizar" recarga datos
- Auto-refresco cada 30 segundos

---

## 🏗️ Arquitectura en Memoria

```
┌─────────────────────────────────────────────────┐
│           BOTI Multi-Usuario System              │
├─────────────────────────────────────────────────┤
│ FRONT-END (Templates + JavaScript)              │
│ ├─ auth/login.html (formulario)                 │
│ ├─ user/consent.html (LSRPD)                    │
│ ├─ user/chat.html (chat principal)              │
│ └─ admin/dashboard.html (métricas)              │
├─────────────────────────────────────────────────┤
│ API ROUTES (Flask Blueprints)                   │
│ ├─ auth_bp (login, register, logout, consent)   │
│ ├─ chat_bp (conversations, messages, history)   │
│ └─ admin_bp (dashboard data, users)             │
├─────────────────────────────────────────────────┤
│ MOCK SERVICES (Sin DB)                          │
│ ├─ MockAuthService                              │
│ │  └─ Almacenamiento: MOCK_USERS, SESSIONS,    │
│ │     CONSENTS                                   │
│ └─ MockConversationStore                        │
│    └─ Almacenamiento: CONVERSATIONS_STORAGE,   │
│       CONTEXT_STORAGE                           │
├─────────────────────────────────────────────────┤
│ BUSINESS LOGIC                                  │
│ ├─ ChatbotOrchestrator (respuestas)             │
│ ├─ ConversationMemory (contexto)                │
│ ├─ ResponseGenerator (generación dinámica)      │
│ └─ SponsorManager (modelo empresarial)          │
└─────────────────────────────────────────────────┘
```

---

## ⚡ Características Implementadas

### ✅ Autenticación Multi-Rol
- Admin y Usuario
- Tokens de sesión (no JWT)
- Expiración en 7 días
- Logout y verificación

### ✅ Cumplimiento LSRPD
- 5 checkboxes con referencias legales
- Artículos de Ley 1581/2016
- Confirmación de mayoría de edad
- Consentimiento para compartir datos anónimos
- No guarda datos reales (simulado)

### ✅ Gestión de Conversaciones
- Múltiples conversaciones por usuario
- Historial de mensajes
- Contexto persistente (región, problema, keywords)
- Eliminación de conversaciones

### ✅ Dashboard Admin
- 6 KPIs principales
- Gráficos en tiempo real (simulados)
- Lista de usuarios con roles
- Estadísticas detalladas
- Auto-refresco

### ✅ Sin Base de Datos
- Almacenamiento en memoria (diccionarios Python)
- Perdidos al reiniciar servidor
- Perfecto para prototipos/demos
- Fácil de convertir a BD real

---

## 🚀 Próximos Pasos (Opcionales)

### 1. **Persistencia en BD Real**
```python
# Reemplazar en-memoria con:
# - PostgreSQL para users/sessions
# - MongoDB para conversaciones
# - Redis para caché de sesiones
```

### 2. **WebSockets para Tiempo Real**
```python
# Actualizar dashboard admin con Socket.io
# Métricas vivas mientras usuarios escriben
```

### 3. **Autenticación Mejorada**
```python
# - Agregar JWT tokens
# - 2FA (autenticación de dos factores)
# - OAuth con Google/Microsoft
```

### 4. **Análisis Avanzado**
```python
# - Exportar conversaciones
# - Reportes por región
# - Análisis de sentimiento
```

---

## 📝 Archivos Modificados

### `app.py`
- ✅ Agregadas importaciones: MockAuthService, MockConversationStore, routes_mock
- ✅ Agregadas variables globales: auth_service, conversation_store
- ✅ Nuevas rutas: /auth/login, /user/consent, /user/chat, /admin/dashboard
- ✅ Registro de blueprints en __main__

### Archivos Creados
1. `src/auth/mock_auth.py` ✨ NEW
2. `src/conversation/mock_store.py` ✨ NEW
3. `src/api/routes_mock.py` ✨ NEW
4. `templates/auth/login.html` ✨ NEW
5. `templates/user/consent.html` ✨ NEW
6. `templates/user/chat.html` ✨ NEW
7. `templates/admin/dashboard.html` ✨ NEW

---

## 🔍 Validación Técnica

### Validaciones Implementadas

#### En Backend (Flask Routes)
```python
# Todas las rutas verifican session_token
# - Validan formato del token
# - Verifican que no haya expirado
# - Validan rol del usuario (admin vs user)
```

#### En Frontend (JavaScript)
```javascript
// Validación de formularios
// - Email formato
// - Contraseña requerida
// - Items LSRPD obligatorios

// Validación de sesión
// - Si no hay token: redirige a /auth/login
// - Si token expirado: logout automático
```

---

## 📊 Datos Simulados

El dashboard admin muestra:
```json
{
  "total_users": 2,
  "total_conversations": 3,
  "children_connected": 1,
  "active_sponsors": 2,
  "regions_covered": 5,
  "users_by_region": {
    "Bogotá": 1,
    "Medellín": 1,
    "Valle": 0,
    "Costa": 0,
    "Eje Cafetero": 0
  },
  "latest_users": [
    {"email": "admin@boti.com", "role": "admin", "consent": true},
    {"email": "user@boti.com", "role": "user", "consent": false}
  ]
}
```

---

## 🛠️ Troubleshooting

### Problema: "404 Not Found" en /auth/login
**Solución**: Asegurate que `templates/auth/login.html` existe

### Problema: "Session token not found"
**Solución**: Login correctamente primero, luego accede a /user/consent

### Problema: Mensajes no se envían
**Solución**: 
- Verifica que ChatbotOrchestrator está inicializado
- Revisa logs de /api/chat/conversation/<id>/message

### Problema: Dashboard admin no carga datos
**Solución**: Admin debe estar logueado con token válido

---

## 📞 Resumen Rápido

| Componente | Ubicación | Tipo | Estado |
|-----------|-----------|------|--------|
| Autenticación | MockAuthService | Mock | ✅ |
| Conversaciones | MockConversationStore | Mock | ✅ |
| Chat API | routes_mock.py | Routes | ✅ |
| Login UI | templates/auth/login.html | HTML | ✅ |
| Consentimiento | templates/user/consent.html | HTML | ✅ |
| Chat UI | templates/user/chat.html | HTML | ✅ |
| Admin UI | templates/admin/dashboard.html | HTML | ✅ |

---

**Sistema completamente funcional sin base de datos. Todos los datos se pierden al reiniciar.**
