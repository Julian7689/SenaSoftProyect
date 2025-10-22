/**
 * MÓDULO: Smart Chat Interface
 * Integración del Chat Inteligente con Orquestador
 * Soporta: NLP + Predicción + Generación de Mejoras
 */

class SmartChatInterface {
    /**
     * Constructor
     * @param {Object} options - Configuración
     * - chatContainerId: ID del contenedor del chat
     * - messageInputId: ID del input de mensajes
     * - sendButtonId: ID del botón enviar
     * - useOrchestrator: Usar orquestador (true/false)
     */
    constructor(options = {}) {
        this.chatContainerId = options.chatContainerId || 'chat-messages';
        this.messageInputId = options.messageInputId || 'message-input';
        this.sendButtonId = options.sendButtonId || 'send-button';
        this.useOrchestrator = options.useOrchestrator !== false;
        
        this.chatContainer = document.getElementById(this.chatContainerId);
        this.messageInput = document.getElementById(this.messageInputId);
        this.sendButton = document.getElementById(this.sendButtonId);
        
        this.messages = [];
        this.userRegion = null;
        this.lastPrediction = null;
        
        this.init();
    }
    
    init() {
        // Validar elementos
        if (!this.chatContainer) {
            console.warn(`⚠ Chat container with ID '${this.chatContainerId}' not found`);
            return;
        }
        
        // Event listeners
        if (this.sendButton) {
            this.sendButton.addEventListener('click', () => this.handleSendMessage());
        }
        
        if (this.messageInput) {
            this.messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.handleSendMessage();
                }
            });
        }
        
        console.log('✓ SmartChatInterface inicializado');
    }
    
    /**
     * Maneja el envío de mensaje
     */
    async handleSendMessage() {
        const message = this.messageInput.value.trim();
        
        if (!message) {
            console.warn('Mensaje vacío');
            return;
        }
        
        // Mostrar mensaje del usuario
        this.displayMessage(message, 'user');
        this.messageInput.value = '';
        this.messageInput.focus();
        
        // Mostrar indicador de escritura
        this.showTypingIndicator();
        
        try {
            // Enviar al servidor
            const response = await this.sendMessageToServer(message);
            
            // Remover indicador de escritura
            this.removeTypingIndicator();
            
            // Procesar respuesta
            await this.processResponse(response);
            
        } catch (error) {
            console.error('Error enviando mensaje:', error);
            this.removeTypingIndicator();
            this.displayMessage('Error: No se pudo procesar tu mensaje. Intenta nuevamente.', 'bot-error');
        }
    }
    
    /**
     * Envía mensaje al servidor
     */
    async sendMessageToServer(message) {
        const endpoint = this.useOrchestrator ? '/api/chat-intelligent' : '/api/message';
        
        const payload = {
            message: message
        };
        
        // Agregar datos del usuario si existen
        if (this.lastPrediction) {
            payload.user_data = this.lastPrediction.data;
        }
        
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    }
    
    /**
     * Procesa la respuesta del servidor
     */
    async processResponse(response) {
        // Mostrar respuesta principal
        this.displayMessage(response.response, 'bot');
        
        // Guardar en historial
        this.messages.push({
            user: this.messageInput.value,
            bot: response.response,
            timestamp: response.timestamp,
            intent: response.intent || null,
            entities: response.entities || {}
        });
        
        // Mostrar información adicional si está disponible
        if (response.intent) {
            this.displayIntentInfo(response);
        }
        
        // Mostrar predicción si se ejecutó
        if (response.prediction && response.prediction.executed) {
            this.displayPredictionResult(response.prediction);
            this.lastPrediction = {
                data: response.user_data,
                result: response.prediction
            };
        }
        
        // Mostrar mejoras si se generaron
        if (response.improvements && response.improvements.executed) {
            this.displayImprovements(response.improvements);
        }
        
        // Actualizar región si se detectó
        if (response.region) {
            this.userRegion = response.region;
        }
        
        // Auto-scroll
        this.scrollToBottom();
    }
    
    /**
     * Muestra información de la intención detectada
     */
    displayIntentInfo(response) {
        const intentDiv = document.createElement('div');
        intentDiv.className = 'chat-intent-info';
        intentDiv.innerHTML = `
            <small>
                🎯 Intención: <strong>${response.intent}</strong> 
                (confianza: ${(response.intent_confidence * 100).toFixed(1)}%)
            </small>
        `;
        this.chatContainer.appendChild(intentDiv);
    }
    
    /**
     * Muestra resultado de predicción
     */
    displayPredictionResult(prediction) {
        if (!prediction.executed) return;
        
        const resultDiv = document.createElement('div');
        resultDiv.className = 'chat-prediction-result';
        
        const icon = prediction.prediction === 1 ? '🟢' : '🔴';
        const text = prediction.interpretation || 'Predicción completada';
        
        resultDiv.innerHTML = `
            <div class="prediction-header">
                ${icon} <strong>Resultado de Análisis</strong>
            </div>
            <div class="prediction-body">
                <p>${text}</p>
                <div class="prediction-probs">
                    <div>Sin acceso: ${(prediction.probability_no_access * 100).toFixed(1)}%</div>
                    <div>Con acceso: ${(prediction.probability_with_access * 100).toFixed(1)}%</div>
                </div>
            </div>
        `;
        
        this.chatContainer.appendChild(resultDiv);
    }
    
    /**
     * Muestra mejoras generadas
     */
    displayImprovements(improvements) {
        if (!improvements.executed || !improvements.proposals) return;
        
        const impDiv = document.createElement('div');
        impDiv.className = 'chat-improvements';
        
        let html = `
            <div class="improvements-header">
                💡 <strong>Propuestas de Mejora (${improvements.n_proposals})</strong>
            </div>
            <div class="improvements-body">
        `;
        
        improvements.proposals.forEach((proposal, idx) => {
            html += `
                <div class="improvement-proposal">
                    <h4>Propuesta ${proposal.proposal_id} (Intensidad: ${proposal.strength.toFixed(0)}%)</h4>
                    <ul>
            `;
            
            // Mostrar top 3 cambios
            const features = Object.entries(proposal.features).slice(0, 3);
            features.forEach(([feature, value]) => {
                html += `<li>${feature}: ${value.toFixed(2)}</li>`;
            });
            
            html += `
                    </ul>
                </div>
            `;
        });
        
        html += `</div>`;
        impDiv.innerHTML = html;
        this.chatContainer.appendChild(impDiv);
    }
    
    /**
     * Muestra un mensaje en el chat
     */
    displayMessage(message, sender = 'bot') {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message chat-${sender}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = message;
        
        messageDiv.appendChild(contentDiv);
        this.chatContainer.appendChild(messageDiv);
        
        this.scrollToBottom();
    }
    
    /**
     * Muestra indicador de que el bot está escribiendo
     */
    showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.id = 'typing-indicator';
        typingDiv.className = 'chat-typing-indicator';
        typingDiv.innerHTML = `
            <div class="typing-bubble"></div>
            <div class="typing-bubble"></div>
            <div class="typing-bubble"></div>
        `;
        this.chatContainer.appendChild(typingDiv);
        this.scrollToBottom();
    }
    
    /**
     * Remueve indicador de escritura
     */
    removeTypingIndicator() {
        const typing = document.getElementById('typing-indicator');
        if (typing) {
            typing.remove();
        }
    }
    
    /**
     * Auto-scroll al fondo
     */
    scrollToBottom() {
        if (this.chatContainer) {
            setTimeout(() => {
                this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
            }, 100);
        }
    }
    
    /**
     * Obtiene historial de conversación
     */
    async getHistory() {
        try {
            const response = await fetch('/api/chat-history');
            const data = await response.json();
            return data.history || [];
        } catch (error) {
            console.error('Error obteniendo historial:', error);
            return [];
        }
    }
    
    /**
     * Reinicia el contexto
     */
    async resetContext() {
        try {
            await fetch('/api/chat-reset', { method: 'POST' });
            this.messages = [];
            this.userRegion = null;
            this.lastPrediction = null;
            this.chatContainer.innerHTML = '';
            console.log('✓ Contexto reiniciado');
        } catch (error) {
            console.error('Error reiniciando contexto:', error);
        }
    }
    
    /**
     * Exporta la conversación
     */
    async exportConversation() {
        try {
            const response = await fetch('/api/chat-export');
            const data = await response.json();
            
            // Descargar como JSON
            const blob = new Blob([JSON.stringify(data.export, null, 2)], {
                type: 'application/json'
            });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `chat-export-${new Date().toISOString()}.json`;
            a.click();
            
            console.log('✓ Conversación exportada');
        } catch (error) {
            console.error('Error exportando conversación:', error);
        }
    }
}

// Exportar para uso global
window.SmartChatInterface = SmartChatInterface;

console.log('✓ smart-chat-interface.js cargado');
