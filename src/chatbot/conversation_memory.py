"""
ConversationMemory: Gestor avanzado de contexto para mantener coherencia en conversaciones
Rastrea: región, problema principal, keywords, historial, estado, intenciones previas
"""

from typing import Dict, List, Optional, Set
from datetime import datetime
from dataclasses import dataclass, field, asdict
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class MessageContext:
    """Contexto de un mensaje individual"""
    timestamp: str
    user_message: str
    intent: str
    confidence: float
    region: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    entities: Dict = field(default_factory=dict)
    bot_response: str = ""
    is_question: bool = False  # ¿El bot preguntó algo?
    question_topic: Optional[str] = None  # ¿Sobre qué preguntó? (región, problema, etc.)


class ConversationMemory:
    """
    Gestor inteligente de memoria de conversación
    - Rastrea región detectada (y no la olvida)
    - Rastrea problema principal mencionado
    - Rastrea todas las palabras clave
    - Rastrea preguntas ya hechas (no las repite)
    - Genera respuestas coherentes basadas en historial
    """
    
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.messages: List[MessageContext] = []
        
        # Estado persistente de la conversación
        self.confirmed_region: Optional[str] = None  # Región detectada
        self.primary_problem: Optional[str] = None  # Problema principal (conectividad, educación, etc.)
        self.all_keywords: Set[str] = set()  # Todas las palabras clave mencionadas
        self.asked_about: Set[str] = set()  # Preguntas ya hechas
        self.conversation_stage: str = "initial"  # initial, gathering_info, analyzing, proposing, closing
        self.user_profile: Dict = {}  # Perfil del usuario
        self.related_intents: List[str] = []  # Intenciones previas en orden
        
        logger.info(f"ConversationMemory inicializada para usuario: {user_id}")
    
    def add_message(
        self,
        user_message: str,
        intent: str,
        confidence: float,
        entities: Dict,
        bot_response: str = "",
        is_question: bool = False,
        question_topic: Optional[str] = None
    ) -> MessageContext:
        """Agrega un mensaje al historial y actualiza estado"""
        
        msg_context = MessageContext(
            timestamp=datetime.now().isoformat(),
            user_message=user_message,
            intent=intent,
            confidence=confidence,
            region=entities.get('region'),
            keywords=entities.get('keywords', []),
            entities=entities,
            bot_response=bot_response,
            is_question=is_question,
            question_topic=question_topic
        )
        
        self.messages.append(msg_context)
        
        # Actualizar estado persistente
        self._update_state(msg_context)
        
        logger.debug(f"Mensaje agregado. Región confirmada: {self.confirmed_region}, "
                    f"Problema: {self.primary_problem}")
        
        return msg_context
    
    def _update_state(self, msg_context: MessageContext):
        """Actualiza el estado persistente basado en nuevo mensaje"""
        
        # Actualizar región (una vez detectada, no cambia)
        if msg_context.region and not self.confirmed_region:
            self.confirmed_region = msg_context.region
            logger.info(f"Región confirmada: {self.confirmed_region}")
        
        # Actualizar problema principal
        if msg_context.intent in ['conectividad', 'educacion', 'mejora']:
            if not self.primary_problem:
                self.primary_problem = msg_context.intent
                logger.info(f"Problema principal identificado: {self.primary_problem}")
        
        # Acumular palabras clave
        self.all_keywords.update(msg_context.keywords)
        
        # Registrar que se preguntó
        if msg_context.is_question and msg_context.question_topic:
            self.asked_about.add(msg_context.question_topic)
        
        # Actualizar intenciones relacionadas
        if msg_context.intent not in self.related_intents:
            self.related_intents.append(msg_context.intent)
        
        # Actualizar etapa de conversación
        self._update_stage()
    
    def _update_stage(self):
        """Actualiza la etapa actual de conversación"""
        if not self.messages:
            self.conversation_stage = "initial"
        elif len(self.messages) == 1:
            self.conversation_stage = "initial"
        elif self.confirmed_region and self.primary_problem:
            if any(m.intent == 'prediccion' for m in self.messages[-3:]):
                self.conversation_stage = "analyzing"
            elif any(m.intent == 'mejora' for m in self.messages[-3:]):
                self.conversation_stage = "proposing"
            else:
                self.conversation_stage = "gathering_info"
        else:
            self.conversation_stage = "gathering_info"
    
    def get_context_summary(self) -> Dict:
        """Obtiene un resumen del contexto actual"""
        return {
            'confirmed_region': self.confirmed_region,
            'primary_problem': self.primary_problem,
            'keywords': list(self.all_keywords),
            'stage': self.conversation_stage,
            'message_count': len(self.messages),
            'intents_sequence': self.related_intents,
            'asked_about': list(self.asked_about),
            'last_message': self.messages[-1].user_message if self.messages else None,
            'last_intent': self.messages[-1].intent if self.messages else None
        }
    
    def get_previous_messages_about(self, topic: str, limit: int = 3) -> List[MessageContext]:
        """Obtiene mensajes previos sobre un tema específico"""
        relevant = [m for m in self.messages if topic in m.keywords or m.intent == topic]
        return relevant[-limit:]
    
    def was_asked_about(self, topic: str) -> bool:
        """Verifica si ya se preguntó sobre algo"""
        return topic in self.asked_about
    
    def should_ask_for_region(self) -> bool:
        """Determina si deberíamos preguntar por región"""
        # NO preguntar si ya tenemos región confirmada
        if self.confirmed_region:
            return False
        # Preguntar solo si hace falta y no la hemos pedido
        return 'region' not in self.asked_about and len(self.messages) > 1
    
    def should_ask_for_problem(self) -> bool:
        """Determina si deberíamos preguntar por el problema principal"""
        if self.primary_problem:
            return False
        return 'problem' not in self.asked_about and len(self.messages) > 2
    
    def get_last_messages(self, n: int = 3) -> List[MessageContext]:
        """Obtiene los últimos N mensajes"""
        return self.messages[-n:]
    
    def get_conversation_flow(self) -> str:
        """Obtiene descripción del flujo de conversación"""
        if not self.messages:
            return "Sin historial"
        
        flow = []
        for msg in self.messages[-4:]:  # Últimos 4 mensajes
            flow.append(f"{msg.intent.upper()}: {msg.user_message[:50]}...")
        
        return " → ".join(flow)
    
    def export(self) -> Dict:
        """Exporta todo el estado de la conversación"""
        return {
            'user_id': self.user_id,
            'confirmed_region': self.confirmed_region,
            'primary_problem': self.primary_problem,
            'keywords': list(self.all_keywords),
            'conversation_stage': self.conversation_stage,
            'message_count': len(self.messages),
            'intents_sequence': self.related_intents,
            'messages': [asdict(m) for m in self.messages]
        }
    
    def reset(self):
        """Reinicia la memoria de conversación"""
        self.messages = []
        self.confirmed_region = None
        self.primary_problem = None
        self.all_keywords = set()
        self.asked_about = set()
        self.conversation_stage = "initial"
        self.user_profile = {}
        self.related_intents = []
        logger.info(f"ConversationMemory reiniciada para usuario: {self.user_id}")
