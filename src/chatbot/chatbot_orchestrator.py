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
    """Genera respuestas coherentes y contextualizadas"""
    
    def __init__(self):
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict:
        """Carga plantillas de respuesta"""
        return {
            'saludar': [
                "🤖 ¡Hola! Soy BOTI, tu asistente educativo. Analizo conectividad e indicadores educativos. ¿Cómo puedo ayudarte?",
                "👋 ¡Hola! Me alegra verte. Puedo ayudarte a analizar conectividad, predecir acceso a internet, o sugerir mejoras. ¿Qué necesitas?",
                "🎓 ¡Hola! Soy BOTI. ¿Hay algo sobre educación o conectividad que necesites?"
            ],
            'ayuda_inicio': [
                "Claro, estoy para ayudarte. Cuéntame sobre tu región o el problema que enfrentas.",
                "¡Por supuesto! Soy experto en análisis educativo. ¿Cuál es tu región o cuál es tu preocupación principal?"
            ],
            'necesito_datos': [
                "Para análisis completo, necesitaré 14 indicadores: población, porcentaje rural, estrato, tasa de pobreza, instituciones, computadores/estudiante, salones/institución, docentes/institución, cobertura eléctrica, 4G, dispositivos/hogar, tasa de aprobación, deserción y puntaje en pruebas.",
                "Para hacer un diagnóstico preciso, necesito estos datos: población total, % rural, estrato promedio, tasa de pobreza, número de instituciones educativas, equipamiento tecnológico, y métricas de desempeño."
            ],
            'prediccion_exito': [
                "✅ ¡Excelentes noticias! Tu región parece tener buena infraestructura de conectividad. Sin embargo, siempre hay espacio para mejorar. ¿Quieres ver sugerencias?",
                "🎉 ¡Muy bien! Tu análisis indica acceso a internet con buena cobertura. ¿Te gustaría explorar cómo mejorar aún más?"
            ],
            'prediccion_alerta': [
                "⚠️ Mi análisis muestra que tu región enfrenta desafíos de conectividad. Es importante actuar. ¿Quieres que sugiera mejoras específicas?",
                "🔴 He detectado que hay oportunidades de mejora en conectividad. Te recomiendo enfocarse en infraestructura. ¿Ves las propuestas abajo?"
            ],
            'despedida': [
                "👋 ¡Hasta luego! Si necesitas más análisis, no dudes en volver. ¡Estoy aquí para ayudarte!",
                "🚀 ¡Adiós! Espero haber sido útil. ¡Cualquier cosa, me encuentras aquí!"
            ]
        }
    
    def generate(
        self,
        intent: str,
        entities: Dict,
        prediction_result: Optional[Dict] = None,
        user_region: Optional[str] = None
    ) -> str:
        """Genera respuesta contextualizada"""
        
        if intent == 'saludar':
            return np.random.choice(self.templates['saludar'])
        
        elif intent == 'despedida':
            return np.random.choice(self.templates['despedida'])
        
        elif intent == 'ayuda':
            if entities['region']:
                return f"Entiendo que buscas ayuda en {entities['region']}. " \
                       f"Para hacerte un análisis completo, necesito información específica. " \
                       f"¿Puedes compartir datos sobre tu región?"
            else:
                response = np.random.choice(self.templates['ayuda_inicio'])
                return response
        
        elif intent == 'conectividad':
            if entities['region']:
                return f"Veo que te interesa conectividad en {entities['region']}. " \
                       f"Este es un factor crucial para la educación. " \
                       f"¿Cuál es la situación específica que enfrentas?"
            else:
                return "Veo que te interesa el tema de conectividad. " \
                       "Es un factor crucial para educación. " \
                       "¿Cuál es tu región o situación específica?"
        
        elif intent == 'prediccion':
            if prediction_result and prediction_result.get('executed'):
                return self._generate_prediction_response(prediction_result)
            else:
                if entities['region']:
                    return f"Para hacer una predicción en {entities['region']}, necesito 14 indicadores específicos. " \
                           f"¿Los tienes disponibles?"
                else:
                    return "Para hacer una predicción, necesito datos específicos de tu región. " \
                           "¿Los tienes disponibles?"
        
        elif intent == 'mejora':
            if prediction_result and prediction_result.get('improvements'):
                return "Perfecto! He generado propuestas de mejora basadas en tu situación. " \
                       "Ver detalles abajo. 👇"
            else:
                return "Para sugerir mejoras, primero necesito analizar tu situación. " \
                       "¿Compartimos datos?"
        
        elif intent == 'reporte':
            return "Claro! Puedo generar reportes con análisis y gráficas. " \
                   "Primero, necesito datos sobre tu región."
        
        elif intent == 'educacion':
            if entities['region']:
                return f"Excelente, vamos a hablar sobre educación en {entities['region']}. " \
                       f"¿Cuál es tu interés específico: acceso, calidad, cobertura o conectividad?"
            else:
                return "Hablemos de educación. ¿Cuál es tu interés específico: acceso, calidad, cobertura o conectividad?"
        
        else:
            region_text = f" en {entities['region']}" if entities['region'] else ""
            return f"Interesante punto sobre {intent}{region_text}. " \
                   f"Cuéntame más para poder ayudarte mejor. Estoy aquí para analizar la situación educativa. 🎓"
    
    def _generate_prediction_response(self, prediction_result: Dict) -> str:
        """Genera respuesta específica para predicción"""
        prediction = prediction_result['prediction']
        prob = prediction_result['probability']
        interpretation = prediction_result['interpretation']
        
        if prediction == 1:
            template = np.random.choice(self.templates['prediccion_exito'])
        else:
            template = np.random.choice(self.templates['prediccion_alerta'])
        
        return f"{template}\n\n📊 Análisis: {interpretation}"


class ChatbotOrchestrator:
    """
    Orquesta todo el flujo conversacional
    Integra: NLP + Modelos ML + Generador de respuestas
    """
    
    def __init__(self, ml_model=None, vae_encoder=None, vae_decoder=None, vae_scaler=None, vae_features=None):
        """
        ml_model: Modelo predictivo (MLP)
        vae_encoder: Encoder del VAE
        vae_decoder: Decoder del VAE
        vae_scaler: Normalizador de datos
        vae_features: Lista de features en orden correcto
        """
        self.ml_model = ml_model
        self.vae_encoder = vae_encoder
        self.vae_decoder = vae_decoder
        self.vae_scaler = vae_scaler
        self.vae_features = vae_features or []
        
        # Componentes NLP
        self.intent_detector = IntentDetector()
        self.entity_extractor = EntityExtractor()
        self.response_generator = ResponseGenerator()
        
        # Contexto del usuario
        self.user_context = {
            'region': None,
            'data': None,
            'last_prediction': None,
            'conversation_history': []
        }
        
        logger.info("✓ ChatbotOrchestrator inicializado")
    
    def process_message(self, user_message: str, user_data: Optional[Dict] = None) -> Dict:
        """
        Procesa mensaje completo del usuario
        
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
        
        # 3. ACTUALIZAR CONTEXTO
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
        
        # 5. GENERAR RESPUESTA
        response_text = self.response_generator.generate(
            intent,
            entities,
            prediction_result,
            self.user_context['region']
        )
        
        # 6. REGISTRAR EN HISTORIAL
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
            return f"✅ CON acceso a internet (confianza: {proba[1]*100:.1f}%)"
        else:
            return f"🔴 SIN acceso a internet (riesgo: {proba[0]*100:.1f}%)"
    
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
