"""

Flujo:
1. Usuario escribe mensaje
2. NLP detecta intención + extrae entidades
3. Ejecuta modelos necesarios (MLP, VAE)
4. Genera respuesta coherente
5. Retorna respuesta contextualizada
"""

import json
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import numpy as np
from abc import ABC, abstractmethod

# Importar ConversationMemory
from .conversation_memory import ConversationMemory

logger = logging.getLogger(__name__)


class IntentDetector:

    
    def __init__(self):
        self.intents = {
            'saludar': {
                'keywords': ['hola', 'hi', 'buenos días', 'buenas noches', 'hola bot', 'hey'],
                'patterns': [r'hola', r'buenos', r'hey\b', r'hi\b']
            },
            'despedida': {
                'keywords': ['adiós', 'chao', 'bye', 'hasta luego', 'nos vemos', 'adios'],
                'patterns': [r'adiós|adios', r'chao', r'bye', r'hasta']
            },
            'ayuda': {
                'keywords': ['ayuda', 'help', 'necesito', 'me ayudas', 'puedes', 'podrias', 'emergencia'],
                'patterns': [r'ayuda', r'necesito', r'me ayuda', r'emergencia']
            },
            'prediccion': {
                'keywords': ['predecir', 'prediction', 'analiza', 'revisa', 'evalúa', 'diagnóstico'],
                'patterns': [r'predecir|predicci[óo]n', r'analiza', r'diagnóstico']
            },
            'conectividad': {
                'keywords': ['internet', 'conectividad', 'wifi', '4g', 'online', 'red', 'conexión'],
                'patterns': [r'internet', r'conectividad|conexi[óo]n', r'4g', r'wifi']
            },
            'educacion': {
                'keywords': ['escuela', 'colegio', 'educación', 'estudiantes', 'docentes', 'formación'],
                'patterns': [r'escuela|colegio', r'educaci[óo]n', r'estudiante', r'docente']
            },
            'mejora': {
                'keywords': ['mejorar', 'propuesta', 'sugerencia', 'recomendación', 'cambios', 'estrategia'],
                'patterns': [r'mejorar|mejora', r'propuesta|sugerencia', r'recomendaci[óo]n', r'estrategia']
            },
            'reporte': {
                'keywords': ['reporte', 'gráfica', 'estadística', 'datos', 'informe', 'resumen'],
                'patterns': [r'reporte|informe', r'gr[áa]fica', r'estad[ií]stica', r'datos']
            },
            'region': {
                'keywords': ['región', 'región', 'departamento', 'zona', 'área', 'municipio'],
                'patterns': [r'regi[óo]n', r'departamento', r'zona', r'municipio']
            }
        }
    
    def detect(self, user_message: str) -> Tuple[str, float]:
        """
        Detecta intención del mensaje
        Retorna: (intención, confianza 0-1)
        """
        user_message_lower = user_message.lower().strip()
        scores = {}
        
        for intent_name, intent_data in self.intents.items():
            score = 0
            
            # Búsqueda por keywords
            for keyword in intent_data['keywords']:
                if keyword in user_message_lower:
                    score += 2
            
            # Búsqueda por patterns
            for pattern in intent_data['patterns']:
                if re.search(pattern, user_message_lower):
                    score += 3
            
            scores[intent_name] = score
        
        if not scores or all(v == 0 for v in scores.values()):
            return 'general', 0.3
        
        max_intent = max(scores, key=scores.get)
        max_score = scores[max_intent]
        
        # Calcular confianza
        total_score = sum(scores.values())
        confidence = max_score / total_score if total_score > 0 else 0.3
        
        return max_intent, min(confidence, 1.0)


class EntityExtractor:
    """Extrae entidades del mensaje del usuario"""
    
    def __init__(self):
        self.regiones = [
            'bogotá', 'antioquia', 'magdalena', 'atlántico', 'córdoba',
            'cundinamarca', 'tolima', 'cauca', 'nariño', 'huila', 'meta',
            'bolivar', 'sucre', 'norte de santander', 'santander', 'arauca'
        ]
    
    def extract(self, user_message: str) -> Dict:
        """
        Extrae entidades del mensaje
        Retorna: dict con región, números, palabras clave
        """
        message_lower = user_message.lower()
        
        return {
            'region': self._extract_region(message_lower),
            'numbers': self._extract_numbers(user_message),
            'keywords': self._extract_keywords(message_lower),
            'has_data_request': self._has_data_request(message_lower)
        }
    
    def _extract_region(self, message_lower: str) -> Optional[str]:
        """Extrae nombre de región si existe"""
        for region in self.regiones:
            if region in message_lower:
                return region.title()
        return None
    
    def _extract_numbers(self, message: str) -> List[float]:
        """Extrae números mencionados"""
        numbers = re.findall(r'\d+\.?\d*', message)
        return [float(n) for n in numbers]
    
    def _extract_keywords(self, message_lower: str) -> List[str]:
        """Extrae palabras clave importantes"""
        important_words = [
            'internet', 'conectividad', 'escuela', 'estudiante',
            'rural', 'urbano', 'docente', 'educación', '4g', 'wifi',
            'infraestructura', 'recursos', 'apoyo', 'problemas'
        ]
        found = [w for w in important_words if w in message_lower]
        return list(set(found))  # Eliminar duplicados
    
    def _has_data_request(self, message_lower: str) -> bool:
        """Detecta si el usuario ofrece o pide datos"""
        data_keywords = ['datos', 'información', 'valores', 'números', 'cifras', 'estadísticas']
        return any(keyword in message_lower for keyword in data_keywords)


class ResponseGenerator:
    """Genera respuestas coherentes y contextualizadas AVANZADAS con memoria de conversación"""
    
    def __init__(self):
        """Inicializa con plantillas específicas por intención"""
        self.conversation_memory: Optional[ConversationMemory] = None
        self.response_templates = self._load_response_templates()
        logger.info("ResponseGenerator AVANZADO inicializado")
    
    def set_conversation_memory(self, memory: ConversationMemory):
        """Asigna memoria de conversación para acceso al contexto"""
        self.conversation_memory = memory
    
    def _load_response_templates(self) -> Dict:
        """Carga plantillas de respuesta muy específicas y naturales"""
        return {
            'initial_greeting': [
                "Hola! Soy BOTI, tu asistente especializado. Puedo analizar conectividad, educación e indicadores de tu región. ¿Cuál es tu región?",
                "¡Bienvenido! Soy BOTI. Puedo ayudarte a analizar la situación educativa y de conectividad en tu zona. ¿De dónde eres?",
                "Hola! Estoy aquí para ayudarte. Cuéntame de qué región eres y qué necesitas analizar.",
            ],
            'confirm_region': [
                "Perfecto, recordaré que eres de {region}.",
                "Listo, trabajaremos con datos de {region}.",
                "Anotado: {region}. Vamos adelante.",
            ],
            'connectivity_help': [
                "Entiendo, necesitas ayuda con conectividad en {region}. ¿Cuál es la situación actual? ¿Tienes acceso a internet o es limitado?",
                "La conectividad es crucial para educación. En {region}, ¿cuáles son los principales problemas que observas?",
                "Perfecto. Vamos a analizar la conectividad en {region}. Cuéntame más sobre la cobertura actual.",
            ],
            'education_help': [
                "Excelente. En {region}, ¿qué aspecto educativo te preocupa más: acceso, calidad, infraestructura escolar?",
                "Enfoquémonos en educación en {region}. ¿Cuáles son los principales desafíos que observas?",
                "Claro. La educación es fundamental. En {region}, ¿qué necesitas mejorar?",
            ],
            'improvement_proposal': [
                "Para proponer mejoras en {region}, necesito entender mejor la situación. ¿Cuáles son los indicadores principales (población, cobertura 4G, cantidad de instituciones)?",
                "Vamos a generar mejoras para {region}. Comparte los datos clave de tu región.",
                "Perfecto. Para {region} puedo sugerir mejoras. ¿Tienes datos sobre población, cobertura de internet, instituciones educativas?",
            ],
            'data_needed': [
                "Para hacer un análisis completo de {region}, necesito 14 indicadores: población, % rural, estrato, pobreza, instituciones educativas, computadores/estudiante, salones/institución, docentes/institución, cobertura eléctrica, cobertura 4G, dispositivos/hogar, tasa aprobación, deserción, puntaje pruebas. ¿Los tienes?",
                "Para {region}, necesito datos sobre: población, cobertura 4G, instituciones educativas, acceso a dispositivos, tasas de aprobación. ¿Puedes compartirlos?",
            ],
            'analysis_ready': [
                "Perfecto. Con la información de {region}, puedo hacer un análisis detallado. Dime qué necesitas: ¿una predicción de acceso a internet, mejoras recomendadas, o un reporte completo?",
                "Listo para analizar {region}. ¿Quieres que prediga acceso a internet, genere propuestas de mejora, o haga un reporte?",
            ],
            'problem_identified': [
                "Veo que en {region} el problema principal es {problem}. Vamos a enfocarnos en eso.",
                "Entiendo. El desafío en {region} es {problem}. Trabajemos en soluciones.",
            ],
            'continuation': [
                "Retomando: en {region} tu problema es {problem}. ¿Quieres que continúe analizando?",
                "Recuerda que en {region} mencionaste {problem}. ¿Qué más necesitas?",
            ],
            'multiple_topics': [
                "Veo que te interesa tanto conectividad como educación en {region}. Son temas relacionados. ¿Cuál es tu prioridad?",
                "Interesante: conectividad Y educación en {region}. Ambas cosas están ligadas. ¿Comenzamos por la conectividad?",
            ],
            'clarification': [
                "Para {region}, necesito clarificar: ¿tu principal preocupación es {topic}? Así puedo ser más específico.",
                "¿Puedes confirmar? En {region}, ¿tu necesidad es realmente {topic}? Quiero ayudarte bien.",
            ],
            'closing': [
                "¿Hay algo más que analizar de {region}?",
                "¿Necesitas algo más para {region}?",
                "Listo con {region}. ¿Hay otro tema?",
            ]
        }
    
    def generate(
        self,
        intent: str,
        entities: Dict,
        memory: Optional[ConversationMemory] = None,
        prediction_result: Optional[Dict] = None,
        user_region: Optional[str] = None
    ) -> Tuple[str, bool, Optional[str]]:
        """
        Genera respuesta inteligente basada en contexto
        
        Retorna:
        - response: Texto de respuesta
        - is_question: Si es una pregunta del bot
        - question_topic: Sobre qué pregunta (si aplica)
        """
        
        if memory:
            self.conversation_memory = memory
        
        # Obtener contexto
        region = entities.get('region') or user_region
        keywords = set(entities.get('keywords', []))
        
        context = self.conversation_memory.get_context_summary() if self.conversation_memory else {}
        
        # Respuestas basadas en intención Y contexto
        
        if intent == 'saludar':
            response = self._generate_greeting_response(region, context)
            return response, False, None
        
        elif intent == 'despedida':
            return "¡Hasta luego! Si necesitas más ayuda, vuelve pronto.", False, None
        
        elif intent == 'ayuda':
            response, is_q, topic = self._generate_help_response(region, keywords, context)
            return response, is_q, topic
        
        elif intent == 'conectividad':
            response, is_q, topic = self._generate_connectivity_response(region, keywords, context)
            return response, is_q, topic
        
        elif intent == 'educacion':
            response, is_q, topic = self._generate_education_response(region, keywords, context)
            return response, is_q, topic
        
        elif intent == 'mejora':
            response, is_q, topic = self._generate_improvement_response(region, keywords, context)
            return response, is_q, topic
        
        elif intent == 'prediccion':
            response = self._generate_prediction_response(region, prediction_result, context)
            return response, False, None
        
        elif intent == 'reporte':
            response, is_q, topic = self._generate_report_response(region, context)
            return response, is_q, topic
        
        else:
            # Respuesta general contextualizada
            if region:
                response = f"Interesante. En {region}, veo que te interesa {intent}. Cuéntame más para ayudarte mejor."
            else:
                response = f"Entiendo tu interés en {intent}. ¿De qué región eres para darte información más útil?"
            return response, False, None
    
    def _generate_greeting_response(self, region: str, context: Dict) -> str:
        """Respuesta al saludo"""
        if context.get('message_count', 0) == 1:
            # Primer mensaje
            if region:
                return f"Hola desde {region}! Perfecto. Soy BOTI, tu asistente. Ahora, ¿en qué te ayudo? ¿Conectividad, educación, o análisis general?"
            else:
                return "Hola! Soy BOTI. Cuéntame de qué región eres y qué necesitas analizar."
        else:
            # Saludo recurrente
            return "¡Qué tal de nuevo! ¿Hay algo más en lo que pueda ayudarte?"
    
    def _generate_help_response(self, region: str, keywords: set, context: Dict) -> Tuple[str, bool, Optional[str]]:
        """Respuesta a solicitud de ayuda"""
        
        # Si tiene palabras clave claras
        if 'conectividad' in keywords or 'internet' in keywords:
            if region:
                return f"Claro. Necesitas ayuda con conectividad en {region}. ¿Cuál es tu situación actual?", True, 'connectivity_situation'
            else:
                return "Entiendo que necesitas ayuda con conectividad. ¿De qué región eres?", True, 'region'
        
        elif 'educacion' in keywords or 'escuela' in keywords or 'colegio' in keywords:
            if region:
                return f"Perfecto. Vamos a hablar de educación en {region}. ¿Cuál es el desafío principal?", True, 'education_problem'
            else:
                return "De acuerdo, educación es importante. ¿De qué región eres?", True, 'region'
        
        else:
            # Sin palabras clave claras
            if region:
                return f"Claro, estoy aquí para ayudarte en {region}. ¿Es sobre conectividad, educación, o indicadores generales?", True, 'main_topic'
            else:
                return "Claro. Cuéntame: ¿de qué región eres y qué necesitas?", True, 'region'
    
    def _generate_connectivity_response(self, region: str, keywords: set, context: Dict) -> Tuple[str, bool, Optional[str]]:
        """Respuesta sobre conectividad"""
        
        if not region and not context.get('confirmed_region'):
            return "La conectividad es crucial. ¿De qué región eres?", True, 'region'
        
        confirmed_region = region or context.get('confirmed_region')
        
        if 'mejorar' in keywords or 'problema' in keywords:
            return f"Entiendo que necesitas mejorar conectividad en {confirmed_region}. ¿Cuál es tu acceso actual a internet?", True, 'current_connectivity'
        else:
            return f"Vemos que conectividad es importante en {confirmed_region}. ¿Tienes buena cobertura o hay limitaciones?", True, 'connectivity_status'
    
    def _generate_education_response(self, region: str, keywords: set, context: Dict) -> Tuple[str, bool, Optional[str]]:
        """Respuesta sobre educación"""
        
        confirmed_region = region or context.get('confirmed_region')
        
        if not confirmed_region:
            return "La educación es fundamental. ¿De qué región eres?", True, 'region'
        
        return f"Enfocándonos en educación en {confirmed_region}: ¿qué aspecto te preocupa más? (acceso, calidad, infraestructura)", True, 'education_aspect'
    
    def _generate_improvement_response(self, region: str, keywords: set, context: Dict) -> Tuple[str, bool, Optional[str]]:
        """Respuesta sobre mejoras"""
        
        confirmed_region = region or context.get('confirmed_region')
        
        if not confirmed_region:
            return "Para proponer mejoras, primero necesito saber tu región.", True, 'region'
        
        if context.get('primary_problem'):
            return f"Perfecto. Para mejorar {context['primary_problem']} en {confirmed_region}, necesito datos sobre tu región. ¿Tienes información sobre población, cobertura 4G, instituciones?", True, 'data'
        else:
            return f"Para generar mejoras en {confirmed_region}, ¿cuál es tu principal desafío: conectividad o educación?", True, 'main_problem'
    
    def _generate_prediction_response(self, region: str, prediction_result: Dict, context: Dict) -> str:
        """Respuesta para predicción"""
        
        confirmed_region = region or context.get('confirmed_region') or 'tu región'
        
        if not prediction_result or not prediction_result.get('executed'):
            return f"Para hacer una predicción en {confirmed_region}, necesito 14 indicadores específicos. ¿Los tienes?"
        
        pred = prediction_result.get('prediction', 0)
        prob = prediction_result.get('probability', 0)
        
        if pred == 1:
            return f"✅ ANÁLISIS: {confirmed_region} TIENE ACCESO A INTERNET (confianza: {prob*100:.0f}%). Ahora, ¿cómo podemos mejorar aún más?"
        else:
            return f"⚠️ ANÁLISIS: {confirmed_region} ENFRENTA DESAFÍOS DE ACCESO (confianza: {prob*100:.0f}%). Necesitamos mejorar infraestructura. ¿Quieres propuestas?"
    
    def _generate_report_response(self, region: str, context: Dict) -> Tuple[str, bool, Optional[str]]:
        """Respuesta para reporte"""
        
        confirmed_region = region or context.get('confirmed_region')
        
        if not confirmed_region:
            return "Para generar un reporte, ¿de qué región?", True, 'region'
        
        return f"Puedo generar un reporte detallado de {confirmed_region}. ¿Qué indicadores te interesan incluir?", True, 'report_indicators'


class ChatbotOrchestrator:
    """
    Orquesta todo el flujo conversacional
    Integra: NLP + Modelos ML + Generador de respuestas + ConversationMemory
    """
    
    def __init__(self, ml_model=None, vae_encoder=None, vae_decoder=None, vae_scaler=None, vae_features=None, user_id: str = "default"):
        """
        ml_model: Modelo predictivo (MLP)
        vae_encoder: Encoder del VAE
        vae_decoder: Decoder del VAE
        vae_scaler: Normalizador de datos
        vae_features: Lista de features en orden correcto
        user_id: ID único del usuario para conversación
        """
        self.ml_model = ml_model
        self.vae_encoder = vae_encoder
        self.vae_decoder = vae_decoder
        self.vae_scaler = vae_scaler
        self.vae_features = vae_features or []
        self.user_id = user_id
        
        # Componentes NLP
        self.intent_detector = IntentDetector()
        self.entity_extractor = EntityExtractor()
        self.response_generator = ResponseGenerator()
        
        # NUEVO: Memoria de conversación
        self.conversation_memory = ConversationMemory(user_id)
        self.response_generator.set_conversation_memory(self.conversation_memory)
        
        # Contexto del usuario (LEGACY - mantener para compatibilidad)
        self.user_context = {
            'region': None,
            'data': None,
            'last_prediction': None,
            'conversation_history': []
        }
        
        logger.info("✓ ChatbotOrchestrator inicializado")
    
    def process_message(self, user_message: str, user_data: Optional[Dict] = None) -> Dict:
        """
        Procesa mensaje completo del usuario CON MEMORIA DE CONTEXTO
        
        Args:
            user_message: Texto del usuario
            user_data: Dict opcional con características (14 features)
        
        Returns:
            Dict con respuesta, intención, metadata, etc.
        """
        
        # 1. DETECTAR INTENCIÓN
        intent, intent_confidence = self.intent_detector.detect(user_message)
        logger.info(f"Intención detectada: {intent} ({intent_confidence:.2%})")
        
        # 2. EXTRAER ENTIDADES
        entities = self.entity_extractor.extract(user_message)
        logger.info(f"Entidades extraídas: {entities}")
        
        # 3. ACTUALIZAR CONTEXTO LEGACY
        if entities['region']:
            self.user_context['region'] = entities['region']
        
        # 4. EJECUTAR MODELOS SI ES NECESARIO
        prediction_result = {}
        improvements_result = {}
        
        if user_data:
            if intent in ['prediccion', 'mejora', 'ayuda']:
                prediction_result = self._run_prediction(user_data)
                
                if intent == 'mejora' and prediction_result.get('executed'):
                    improvements_result = self._generate_improvements(user_data)
        
        # 5. GENERAR RESPUESTA CON MEMORIA CONVERSACIONAL
        response_tuple = self.response_generator.generate(
            intent,
            entities,
            self.conversation_memory,  # Pasar memoria
            prediction_result,
            self.user_context['region']
        )
        
        # Desempacar respuesta
        if isinstance(response_tuple, tuple):
            response_text, is_question, question_topic = response_tuple
        else:
            response_text = response_tuple
            is_question = False
            question_topic = None
        
        # 6. REGISTRAR EN MEMORIA CON CONTEXTO
        self.conversation_memory.add_message(
            user_message=user_message,
            intent=intent,
            confidence=intent_confidence,
            entities=entities,
            bot_response=response_text,
            is_question=is_question,
            question_topic=question_topic
        )
        
        # 7. REGISTRAR EN HISTORIAL LEGACY
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'user_message': user_message,
            'intent': intent,
            'intent_confidence': intent_confidence,
            'entities': entities,
            'bot_response': response_text,
            'prediction': prediction_result,
            'improvements': improvements_result
        }
        self.user_context['conversation_history'].append(log_entry)
        
        # 7. RETORNAR RESPUESTA COMPLETA
        return {
            'success': True,
            'response': response_text,
            'intent': intent,
            'intent_confidence': intent_confidence,
            'entities': entities,
            'prediction': prediction_result,
            'improvements': improvements_result,
            'region': self.user_context['region'],
            'timestamp': datetime.now().isoformat()
        }
    
    def _run_prediction(self, user_data: Dict) -> Dict:
        """Ejecuta predicción con MLP si es posible"""
        
        if self.ml_model is None:
            return {'executed': False, 'reason': 'modelo_no_disponible'}
        
        try:
            # Verificar que tenemos todos los features
            required_features = [
                'poblacion_total', 'porcentaje_rural', 'estrato_promedio',
                'tasa_pobreza', 'num_instituciones', 'computadores_por_estudiante',
                'salones_por_institucion', 'docentes_por_institucion',
                'cobertura_electrica', 'cobertura_4g',
                'dispositivos_promedio_hogar', 'tasa_aprobacion',
                'tasa_desercion', 'puntaje_pruebas'
            ]
            
            missing = [f for f in required_features if f not in user_data]
            if missing:
                return {
                    'executed': False,
                    'reason': 'datos_incompletos',
                    'missing_features': missing
                }
            
            # Preparar datos
            X = np.array([user_data[f] for f in required_features]).reshape(1, -1)
            
            # Predicción
            prediction = self.ml_model.predict(X)[0]
            prediction_proba = self.ml_model.predict_proba(X)[0]
            
            # Guardar en contexto
            self.user_context['last_prediction'] = {
                'prediction': int(prediction),
                'probability': float(prediction_proba[1])
            }
            self.user_context['data'] = user_data
            
            return {
                'executed': True,
                'prediction': int(prediction),
                'probability_no_access': float(prediction_proba[0]),
                'probability_with_access': float(prediction_proba[1]),
                'interpretation': self._interpret_prediction(prediction, prediction_proba)
            }
        
        except Exception as e:
            logger.error(f"Error en predicción: {str(e)}")
            return {'executed': False, 'error': str(e)}
    
    def _interpret_prediction(self, prediction: int, proba: np.ndarray) -> str:
        """Interpreta predicción en texto"""
        if prediction == 1:
            return f" CON acceso a internet (confianza: {proba[1]*100:.1f}%)"
        else:
            return f" SIN acceso a internet (riesgo: {proba[0]*100:.1f}%)"
    
    def _generate_improvements(self, user_data: Dict) -> Dict:
        """Genera mejoras con VAE si es posible"""
        
        if self.vae_decoder is None or not self.vae_features:
            return {'executed': False, 'reason': 'modelo_vae_no_disponible'}
        
        try:
            required_features = self.vae_features
            
            missing = [f for f in required_features if f not in user_data]
            if missing:
                return {'executed': False, 'reason': 'datos_incompletos'}
            
            # Preparar datos
            X = np.array([user_data[f] for f in required_features]).reshape(1, -1)
            X_scaled = self.vae_scaler.transform(X)
            
            # Generar mejoras
            improvements = []
            for idx, strength in enumerate([0.3, 0.5, 0.7]):
                try:
                    perturbed_z = np.random.normal(0, strength, (1, 8))
                    improved_scaled = self.vae_decoder.predict(perturbed_z, verbose=0)
                    improved_data = self.vae_scaler.inverse_transform(improved_scaled)
                    
                    improvements.append({
                        'proposal_id': idx + 1,
                        'strength': float(strength * 100),
                        'features': {
                            required_features[i]: float(improved_data[0][i])
                            for i in range(len(required_features))
                        }
                    })
                except Exception as e:
                    logger.warning(f"Error en propuesta {idx+1}: {str(e)}")
                    continue
            
            return {
                'executed': True,
                'n_proposals': len(improvements),
                'proposals': improvements
            }
        
        except Exception as e:
            logger.error(f"Error generando mejoras: {str(e)}")
            return {'executed': False, 'error': str(e)}
    
    def get_conversation_history(self) -> List[Dict]:
        """Retorna historial de conversación"""
        return self.user_context['conversation_history']
    
    def reset_context(self):
        """Reinicia contexto del usuario"""
        self.user_context = {
            'region': None,
            'data': None,
            'last_prediction': None,
            'conversation_history': []
        }
        logger.info("Contexto del usuario reiniciado")
    
    def export_conversation(self) -> Dict:
        """Exporta conversación para análisis"""
        return {
            'user_region': self.user_context['region'],
            'last_prediction': self.user_context['last_prediction'],
            'conversation_count': len(self.user_context['conversation_history']),
            'history': self.user_context['conversation_history'],
            'exported_at': datetime.now().isoformat()
        }
