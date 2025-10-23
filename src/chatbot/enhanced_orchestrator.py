"""
Enhanced Chatbot Orchestrator
Integra: Modelos generativos + ML + Case Manager + Preguntas Inteligentes
"""

from src.chatbot.case_manager import (
    CaseManager, UrgencyLevel, ProblemType, AvailableSolution, Case
)
from src.chatbot.chatbot_orchestrator import ChatbotOrchestrator
from src.chatbot.intelligent_questions import IntelligentQuestionGenerator
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class EnhancedChatbotOrchestrator(ChatbotOrchestrator):
    """
    Versión mejorada del ChatbotOrchestrator que incluye:
    - Tus modelos generativos existentes
    - Case Manager para gestión de casos sociales
    - Síntesis inteligente de respuestas
    """
    
    def __init__(self, ml_model=None, vae_encoder=None, vae_decoder=None,
                 vae_scaler=None, vae_features=None, user_id='default'):
        """
        Inicializa con tus modelos existentes + Case Manager + Sistema Inteligente
        """
        # Inicializar clase padre (con tus modelos)
        super().__init__(
            ml_model=ml_model,
            vae_encoder=vae_encoder,
            vae_decoder=vae_decoder,
            vae_scaler=vae_scaler,
            vae_features=vae_features,
            user_id=user_id
        )
        
        # NUEVO: Case Manager para gestión de casos sociales
        self.case_manager = CaseManager()
        
        # NUEVO: Generador de preguntas inteligentes con memoria conversacional
        self.question_generator = IntelligentQuestionGenerator()
        
        logger.info("✅ EnhancedChatbotOrchestrator inicializado con sistema inteligente")
    
    def process_message_with_case_management(self, user_message: str,
                                            conversation_history: List[Dict]) -> Dict:
        """
        Procesa mensaje Y gestiona caso si es necesario
        
        FLUJO:
        1. Análisis con modelos existentes (intent + response)
        2. Análisis de problema social (nuevo)
        3. Si hay urgencia ALTA → crear caso + buscar soluciones
        4. Síntesis de respuesta final
        """
        
        # =============== FASE 1: TUS MODELOS EXISTENTES ===============
        
        logger.info("📨 Procesando mensaje con ambos sistemas...")
        
        # 1.1 Procesar mensaje con la clase padre para obtener respuesta
        result = self.process_message(user_message=user_message, user_data={})
        base_response = result.get('response', 'Lo siento, no pude procesar tu mensaje.')
        intent = result.get('intent', 'general')
        confidence = result.get('confidence', 0.0)
        
        logger.debug(f"✅ Respuesta base generada ({len(base_response)} chars)")
        logger.debug(f"Intent: {intent} (confianza: {confidence})")
        
        # =============== FASE 2: ANÁLISIS DE CASO (NUEVO) ===============
        
        # 2.1 Analizar si hay problema social que abordar
        problem_analysis = self.case_manager.analyze_conversation(
            user_id=self.user_id,
            message=user_message,
            conversation_history=conversation_history
        )
        logger.info(f"📋 Análisis: {problem_analysis.primary_problem.value}")
        logger.info(f"   └─ Urgencia: {problem_analysis.urgency.value}")
        logger.info(f"   └─ Impacto: {problem_analysis.impact_score:.0f}/100")
        
        # =============== FASE 2.5: ANÁLISIS INTELIGENTE DE REGIÓN ===============
        
        # 2.5.1 Detectar si pregunta sobre regiones colombianas sin internet
        regional_context = None
        intelligent_questions = []
        
        if any(keyword in user_message.lower() for keyword in 
               ['region', 'departamento', 'cobertura', 'internet', 'conectividad', 'colombia']):
            logger.info("🌍 Detectada pregunta sobre conectividad regional")

            # Obtener/crear contexto conversacional del generador
            try:
                q_context = self.question_generator.get_conversation_context(self.user_id)

                # Intentar detectar región mencionada en el mensaje
                detected_region = self.question_generator.detect_region(user_message, q_context)

                if detected_region:
                    regional_context = self.question_generator.get_regional_info(detected_region)
                else:
                    regional_context = None

                # Generar preguntas inteligentes basadas en el mensaje y contexto
                intelligent_questions = self.question_generator.generate_next_questions(
                    user_message=user_message,
                    user_id=self.user_id
                )
            except Exception as e:
                logger.warning(f"⚠️ IntelligentQuestionGenerator falló: {e}")
                intelligent_questions = []
                regional_context = None
            
            logger.info(f"✨ Generadas {len(intelligent_questions)} preguntas inteligentes")
            if regional_context:
                logger.info(f"📍 Contexto regional: {regional_context.get('department_name', 'N/A')}")
        
        # =============== FASE 3: GESTIÓN DE CASO (si es necesario) ===============
        
        case_id = None
        solutions_offered = 0
        generated_by = 'generative_model'
        requires_action = False
        action_type = None
        
        # ¿Es un problema de urgencia ALTA o CRÍTICA?
        if problem_analysis.urgency in [UrgencyLevel.HIGH, UrgencyLevel.CRITICAL]:
            logger.warning(f"⚠️ PROBLEMA SOCIAL DETECTADO - Urgencia: {problem_analysis.urgency.value}")
            
            # Crear caso
            case = self.case_manager.create_case(
                self.user_id,
                problem_analysis
            )
            case_id = case.case_id
            logger.info(f"📌 Caso creado: {case_id}")
            
            # Buscar soluciones disponibles
            solutions = self.case_manager.find_matching_solutions(case)
            solutions_offered = len(solutions)
            logger.info(f"✅ {solutions_offered} soluciones encontradas")
            
            if solutions:
                # =============== FASE 4: SÍNTESIS INTELIGENTE ===============
                # Combinar respuesta generativa + oferta de solución + contexto regional
                
                enhanced_response = self._synthesize_response(
                    base_response=base_response,
                    problem=problem_analysis,
                    solutions=solutions,
                    case=case,
                    regional_context=regional_context,
                    intelligent_questions=intelligent_questions
                )
                
                generated_by = 'case_manager'
                requires_action = True
                action_type = 'offer_solution'
                
                return {
                    'response': enhanced_response,
                    'intent': intent,
                    'confidence': confidence,
                    'case_id': case_id,
                    'urgency': problem_analysis.urgency.value,
                    'impact_score': problem_analysis.impact_score,
                    'solutions_offered': solutions_offered,
                    'primary_solution': {
                        'id': solutions[0].solution_id,
                        'type': solutions[0].type.value,
                        'sponsor': solutions[0].sponsor_name,
                        'match_score': solutions[0].match_score,
                        'monthly_value': solutions[0].monthly_value,
                        'duration_months': solutions[0].duration_months
                    } if solutions else None,
                    'requires_action': True,
                    'action_type': action_type,
                    'generated_by': generated_by,
                    'regional_context': regional_context,
                    'intelligent_questions': intelligent_questions,
                    'metadata': {
                        'affected_people': problem_analysis.affected_people,
                        'keywords': problem_analysis.keywords
                    }
                }
        
        # =============== FLUJO NORMAL (sin problema detectado) ===============
        
        # Pero SI hay contexto regional o preguntas inteligentes, enriquecer respuesta
        if regional_context or intelligent_questions:
            enhanced_normal_response = self._enrich_response_with_intelligence(
                base_response=base_response,
                regional_context=regional_context,
                intelligent_questions=intelligent_questions
            )
            
            return {
                'response': enhanced_normal_response,
                'intent': intent,
                'confidence': confidence,
                'case_id': None,
                'requires_action': False,
                'action_type': None,
                'generated_by': 'intelligent_system',
                'regional_context': regional_context,
                'intelligent_questions': intelligent_questions,
                'metadata': {
                    'problem_type': problem_analysis.primary_problem.value,
                    'urgency': problem_analysis.urgency.value
                }
            }
        
        return {
            'response': base_response,
            'intent': intent,
            'confidence': confidence,
            'case_id': None,
            'requires_action': False,
            'action_type': None,
            'generated_by': generated_by,
            'metadata': {
                'problem_type': problem_analysis.primary_problem.value,
                'urgency': problem_analysis.urgency.value
            }
        }
    
    def _synthesize_response(self, base_response: str,
                            problem, solutions: List[AvailableSolution],
                            case: Case, regional_context: Optional[Dict] = None,
                            intelligent_questions: Optional[List[str]] = None) -> str:
        """
        SÍNTESIS INTELIGENTE:
        Combina la respuesta empática del modelo generativo
        CON la oferta de solución específica del Case Manager
        """
        
        best_solution = solutions[0]
        
        # Construir respuesta sintetizada
        solution_type = best_solution.type.value.replace('_', ' ')
        
        # Construir respuesta base con solución
        synthesized = f"""{base_response}

---

**Tengo una solución para ti:**

He encontrado una opción de {solution_type} disponible en tu zona, completamente patrocinada por {best_solution.sponsor_name}.

 **Detalles de la solución:**
 Tipo: {solution_type.title()}
 Duración: {best_solution.duration_months} meses
 Costo para ti: **GRATIS** (100% patrocinado)
 Coincidencia con tu necesidad: {int(best_solution.match_score * 100)}%
 Cupos disponibles: {best_solution.capacity_remaining}"""

        # Agregar contexto regional si está disponible
        if regional_context:
            dept_name = regional_context.get('department_name', 'tu región')
            coverage_level = regional_context.get('coverage_level', 'N/A')
            
            synthesized += f"""

 **Información regional - {dept_name}:**
 Nivel de cobertura actual: {coverage_level}/5
Municipios más afectados: {', '.join(regional_context.get('problematic_areas', [])[:3])}
 Hogares sin conectividad: {regional_context.get('households_without_connectivity', 'N/A'):,}
 Programas activos en la región: {len(regional_context.get('active_programs', []))}"""

        # Agregar preguntas inteligentes
        if intelligent_questions:
            synthesized += f"""

🤔 **Basándome en tu situación, me gustaría saber:**"""
            for i, question in enumerate(intelligent_questions[:3], 1):
                synthesized += f"\n{i}. {question}"

        # Finalizar con call-to-action
        synthesized += f"""

💡 **Mientras tanto, opciones inmediatas:**
📍 Biblioteca local - WiFi gratis de 8am-6pm
🖥️ Centro digital comunitario - Computadores disponibles

¿Te interesa que te ayude a activar esta solución?"""
        
        return synthesized
    
    def _enrich_response_with_intelligence(self, base_response: str, 
                                         regional_context: Optional[Dict] = None,
                                         intelligent_questions: Optional[List[str]] = None) -> str:
        """
        Enriquece respuesta normal con contexto regional e inteligencia conversacional
        """
        enriched_response = base_response
        
        # Agregar contexto regional colombiano
        if regional_context:
            dept_name = regional_context.get('department_name', 'esta región')
            coverage_level = regional_context.get('coverage_level', 0)
            
            # Información específica según nivel de cobertura
            if coverage_level <= 2:
                coverage_desc = "⚠️ **Cobertura BAJA** - Zona prioritaria para intervención"
            elif coverage_level <= 3:
                coverage_desc = "⚡ **Cobertura MEDIA** - En proceso de mejora"
            else:
                coverage_desc = "✅ **Cobertura BUENA** - Servicios disponibles"
            
            enriched_response += f"""

---

🌍 **Información sobre conectividad en {dept_name}:**

{coverage_desc}
📊 Nivel actual: {coverage_level}/5
🏘️ Municipios con mayor necesidad: {', '.join(regional_context.get('problematic_areas', [])[:3])}
🏠 Hogares sin internet: {regional_context.get('households_without_connectivity', 'N/A'):,}
📡 Proveedores activos: {', '.join(regional_context.get('providers', []))}

💡 **Programas gubernamentales disponibles:**"""
            
            for program in regional_context.get('active_programs', [])[:2]:
                enriched_response += f"\n• {program}"
        
        # Agregar preguntas inteligentes para profundizar
        if intelligent_questions:
            enriched_response += f"""

🤔 **Para ayudarte mejor, me gustaría conocer:**"""
            for i, question in enumerate(intelligent_questions[:3], 1):
                enriched_response += f"\n{i}. {question}"
            
            enriched_response += "\n\n💬 Responde cualquiera de estas preguntas para que pueda darte información más específica."
        
        return enriched_response
    
    def activate_case_solution(self, case_id: str,
                              user_data: Dict,
                              solution_index: int = 0) -> Dict:
        """
        Usuario confirma que quiere la solución
        """
        case = self.case_manager.cases.get(case_id)
        if not case:
            return {'success': False, 'error': 'Caso no encontrado'}
        
        if not case.assigned_solutions:
            return {'success': False, 'error': 'No hay soluciones disponibles'}
        
        solution = case.assigned_solutions[solution_index]
        
        # Actualizar perfil con datos verificados
        profile = self.case_manager.user_profiles.get(case.user_id)
        if profile and user_data:
            profile.phone = user_data.get('phone', profile.phone)
            profile.location = user_data.get('location', profile.location)
            profile.consent_given = user_data.get('consent', False)
        
        # Activar solución
        activated = self.case_manager.activate_solution(case, solution)
        
        if activated:
            logger.info(f"✅ Caso {case_id} activado con éxito")
            
            return {
                'success': True,
                'case_id': case_id,
                'solution_type': solution.type.value,
                'sponsor': solution.sponsor_name,
                'monthly_value': solution.monthly_value,
                'duration_months': solution.duration_months,
                'next_step': f'El {solution.sponsor_name} te contactará en máximo 48 horas',
                'social_worker': case.social_worker_assigned,
                'follow_up_dates': [d.isoformat() for d in case.follow_up_schedule],
                'verification_url': solution.verification_url
            }
        
        logger.error(f"❌ Error activando caso {case_id}")
        return {'success': False, 'error': 'No se pudo activar la solución'}
    
    def get_case_status(self, case_id: str) -> Dict:
        """Obtiene el estado de un caso"""
        case = self.case_manager.cases.get(case_id)
        if not case:
            return {'error': 'Caso no encontrado'}
        
        return {
            'case_id': case_id,
            'status': case.status,
            'problem': case.problem_analysis.primary_problem.value,
            'urgency': case.problem_analysis.urgency.value,
            'impact_score': case.problem_analysis.impact_score,
            'affected_people': case.problem_analysis.affected_people,
            'sponsor': case.primary_sponsor,
            'social_worker': case.social_worker_assigned,
            'solutions_count': len(case.assigned_solutions),
            'target_resolution_date': case.target_resolution_date.isoformat(),
            'created_at': case.created_at.isoformat(),
            'follow_up_schedule': [d.isoformat() for d in case.follow_up_schedule]
        }
    
    def get_user_cases(self, user_id: str) -> List[Dict]:
        """Obtiene todos los casos de un usuario"""
        user_cases = [
            case for case in self.case_manager.cases.values()
            if case.user_id == user_id
        ]
        
        return [
            {
                'case_id': case.case_id,
                'status': case.status,
                'problem': case.problem_analysis.primary_problem.value,
                'urgency': case.problem_analysis.urgency.value,
                'created_at': case.created_at.isoformat(),
                'target_resolution_date': case.target_resolution_date.isoformat()
            }
            for case in user_cases
        ]
    
    def generate_impact_report(self, case_id: str) -> Dict:
        """Genera reporte de impacto para sponsors"""
        case = self.case_manager.cases.get(case_id)
        if not case:
            return {'error': 'Caso no encontrado'}
        
        return self.case_manager.generate_impact_report(case)
