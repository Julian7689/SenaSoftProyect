"""
Enhanced Chatbot Orchestrator
Integra: Modelos generativos + ML + Case Manager
"""

from src.chatbot.case_manager import (
    CaseManager, UrgencyLevel, ProblemType, AvailableSolution, Case
)
from src.chatbot.chatbot_orchestrator import ChatbotOrchestrator
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
        Inicializa con tus modelos existentes + Case Manager
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
        
        logger.info("✅ EnhancedChatbotOrchestrator inicializado")
    
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
                # Combinar respuesta generativa + oferta de solución
                
                enhanced_response = self._synthesize_response(
                    base_response=base_response,
                    problem=problem_analysis,
                    solutions=solutions,
                    case=case
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
                    'metadata': {
                        'affected_people': problem_analysis.affected_people,
                        'keywords': problem_analysis.keywords
                    }
                }
        
        # =============== FLUJO NORMAL (sin problema detectado) ===============
        
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
                            case: Case) -> str:
        """
        SÍNTESIS INTELIGENTE:
        Combina la respuesta empática del modelo generativo
        CON la oferta de solución específica del Case Manager
        """
        
        best_solution = solutions[0]
        
        # Construir respuesta sintetizada
        solution_type = best_solution.type.value.replace('_', ' ')
        
        synthesized = f"""{base_response}

---

🎯 **Tengo una solución para ti:**

He encontrado una opción de {solution_type} disponible en tu zona, completamente patrocinada por {best_solution.sponsor_name}.

✨ **Detalles de la solución:**
📌 Tipo: {solution_type.title()}
⏱️ Duración: {best_solution.duration_months} meses
💰 Costo para ti: **GRATIS** (100% patrocinado)
📊 Coincidencia con tu necesidad: {int(best_solution.match_score * 100)}%
📦 Cupos disponibles: {best_solution.capacity_remaining}

¿Te interesa que te ayude a activarlo? Necesitaré algunos datos básicos para verificar tu elegibilidad.

💡 **Mientras tanto, opciones inmediatas:**
📍 Biblioteca local - WiFi gratis de 8am-6pm
🖥️ Centro digital comunitario - Computadores disponibles

¿Quieres continuar con la activación?"""
        
        return synthesized
    
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
