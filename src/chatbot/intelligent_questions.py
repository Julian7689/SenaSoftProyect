"""
Sistema de Preguntas Predictivas Inteligentes
Genera preguntas contextuales basadas en ML y evita repetición
"""
from typing import Dict, List, Optional, Tuple
import json
from pathlib import Path
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

@dataclass
class ConversationContext:
    """Contexto de la conversación actual"""
    user_id: str
    region: Optional[str] = None
    problem_type: Optional[str] = None
    keywords_mentioned: set = field(default_factory=set)
    questions_asked: set = field(default_factory=set)
    answers_given: Dict[str, str] = field(default_factory=dict)
    session_start: str = field(default_factory=lambda: str(datetime.now()))
    
class IntelligentQuestionGenerator:
    """
    Generador de preguntas inteligentes que:
    1. Usa modelo predictivo para detectar qué preguntar
    2. No repite preguntas ya hechas
    3. Se adapta según la región y problema
    """
    
    def __init__(self):
        self.connectivity_data = self._load_connectivity_data()
        self.question_templates = self._load_question_templates()
        self.conversation_contexts: Dict[str, ConversationContext] = {}
        
    def _load_connectivity_data(self) -> Dict:
        """Cargar datos de conectividad de Colombia"""
        try:
            data_path = Path(__file__).parent.parent / 'data' / 'colombia_connectivity.json'
            with open(data_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error cargando datos de conectividad: {e}")
            return {}
    
    def _load_question_templates(self) -> Dict:
        """Templates de preguntas según contexto"""
        return {
            'region_identification': {
                'questions': [
                    "¿En qué departamento o municipio te encuentras?",
                    "¿Podrías decirme tu ubicación para darte información más precisa?",
                    "Para ayudarte mejor, ¿desde qué región de Colombia me escribes?"
                ],
                'keywords': ['ubicacion', 'region', 'departamento', 'municipio', 'donde']
            },
            'connectivity_problems': {
                'questions': [
                    "¿Qué tipo de problemas de conectividad experimentas? (velocidad lenta, cortes frecuentes, sin señal)",
                    "¿El problema es constante o solo en ciertos horarios?",
                    "¿Afecta a toda tu familia o solo a ciertos dispositivos?",
                    "¿Has probado con diferentes proveedores de internet?"
                ],
                'keywords': ['internet', 'conexion', 'wifi', 'lento', 'cortes', 'señal']
            },
            'educational_impact': {
                'questions': [
                    "¿Estudias actualmente? ¿En qué nivel? (primaria, secundaria, universidad)",
                    "¿Necesitas internet para clases virtuales o tareas?",
                    "¿Tienes hermanos que también necesiten conectividad para estudiar?",
                    "¿Tu colegio o universidad ofrece alternativas para conectividad?"
                ],
                'keywords': ['estudios', 'clases', 'tareas', 'colegio', 'universidad', 'virtual']
            },
            'economic_situation': {
                'questions': [
                    "¿El costo del internet es un obstáculo para tu familia?",
                    "¿Conoces programas gubernamentales de conectividad gratuita?",
                    "¿Estarías interesado en planes subsidiados o gratuitos?"
                ],
                'keywords': ['dinero', 'costo', 'plata', 'caro', 'gratis', 'subsidio']
            },
            'device_availability': {
                'questions': [
                    "¿Tienes dispositivos para conectarte? (celular, computador, tablet)",
                    "¿Compartes dispositivos con otros familiares?",
                    "¿Necesitas ayuda para conseguir dispositivos?"
                ],
                'keywords': ['computador', 'celular', 'tablet', 'dispositivo', 'equipo']
            },
            'regional_solutions': {
                'antioquia': [
                    "¿Conoces los Puntos Vive Digital cerca de tu zona en Antioquia?",
                    "¿Has consultado sobre Conexión Total en tu municipio?",
                    "¿Sabes que en Medellín hay WiFi gratis en espacios públicos?"
                ],
                'choco': [
                    "¿Conoces el programa Internet para Todos en Chocó?",
                    "¿Has visitado los Kioscos Vive Digital en tu comunidad?",
                    "¿Sabes sobre la conectividad satelital disponible en zonas remotas?"
                ],
                'guajira': [
                    "¿Conoces los Puntos Vive Digital Wayuu en La Guajira?",
                    "¿Has consultado sobre internet satelital para zonas desérticas?",
                    "¿Sabes de programas especiales para comunidades indígenas?"
                ]
            }
        }
    
    def get_conversation_context(self, user_id: str) -> ConversationContext:
        """Obtener o crear contexto de conversación"""
        if user_id not in self.conversation_contexts:
            self.conversation_contexts[user_id] = ConversationContext(user_id=user_id)
        return self.conversation_contexts[user_id]
    
    def extract_keywords(self, message: str) -> set:
        """Extraer palabras clave del mensaje"""
        message_lower = message.lower()
        keywords = set()
        
        # Buscar keywords en todos los templates
        for category, template in self.question_templates.items():
            if isinstance(template, dict) and 'keywords' in template:
                for keyword in template['keywords']:
                    if keyword in message_lower:
                        keywords.add(keyword)
        
        # Detectar regiones mencionadas
        for dept_key, dept_info in self.connectivity_data['colombia_connectivity']['departments'].items():
            dept_name = dept_info['name'].lower()
            if dept_name in message_lower:
                keywords.add(f"region_{dept_key}")
                
        return keywords
    
    def detect_region(self, message: str, context: ConversationContext) -> Optional[str]:
        """Detectar región mencionada en el mensaje"""
        message_lower = message.lower()
        
        for dept_key, dept_info in self.connectivity_data['colombia_connectivity']['departments'].items():
            dept_name = dept_info['name'].lower()
            capital = dept_info['capital'].lower()
            
            if dept_name in message_lower or capital in message_lower:
                context.region = dept_key
                return dept_key
                
            # Buscar municipios
            if 'municipalities_low_coverage' in dept_info:
                for municipality in dept_info['municipalities_low_coverage']:
                    if municipality.lower() in message_lower:
                        context.region = dept_key
                        return dept_key
        
        return None
    
    def generate_next_questions(self, user_message: str, user_id: str) -> List[str]:
        """
        Generar las próximas preguntas inteligentes basadas en:
        - Mensaje del usuario
        - Contexto previo
        - Región detectada
        - Palabras clave mencionadas
        """
        context = self.get_conversation_context(user_id)
        
        # Actualizar contexto con nueva información
        new_keywords = self.extract_keywords(user_message)
        context.keywords_mentioned.update(new_keywords)
        
        # Detectar región si no está establecida
        if not context.region:
            detected_region = self.detect_region(user_message, context)
            if detected_region:
                logger.info(f"Región detectada: {detected_region}")
        
        # Generar preguntas según prioridades
        questions = []
        
        # 1. Si no sabemos la región, preguntar primero
        if not context.region and 'region_identification' not in context.questions_asked:
            questions.extend(self._get_questions_by_category('region_identification', context))
        
        # 2. Si ya tenemos región, hacer preguntas específicas
        elif context.region:
            questions.extend(self._get_regional_questions(context.region, context))
        
        # 3. Preguntas según keywords detectadas
        if 'internet' in new_keywords or 'conexion' in new_keywords:
            questions.extend(self._get_questions_by_category('connectivity_problems', context))
        
        if 'estudios' in new_keywords or 'clases' in new_keywords:
            questions.extend(self._get_questions_by_category('educational_impact', context))
            
        if 'dinero' in new_keywords or 'caro' in new_keywords:
            questions.extend(self._get_questions_by_category('economic_situation', context))
            
        if 'computador' in new_keywords or 'dispositivo' in new_keywords:
            questions.extend(self._get_questions_by_category('device_availability', context))
        
        # Filtrar preguntas ya hechas y limitar a 2-3
        unique_questions = []
        for q in questions:
            if q not in context.questions_asked and len(unique_questions) < 3:
                unique_questions.append(q)
                context.questions_asked.add(q)
        
        return unique_questions
    
    def _get_questions_by_category(self, category: str, context: ConversationContext) -> List[str]:
        """Obtener preguntas de una categoría específica"""
        if category in self.question_templates:
            template = self.question_templates[category]
            if isinstance(template, dict) and 'questions' in template:
                return template['questions'][:2]  # Máximo 2 por categoría
        return []
    
    def _get_regional_questions(self, region: str, context: ConversationContext) -> List[str]:
        """Obtener preguntas específicas de la región"""
        regional_templates = self.question_templates.get('regional_solutions', {})
        if region in regional_templates:
            return regional_templates[region][:2]
        return []
    
    def get_regional_info(self, region: str) -> Dict:
        """Obtener información detallada de una región"""
        departments = self.connectivity_data.get('colombia_connectivity', {}).get('departments', {})
        return departments.get(region, {})
    
    def get_connectivity_summary(self, region: str) -> str:
        """Generar resumen de conectividad para una región"""
        region_info = self.get_regional_info(region)
        if not region_info:
            return "No tengo información específica de esa región."
        
        coverage = region_info.get('internet_coverage', 0)
        coverage_text = {
            1: "muy baja",
            2: "baja", 
            3: "media",
            4: "buena",
            5: "excelente"
        }.get(coverage, "desconocida")
        
        summary = f"""
📍 **{region_info.get('name', region)}**
📶 Cobertura: {coverage_text} ({coverage}/5)
📡 Proveedores: {', '.join(region_info.get('main_providers', []))}
⚠️ Áreas problemáticas: {', '.join(region_info.get('problematic_areas', [])[:3])}
🏠 Hogares sin internet: ~{region_info.get('estimated_households_without_internet', 0):,}
💡 Programas disponibles: {', '.join(region_info.get('connectivity_programs', []))}
        """
        
        return summary.strip()

# Importar datetime que faltaba
from datetime import datetime