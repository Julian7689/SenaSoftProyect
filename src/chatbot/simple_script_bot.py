"""
SimpleScriptBot: implementación mínima que sigue un guion predefinido.
Flujo deseado por el usuario:
 - Usuario: "hola"  -> Bot saluda y pregunta región y problema
 - Usuario: indica región y problema -> Bot devuelve una solución simple

El módulo mantiene estado en memoria por `user_email::conv_id`.
Esta clase está pensada para pruebas rápidas y reemplazar al orquestador
complejo cuando se necesite un comportamiento determinista.
"""
from typing import Dict, Optional
from datetime import datetime
import re

# Estado en memoria simple
_STATE: Dict[str, Dict] = {}

REGIONS = [
    'bogotá', 'bogota', 'antioquia', 'medellín', 'medellin', 'magdalena', 'atlántico', 'atlántico',
    'cordoba', 'córdoba', 'cundinamarca', 'tolima', 'cauca', 'nariño', 'huila', 'meta',
    'bolívar', 'sucre', 'norte de santander', 'santander', 'arauca'
]

CONNECTIVITY_KEYWORDS = ['internet', 'conectividad', 'wifi', '4g', 'sin internet', 'no tengo internet', 'cobertura']


class SimpleScriptBot:
    """Bot determinista y con guion simple."""

    def _key(self, user_email: Optional[str], conv_id: Optional[str]) -> str:
        return f"{user_email or 'anon'}::{conv_id or 'default'}"

    def reset(self, user_email: Optional[str], conv_id: Optional[str]) -> None:
        key = self._key(user_email, conv_id)
        _STATE.pop(key, None)

    def _init_state(self, user_email: Optional[str], conv_id: Optional[str]) -> Dict:
        key = self._key(user_email, conv_id)
        if key not in _STATE:
            _STATE[key] = {
                'stage': 'initial',
                'region': None,
                'problem': None,
                'history': []
            }
        return _STATE[key]

    def _extract_region(self, message: str) -> Optional[str]:
        m = message.lower()
        for r in REGIONS:
            if r in m:
                # retornar con capitalizada simple (primera letra mayúscula)
                return r.title()
        # patrones como "soy de X" o "vivo en X"
        m2 = re.search(r"soy de\s+([A-Za-zÁÉÍÓÚáéíóúñÑ ]{2,30})", message, re.I)
        if m2:
            return m2.group(1).strip().title()
        m3 = re.search(r"vivo en\s+([A-Za-zÁÉÍÓÚáéíóúñÑ ]{2,30})", message, re.I)
        if m3:
            return m3.group(1).strip().title()
        return None

    def _extract_problem(self, message: str) -> Optional[str]:
        m = message.lower()
        for kw in CONNECTIVITY_KEYWORDS:
            if kw in m:
                return 'conectividad'
        # palabras genéricas
        if 'educación' in m or 'educacion' in m or 'escuela' in m:
            return 'educacion'
        return None

    def process_message(self, user_message: str, user_email: Optional[str] = None, conv_id: Optional[str] = None) -> Dict:
        """Procesa un mensaje siguiendo el guion simple.

        Retorna dict con keys: success, response, intent, entities, timestamp
        """
        st = self._init_state(user_email, conv_id)
        msg = (user_message or '').strip()
        lc = msg.lower()

        # Registrar en historial
        st['history'].append({'sender': 'user', 'content': msg, 'timestamp': datetime.now().isoformat()})

        # Stage logic
        if st['stage'] == 'initial':
            # Si el usuario saluda -> responder saludo y pedir region+problema
            if any(g in lc for g in ['hola', 'buenos', 'buenas', 'hi', 'hey']):
                st['stage'] = 'asked_region'
                resp = "¡Hola! Soy BOT simple. ¿De qué región eres y cuál es tu problema?"
                # guardar respuesta
                st['history'].append({'sender': 'bot', 'content': resp, 'timestamp': datetime.now().isoformat()})
                return {
                    'success': True,
                    'response': resp,
                    'intent': 'saludo',
                    'entities': {},
                    'timestamp': datetime.now().isoformat()
                }

            # Si el usuario ya provee región+problema en el primer mensaje
            region = self._extract_region(msg)
            problem = self._extract_problem(msg)
            if region and problem:
                st['region'] = region
                st['problem'] = problem
                st['stage'] = 'done'
                resp = self._build_solution(region, problem)
                st['history'].append({'sender': 'bot', 'content': resp, 'timestamp': datetime.now().isoformat()})
                return {
                    'success': True,
                    'response': resp,
                    'intent': 'solution',
                    'entities': {'region': region, 'problem': problem},
                    'timestamp': datetime.now().isoformat()
                }

            # Default fallback when message is not a greeting
            resp = "Hola. ¿De qué región eres y qué problema tienes?"
            st['stage'] = 'asked_region'
            st['history'].append({'sender': 'bot', 'content': resp, 'timestamp': datetime.now().isoformat()})
            return {'success': True, 'response': resp, 'intent': 'ask_region', 'entities': {}, 'timestamp': datetime.now().isoformat()}

        elif st['stage'] in ('asked_region', 'asked_problem'):
            # Intentar extraer región y problema del mensaje
            region = self._extract_region(msg) or st.get('region')
            problem = self._extract_problem(msg) or st.get('problem')

            if region:
                st['region'] = region
            if problem:
                st['problem'] = problem

            if st.get('region') and st.get('problem'):
                st['stage'] = 'done'
                resp = self._build_solution(st['region'], st['problem'])
                st['history'].append({'sender': 'bot', 'content': resp, 'timestamp': datetime.now().isoformat()})
                return {
                    'success': True,
                    'response': resp,
                    'intent': 'solution',
                    'entities': {'region': st['region'], 'problem': st['problem']},
                    'timestamp': datetime.now().isoformat()
                }
            else:
                # Si falta alguno, pedir lo que falta
                if not st.get('region') and not st.get('problem'):
                    ask = "Por favor dime tu región y cuál es el problema."
                elif not st.get('region'):
                    ask = "¿De qué región eres?"
                else:
                    ask = "¿Cuál es exactamente el problema de conectividad?"
                st['stage'] = 'asked_region'
                st['history'].append({'sender': 'bot', 'content': ask, 'timestamp': datetime.now().isoformat()})
                return {'success': True, 'response': ask, 'intent': 'clarify', 'entities': {}, 'timestamp': datetime.now().isoformat()}

        else:
            # stage == done o desconocido: repetir solución breve
            region = st.get('region') or 'tu región'
            problem = st.get('problem') or 'el problema'
            resp = self._build_solution(region, problem)
            st['history'].append({'sender': 'bot', 'content': resp, 'timestamp': datetime.now().isoformat()})
            return {'success': True, 'response': resp, 'intent': 'solution_repeat', 'entities': {'region': region, 'problem': problem}, 'timestamp': datetime.now().isoformat()}

    def _build_solution(self, region: str, problem: str) -> str:
        if problem == 'conectividad':
            return (
                f"Entiendo que en {region} tienes problemas de conectividad. Sugerencias prácticas:\n"
                "1) Reinicia y revisa el router/modem; 2) Comprueba si el proveedor tiene caída; 3) Usa puntos comunitarios de WiFi o datos móviles compartidos;\n"
                "4) Si es persistente, recopila ubicación y evidencia y contacta a tu proveedor o a la secretaría de educación local para apoyo."
            )
        elif problem == 'educacion':
            return (
                f"En {region}, para problemas educativos te recomiendo: 1) Priorizar materiales offline; 2) Coordinar con instituciones locales para entrega de recursos; 3) Buscar apoyos o subsidios educativos."
            )
        else:
            return f"En {region}, atención a {problem}. Recolecta información básica (acceso, número de estudiantes, infraestructura) para poder recomendar acciones concretas."
