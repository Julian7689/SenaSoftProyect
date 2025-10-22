/**
 * JavaScript para el Chatbot de Apoyo
 * Maneja la interacción del usuario con el chat
 */

// We'll query DOM inside DOMContentLoaded to avoid null refs
let chatForm = null;
let messageInput = null;
let sendButton = null;
let chatMessages = null;
let typingIndicator = null;

// ID de sesión único para el usuario
let sessionId = generateSessionId();

// ==================== INICIALIZACIÓN ====================
document.addEventListener('DOMContentLoaded', () => {
    try {
        console.log('Chat inicializado');

        chatForm = document.getElementById('chatForm');
        messageInput = document.getElementById('messageInput');
        sendButton = document.getElementById('sendButton');
        chatMessages = document.getElementById('chatMessages');
        typingIndicator = document.getElementById('typingIndicator');

        if (messageInput) messageInput.focus();

        // Event listener para el formulario
        if (chatForm) {
            chatForm.addEventListener('submit', handleSendMessage);
        }

        // Auto-resize del textarea (guardado)
        if (messageInput) {
            messageInput.addEventListener('input', () => {
                messageInput.style.height = 'auto';
                messageInput.style.height = messageInput.scrollHeight + 'px';
            });

            // Enviar con Ctrl+Enter
            messageInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && e.ctrlKey) {
                    e.preventDefault();
                    handleSendMessage(e);
                }
            });
        }
    } catch (err) {
        console.error('Error inicializando chat DOM:', err);
    }
});

// ==================== FUNCIONES PRINCIPALES ====================

/**
 * Manejar el envío de mensajes
 */
async function handleSendMessage(e) {
    e.preventDefault();
    if (!messageInput) return;

    const message = messageInput.value.trim();
    if (!message) return;

    // Deshabilitar input mientras se procesa
    disableInput();

    // Agregar mensaje del usuario al chat (localmente) y en consola para debug
    try {
        addMessageToChat(message, 'user');
    } catch (err) {
        console.error('Error agregando mensaje localmente:', err);
    }

    // Limpiar input
    messageInput.value = '';
    messageInput.style.height = 'auto';

    // Mostrar indicador de escritura
    showTypingIndicator();
    
    try {
        // Enviar mensaje al backend
        const response = await sendMessageToAPI(message);
        
        // Ocultar indicador de escritura
        hideTypingIndicator();
        
        // Agregar respuesta del bot
        addMessageToChat(response.response, 'bot', response);
        
        // Manejar urgencia si es necesaria
        if (response.urgency === 'critical' || response.urgency === 'high') {
            showUrgencyAlert(response);
        }
        
    } catch (error) {
        console.error('Error enviando mensaje:', error);
        hideTypingIndicator();
        addMessageToChat(
            'Lo siento, ha ocurrido un error. Por favor intenta de nuevo. Si es una emergencia, llama al 123.',
            'bot',
            { urgency: 'high' }
        );
    } finally {
        enableInput();
        if (messageInput) messageInput.focus();
    }
}

/**
 * Enviar mensaje a la API
 */
async function sendMessageToAPI(message) {
    const response = await fetch('/api/message', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            message: message,
            session_id: sessionId
        })
    });
    
    if (!response.ok) {
        throw new Error('Error en la respuesta del servidor');
    }
    
    return await response.json();
}

/**
 * Agregar mensaje al chat con animaciones mejoradas
 */
function addMessageToChat(text, sender, data = null) {
    // Validar que chatMessages exista
    if (!chatMessages) {
        chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) {
            console.warn('chatMessages no encontrado, mensaje no se añadirá al DOM');
            return;
        }
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    messageDiv.style.opacity = '0';
    messageDiv.style.transform = 'translateY(20px)';
    
    if (sender === 'bot') {
        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message-avatar';
        avatarDiv.innerHTML = `
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <path d="M8 14s1.5 2 4 2 4-2 4-2"/>
                <line x1="9" y1="9" x2="9.01" y2="9"/>
                <line x1="15" y1="9" x2="15.01" y2="9"/>
            </svg>
        `;
        messageDiv.appendChild(avatarDiv);
    }
    
    const wrapperDiv = document.createElement('div');
    wrapperDiv.className = sender === 'bot' ? 'message-wrapper' : '';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    const textP = document.createElement('p');
    textP.textContent = text;
    contentDiv.appendChild(textP);
    
    // Agregar recursos si están disponibles
    if (data && data.resources && data.resources.length > 0) {
        const resourcesDiv = createResourcesElement(data.resources);
        contentDiv.appendChild(resourcesDiv);
    }
    
    const timeSpan = document.createElement('span');
    timeSpan.className = 'message-time';
    timeSpan.textContent = getCurrentTime();
    
    if (sender === 'bot') {
        wrapperDiv.appendChild(contentDiv);
        wrapperDiv.appendChild(timeSpan);
        messageDiv.appendChild(wrapperDiv);
    } else {
        messageDiv.appendChild(contentDiv);
        messageDiv.appendChild(timeSpan);
    }
    
    chatMessages.appendChild(messageDiv);
    
    // Animación de entrada
    requestAnimationFrame(() => {
        messageDiv.style.transition = 'all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275)';
        messageDiv.style.opacity = '1';
        messageDiv.style.transform = 'translateY(0)';
    });
    
    // Scroll al final con animación suave
    scrollToBottom();
}

/**
 * Crear elemento de recursos
 */
function createResourcesElement(resources) {
    const div = document.createElement('div');
    div.className = 'message-resources';
    div.style.marginTop = '1rem';
    div.style.padding = '0.75rem';
    div.style.backgroundColor = 'rgba(99, 102, 241, 0.1)';
    div.style.borderRadius = '8px';
    
    const title = document.createElement('strong');
    title.textContent = '📞 Recursos disponibles:';
    div.appendChild(title);
    
    const ul = document.createElement('ul');
    ul.style.marginTop = '0.5rem';
    ul.style.marginLeft = '1rem';
    
    resources.forEach(resource => {
        const li = document.createElement('li');
        li.textContent = resource;
        ul.appendChild(li);
    });
    
    div.appendChild(ul);
    return div;
}

/**
 * Mostrar alerta de urgencia
 */
function showUrgencyAlert(data) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'urgency-alert';
    alertDiv.style.cssText = `
        background-color: #fef2f2;
        border: 2px solid #ef4444;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        animation: pulse 2s infinite;
    `;
    
    alertDiv.innerHTML = `
        <strong style="color: #ef4444; font-size: 1.1rem;">⚠️ Atención Urgente</strong>
        <p style="margin-top: 0.5rem;">
            Si estás en peligro inmediato, por favor llama al <strong>123</strong> ahora mismo.
        </p>
        <button onclick="this.parentElement.remove()" 
                style="margin-top: 1rem; padding: 0.5rem 1rem; background: #ef4444; 
                       color: white; border: none; border-radius: 6px; cursor: pointer;">
            Entendido
        </button>
    `;
    
    chatMessages.appendChild(alertDiv);
    scrollToBottom();
}

/**
 * Mostrar indicador de escritura
 */
function showTypingIndicator() {
    if (typingIndicator) {
        typingIndicator.style.display = 'flex';
    }
}

/**
 * Ocultar indicador de escritura
 */
function hideTypingIndicator() {
    if (typingIndicator) {
        typingIndicator.style.display = 'none';
    }
}

/**
 * Deshabilitar input mientras se procesa
 */
function disableInput() {
    messageInput.disabled = true;
    sendButton.disabled = true;
}

/**
 * Habilitar input
 */
function enableInput() {
    messageInput.disabled = false;
    sendButton.disabled = false;
}

/**
 * Scroll automático al final del chat con animación suave
 */
function scrollToBottom() {
    chatMessages.scrollTo({
        top: chatMessages.scrollHeight,
        behavior: 'smooth'
    });
}

/**
 * Obtener hora actual formateada
 */
function getCurrentTime() {
    const now = new Date();
    const hours = now.getHours().toString().padStart(2, '0');
    const minutes = now.getMinutes().toString().padStart(2, '0');
    return `${hours}:${minutes}`;
}

/**
 * Generar ID de sesión único
 */
function generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// ==================== FUNCIONES AUXILIARES ====================

/**
 * Detectar palabras de emergencia
 */
function detectEmergencyKeywords(message) {
    const emergencyKeywords = [
        'emergencia', 'peligro', 'ayuda urgente', 'me va a matar',
        'socorro', 'ahora', 'rápido'
    ];
    
    const lowerMessage = message.toLowerCase();
    return emergencyKeywords.some(keyword => lowerMessage.includes(keyword));
}

// Agregar estilos para la animación de pulse
const style = document.createElement('style');
style.textContent = `
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.8; }
    }
`;
document.head.appendChild(style);
