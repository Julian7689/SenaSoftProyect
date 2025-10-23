"""
Case Manager Digital - Sistema de Orquestación Inteligente
Coordina: Sponsors, Trabajadores Sociales, Recursos, Usuarios
Integración con modelos existentes de ML/VAE
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import logging
import json

logger = logging.getLogger(__name__)

# ==================== ENUMERACIONES ====================

class UrgencyLevel(Enum):
    """Niveles de urgencia basados en impacto"""
    LOW = "baja"
    MEDIUM = "media"
    HIGH = "alta"
    CRITICAL = "crítica"

class ProblemType(Enum):
    """Categorías de problemas"""
    CONNECTIVITY = "conectividad"
    DEVICE = "dispositivo"
    LITERACY = "alfabetización"
    ECONOMIC = "barrera_economica"
    PSYCHOLOGICAL = "apoyo_emocional"
    HEALTH = "salud"
    FOOD_SECURITY = "seguridad_alimentaria"

class SolutionType(Enum):
    """Tipos de soluciones disponibles"""
    INTERNET_SUBSIDY = "subsidio_internet"
    DEVICE_LOAN = "prestamo_dispositivo"
    TRAINING = "capacitacion"
    REFERRAL = "derivacion"
    DIRECT_BENEFIT = "beneficio_directo"

# ==================== DATA CLASSES ====================

@dataclass
class UserProfile:
    """Perfil completo del usuario"""
    user_id: str
    name: str = "Anónimo"
    phone: str = ""
    location: Dict = field(default_factory=lambda: {"city": "", "neighborhood": ""})
    age: int = 0
    vulnerabilities: List[str] = field(default_factory=list)
    children_count: int = 0
    school_names: List[str] = field(default_factory=list)
    income_level: str = "low"
    active_sponsors: List[str] = field(default_factory=list)
    consent_given: bool = False
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class ProblemAnalysis:
    """Análisis del problema detectado"""
    primary_problem: ProblemType
    secondary_problems: List[ProblemType] = field(default_factory=list)
    urgency: UrgencyLevel = UrgencyLevel.LOW
    impact_score: float = 0.0
    affected_people: int = 1
    keywords: List[str] = field(default_factory=list)
    confidence: float = 0.0
    detected_at: datetime = field(default_factory=datetime.now)

@dataclass
class AvailableSolution:
    """Solución disponible para ofertar"""
    solution_id: str
    type: SolutionType
    sponsor_name: str
    location: Dict = field(default_factory=dict)
    capacity_remaining: int = 0
    monthly_value: float = 0.0
    duration_months: int = 0
    requirements: List[str] = field(default_factory=list)
    match_score: float = 0.0
    verification_url: str = ""

@dataclass
class Case:
    """Un caso es la intervención completa"""
    case_id: str
    user_id: str
    problem_analysis: ProblemAnalysis
    assigned_solutions: List[AvailableSolution] = field(default_factory=list)
    primary_sponsor: Optional[str] = None
    social_worker_assigned: Optional[str] = None
    status: str = "created"  # created, verified, activated, in_progress, resolved
    checkpoints: List[Dict] = field(default_factory=list)
    follow_up_schedule: List[datetime] = field(default_factory=list)
    impact_metrics: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    target_resolution_date: datetime = field(default_factory=lambda: datetime.now() + timedelta(days=7))
    resolved_at: Optional[datetime] = None

# ==================== CASE MANAGER ====================

class CaseManager:
    """
    Gestor central de casos. Coordina:
    - Análisis de problemas
    - Búsqueda de soluciones
    - Activación de sponsors
    - Seguimiento automático
    - Medición de impacto
    """
    
    def __init__(self):
        self.cases: Dict[str, Case] = {}
        self.user_profiles: Dict[str, UserProfile] = {}
        self.sponsors_db = self._load_sponsors()
        self.social_workers = self._load_social_workers()
        self.resources_db = self._load_available_resources()
        logger.info("✓ CaseManager inicializado")
    
    def analyze_conversation(self, user_id: str, message: str,
                            conversation_history: List[Dict]) -> ProblemAnalysis:
        """
        Analiza el mensaje para detectar problemas sociales
        """
        intent = self._detect_intent(message)
        entities = self._extract_entities(message, conversation_history)
        vulnerabilities = self._assess_vulnerabilities(entities, conversation_history)
        
        urgency = self._calculate_urgency(
            intent,
            vulnerabilities,
            entities.get('affected_people', 1)
        )
        
        impact_score = self._calculate_impact_score(
            problem_type=intent,
            affected_people=entities.get('affected_people', 1),
            vulnerabilities=vulnerabilities
        )
        
        analysis = ProblemAnalysis(
            primary_problem=intent,
            secondary_problems=self._detect_secondary_problems(message),
            urgency=urgency,
            impact_score=impact_score,
            affected_people=entities.get('affected_people', 1),
            keywords=entities.get('keywords', []),
            confidence=0.85,
            detected_at=datetime.now()
        )
        
        logger.debug(f"📋 Análisis: {intent.value} - Urgencia: {urgency.value}")
        return analysis
    
    def create_case(self, user_id: str, problem_analysis: ProblemAnalysis) -> Case:
        """Crea un nuevo caso"""
        profile = self._get_or_create_profile(user_id)
        target_date = self._calculate_target_date(problem_analysis.urgency)
        
        case = Case(
            case_id=f"CASE_{user_id}_{int(datetime.now().timestamp())}",
            user_id=user_id,
            problem_analysis=problem_analysis,
            target_resolution_date=target_date
        )
        
        self.cases[case.case_id] = case
        logger.info(f"✓ Caso creado: {case.case_id}")
        return case
    
    def find_matching_solutions(self, case: Case) -> List[AvailableSolution]:
        """Busca soluciones disponibles que coincidan"""
        solutions = []
        
        problem_to_solutions = {
            ProblemType.CONNECTIVITY: [
                SolutionType.INTERNET_SUBSIDY,
                SolutionType.DEVICE_LOAN,
                SolutionType.TRAINING
            ],
            ProblemType.DEVICE: [
                SolutionType.DEVICE_LOAN,
                SolutionType.TRAINING
            ],
            ProblemType.ECONOMIC: [
                SolutionType.DIRECT_BENEFIT,
                SolutionType.INTERNET_SUBSIDY
            ],
            ProblemType.PSYCHOLOGICAL: [
                SolutionType.TRAINING,
                SolutionType.REFERRAL
            ],
        }
        
        solution_types_needed = problem_to_solutions.get(
            case.problem_analysis.primary_problem,
            [SolutionType.REFERRAL]
        )
        
        user_profile = self.user_profiles[case.user_id]
        zone = user_profile.location.get('neighborhood', '')
        
        for sponsor_name, sponsor_data in self.sponsors_db.items():
            if zone and zone not in sponsor_data['coverage_zones']:
                continue
            
            for solution_type in solution_types_needed:
                available = sponsor_data['available_solutions'].get(solution_type.value, [])
                
                for sol in available:
                    if sol['capacity_remaining'] > 0:
                        match_score = self._calculate_match_score(
                            solution=sol,
                            problem=case.problem_analysis,
                            user_profile=user_profile
                        )
                        
                        solution_obj = AvailableSolution(
                            solution_id=sol['id'],
                            type=solution_type,
                            sponsor_name=sponsor_name,
                            location=sol['location'],
                            capacity_remaining=sol['capacity_remaining'],
                            monthly_value=sol['monthly_value'],
                            duration_months=sol['duration_months'],
                            requirements=sol['requirements'],
                            match_score=match_score,
                            verification_url=sol['verification_url']
                        )
                        
                        solutions.append(solution_obj)
        
        solutions.sort(key=lambda x: x.match_score, reverse=True)
        logger.info(f"✓ {len(solutions)} soluciones encontradas para {case.case_id}")
        return solutions
    
    def activate_solution(self, case: Case, solution: AvailableSolution) -> bool:
        """Activa una solución"""
        user_profile = self.user_profiles[case.user_id]
        
        requirements_met = self._verify_requirements(user_profile, solution.requirements)
        if not requirements_met:
            logger.warning(f"⚠ Requisitos no cumplidos para {case.case_id}")
            return False
        
        case.assigned_solutions.append(solution)
        case.primary_sponsor = solution.sponsor_name
        case.status = "activated"
        case.social_worker_assigned = self._assign_social_worker(
            zone=user_profile.location.get('neighborhood', '')
        )
        case.follow_up_schedule = self._create_follow_up_schedule(case)
        
        self._notify_sponsor(case, solution)
        self._notify_social_worker(case)
        
        logger.info(f"✅ Solución activada: {case.case_id}")
        return True
    
    def generate_impact_report(self, case: Case) -> Dict:
        """Genera reporte de impacto"""
        profile = self.user_profiles.get(case.user_id)
        if not profile:
            return {}
        
        return {
            'case_id': case.case_id,
            'beneficiary': {
                'location': profile.location,
                'vulnerability_score': self._calculate_vulnerability_score(profile)
            },
            'problem': {
                'type': case.problem_analysis.primary_problem.value,
                'impact_score': case.problem_analysis.impact_score,
                'affected_people': case.problem_analysis.affected_people
            },
            'solution': {
                'type': case.assigned_solutions[0].type.value if case.assigned_solutions else None,
                'total_investment': sum(
                    s.monthly_value * s.duration_months for s in case.assigned_solutions
                )
            },
            'status': case.status,
            'created_at': case.created_at.isoformat(),
            'metrics': case.impact_metrics
        }
    
    # ==================== MÉTODOS PRIVADOS ====================
    
    def _detect_intent(self, message: str) -> ProblemType:
        """Detecta tipo de problema"""
        msg_lower = message.lower()
        
        if any(word in msg_lower for word in ['internet', 'wifi', 'conectividad', 'conexión', 'señal']):
            return ProblemType.CONNECTIVITY
        elif any(word in msg_lower for word in ['computador', 'tablet', 'dispositivo', 'celular', 'teléfono']):
            return ProblemType.DEVICE
        elif any(word in msg_lower for word in ['plata', 'dinero', 'economía', 'pago', 'no puedo pagar']):
            return ProblemType.ECONOMIC
        elif any(word in msg_lower for word in ['triste', 'solo', 'ayuda', 'depresión', 'ansiedad', 'miedo']):
            return ProblemType.PSYCHOLOGICAL
        elif any(word in msg_lower for word in ['comida', 'hambre', 'alimento']):
            return ProblemType.FOOD_SECURITY
        
        return ProblemType.CONNECTIVITY
    
    def _extract_entities(self, message: str, history: List[Dict]) -> Dict:
        """Extrae entidades"""
        entities = {'keywords': [], 'affected_people': 1}
        
        full_conversation = message + ' ' + ' '.join([m.get('content', '') for m in history])
        
        # Detectar hijos/personas afectadas
        if 'hijo' in full_conversation.lower() or 'hija' in full_conversation.lower():
            if '2' in full_conversation or 'dos' in full_conversation.lower():
                entities['affected_people'] = 2
            else:
                entities['affected_people'] = 1
        
        if 'hijos' in full_conversation.lower() or 'hijas' in full_conversation.lower():
            entities['affected_people'] = 2
        
        entities['has_school_age_children'] = any(
            word in full_conversation.lower()
            for word in ['colegio', 'escuela', 'clases', 'estudiante']
        )
        
        return entities
    
    def _assess_vulnerabilities(self, entities: Dict, history: List[Dict]) -> List[str]:
        """Detecta factores de vulnerabilidad"""
        vulnerabilities = []
        full_conversation = ' '.join([m.get('content', '') for m in history])
        msg_lower = full_conversation.lower()
        
        if any(word in msg_lower for word in ['sola', 'solo', 'mamá', 'papá', 'viuda', 'divorciada']):
            vulnerabilities.append('familia_monoparental')
        
        if entities.get('affected_people', 1) > 1:
            vulnerabilities.append('multiples_dependientes')
        
        if any(word in msg_lower for word in ['no tenemos plata', 'no hay dinero', 'desempleado', 'desempleada']):
            vulnerabilities.append('barrera_economica_severa')
        
        if entities.get('has_school_age_children'):
            vulnerabilities.append('estudiantes_dependientes')
        
        return vulnerabilities
    
    def _calculate_urgency(self, problem_type: ProblemType,
                          vulnerabilities: List[str],
                          affected_people: int) -> UrgencyLevel:
        """Calcula nivel de urgencia"""
        urgency_score = 0
        
        if problem_type in [ProblemType.CONNECTIVITY, ProblemType.DEVICE]:
            urgency_score += 3
        elif problem_type in [ProblemType.ECONOMIC, ProblemType.FOOD_SECURITY]:
            urgency_score += 2
        
        if affected_people > 1:
            urgency_score += 2
        
        if 'barrera_economica_severa' in vulnerabilities:
            urgency_score += 3
        if 'estudiantes_dependientes' in vulnerabilities:
            urgency_score += 2
        if 'familia_monoparental' in vulnerabilities:
            urgency_score += 1
        
        if urgency_score >= 7:
            return UrgencyLevel.CRITICAL
        elif urgency_score >= 5:
            return UrgencyLevel.HIGH
        elif urgency_score >= 3:
            return UrgencyLevel.MEDIUM
        else:
            return UrgencyLevel.LOW
    
    def _calculate_impact_score(self, problem_type: ProblemType,
                               affected_people: int,
                               vulnerabilities: List[str]) -> float:
        """Score 0-100 del impacto social"""
        score = 0.0
        
        problem_weights = {
            ProblemType.CONNECTIVITY: 40,
            ProblemType.DEVICE: 35,
            ProblemType.ECONOMIC: 30,
            ProblemType.PSYCHOLOGICAL: 25,
            ProblemType.FOOD_SECURITY: 40,
        }
        score += problem_weights.get(problem_type, 20)
        score += affected_people * 10
        score += len(vulnerabilities) * 5
        
        return min(score, 100.0)
    
    def _calculate_target_date(self, urgency: UrgencyLevel) -> datetime:
        """Calcula fecha objetivo de resolución"""
        base_date = datetime.now()
        
        if urgency == UrgencyLevel.CRITICAL:
            return base_date + timedelta(days=1)
        elif urgency == UrgencyLevel.HIGH:
            return base_date + timedelta(days=3)
        elif urgency == UrgencyLevel.MEDIUM:
            return base_date + timedelta(days=7)
        else:
            return base_date + timedelta(days=14)
    
    def _calculate_match_score(self, solution: Dict, problem: ProblemAnalysis,
                              user_profile: UserProfile) -> float:
        """Score 0-1 de qué tan bien la solución resuelve el problema"""
        score = 0.5
        
        if 'zone' in solution:
            score += 0.2
        
        if solution['capacity_remaining'] > 0:
            score += 0.1
        
        score += 0.2
        
        return min(score, 1.0)
    
    def _verify_requirements(self, profile: UserProfile, requirements: List[str]) -> bool:
        """Verifica que el usuario cumple requisitos"""
        for req in requirements:
            if req == 'have_phone' and not profile.phone:
                return False
            if req == 'accept_consent' and not profile.consent_given:
                return False
        return True
    
    def _assign_social_worker(self, zone: str) -> Optional[str]:
        """Asigna trabajador social"""
        workers_in_zone = [
            w for w in self.social_workers
            if zone in w['coverage_zones']
        ]
        
        if workers_in_zone:
            return min(workers_in_zone, key=lambda w: len(w['active_cases']))['id']
        
        return None
    
    def _create_follow_up_schedule(self, case: Case) -> List[datetime]:
        """Crea schedule de seguimiento"""
        schedule = []
        base = datetime.now()
        
        schedule.append(base + timedelta(days=2))
        schedule.append(base + timedelta(days=7))
        schedule.append(base + timedelta(days=30))
        schedule.append(base + timedelta(days=90))
        
        return schedule
    
    def _notify_sponsor(self, case: Case, solution: AvailableSolution):
        """Notifica al sponsor"""
        logger.info(f"📬 Notificación a {solution.sponsor_name} - Caso: {case.case_id}")
    
    def _notify_social_worker(self, case: Case):
        """Notifica al trabajador social"""
        if case.social_worker_assigned:
            logger.info(f"📬 Notificación a trabajador social - Caso: {case.case_id}")
    
    def _detect_secondary_problems(self, message: str) -> List[ProblemType]:
        """Detecta problemas secundarios"""
        secondary = []
        msg_lower = message.lower()
        
        if 'dispositivo' in msg_lower:
            secondary.append(ProblemType.DEVICE)
        if any(word in msg_lower for word in ['ayuda', 'clases', 'enseñanza']):
            secondary.append(ProblemType.LITERACY)
        
        return secondary
    
    def _calculate_vulnerability_score(self, profile: UserProfile) -> float:
        """Score de vulnerabilidad general"""
        score = 0.0
        
        if profile.income_level == 'low':
            score += 3
        
        score += len(profile.vulnerabilities)
        
        return min(score, 10.0)
    
    def _get_or_create_profile(self, user_id: str) -> UserProfile:
        """Obtiene o crea perfil del usuario"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserProfile(user_id=user_id)
        return self.user_profiles[user_id]
    
    def _load_sponsors(self) -> Dict:
        """Carga base de datos de sponsors"""
        return {
            'Claro RSE': {
                'coverage_zones': ['Soacha', 'Ciudadela Sucre', 'Sibaté', 'Bogotá'],
                'available_solutions': {
                    'subsidio_internet': [
                        {
                            'id': 'CLARO_INTERNET_001',
                            'capacity_remaining': 50,
                            'monthly_value': 45000,
                            'duration_months': 6,
                            'location': {'city': 'Soacha', 'coverage': 'full_zone'},
                            'requirements': ['phone', 'identity'],
                            'verification_url': 'https://claro.com/verify'
                        }
                    ],
                    'prestamo_dispositivo': []
                }
            },
            'Google.org': {
                'coverage_zones': ['Soacha', 'Bogotá', 'Bosa', 'Kennedy'],
                'available_solutions': {
                    'capacitacion': [
                        {
                            'id': 'GOOGLE_TRAINING_001',
                            'capacity_remaining': 100,
                            'monthly_value': 0,
                            'duration_months': 3,
                            'location': {'type': 'online'},
                            'requirements': ['age_over_13'],
                            'verification_url': 'https://google.org/verify'
                        }
                    ]
                }
            },
            'MinTIC': {
                'coverage_zones': ['Soacha', 'Bogotá', 'Sibaté'],
                'available_solutions': {
                    'prestamo_dispositivo': [
                        {
                            'id': 'MITIC_DEVICE_001',
                            'capacity_remaining': 30,
                            'monthly_value': 0,
                            'duration_months': 12,
                            'location': {'type': 'nationwide'},
                            'requirements': ['proof_of_residence', 'student_id'],
                            'verification_url': 'https://mitic.gov.co/verify'
                        }
                    ]
                }
            }
        }
    
    def _load_social_workers(self) -> List[Dict]:
        """Carga trabajadores sociales"""
        return [
            {
                'id': 'SW_001',
                'name': 'Laura Gómez',
                'phone': '310-1234567',
                'coverage_zones': ['Soacha', 'Ciudadela Sucre'],
                'active_cases': []
            },
            {
                'id': 'SW_002',
                'name': 'Carlos Rojas',
                'phone': '310-2345678',
                'coverage_zones': ['Soacha', 'Sibaté'],
                'active_cases': []
            }
        ]
    
    def _load_available_resources(self) -> Dict:
        """Carga recursos físicos disponibles"""
        return {
            'wifi_points': [
                {
                    'name': 'Biblioteca Sucre',
                    'location': 'Calle 8 #15-32',
                    'hours': '8am-6pm',
                    'distance': '2km'
                }
            ],
            'digital_centers': [
                {
                    'name': 'Punto Vive Digital Soacha',
                    'location': 'Centro administrativo',
                    'computers': 30,
                    'hours': '8am-8pm'
                }
            ]
        }
