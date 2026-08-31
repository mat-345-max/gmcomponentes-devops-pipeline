"""
security.py - EV3 Seguridad y Uso Responsable GM-COMPONENTS

Implementa filtros previos para agentes:
- bloqueo de solicitudes peligrosas
- deteccion de datos sensibles
- criterios eticos basicos
- respuesta segura sin llamar al agente

Este modulo sirve para IL3.3.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


BLOCKED_PATTERNS = [
    r"\bhackear?\b",
    r"\bmalware\b",
    r"\bvirus\b",
    r"\bexploit\b",
    r"\bphishing\b",
    r"\bransomware\b",
    r"\bsqlmap\b",
    r"\binjection\b",
    r"\brobar\b.{0,30}\bcontrase",
    r"\bcontraseñas?\b.{0,30}\brobar\b",
    r"\bataque\b.{0,30}\bservidor\b",
    r"\bcomo\b.{0,30}\bromper\b.{0,30}\bseguridad\b",
]

SENSITIVE_DATA_PATTERNS = [
    r"\b\d{1,2}\.?\d{3}\.?\d{3}-[\dkK]\b",
    r"\b\d{16}\b",
    r"\b(?:api[_-]?key|token|password|contraseña|secreto)\b",
]

ETHICAL_DISCLAIMER = (
    "Tu solicitud fue bloqueada por la capa EV3 de seguridad y uso responsable. "
    "No puedo ayudar con instrucciones que puedan facilitar abuso, robo de credenciales, "
    "malware, ataques o exposicion de datos sensibles."
)

PRIVACY_WARNING = (
    "Detecte posible informacion sensible en tu mensaje. Por privacidad, evita compartir "
    "RUT, tarjetas, contraseñas, tokens o claves API."
)


@dataclass
class SecurityResult:
    allowed: bool
    reason: str
    category: str
    safe_response: str


def _matches_any(patterns: list[str], text: str) -> tuple[bool, str]:
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True, pattern

    return False, ""


def validate_input(message: str) -> SecurityResult:
    """
    Valida un mensaje antes de ejecutar el agente.

    Retorna allowed=False cuando debe bloquearse.
    """
    text = str(message or "").strip()

    if not text:
        return SecurityResult(
            allowed=False,
            reason="Mensaje vacio",
            category="empty_input",
            safe_response="Escribe una consulta valida para poder ayudarte.",
        )

    blocked, blocked_pattern = _matches_any(BLOCKED_PATTERNS, text)
    if blocked:
        return SecurityResult(
            allowed=False,
            reason=f"Patron bloqueado: {blocked_pattern}",
            category="harmful_request",
            safe_response=ETHICAL_DISCLAIMER,
        )

    sensitive, sensitive_pattern = _matches_any(SENSITIVE_DATA_PATTERNS, text)
    if sensitive:
        return SecurityResult(
            allowed=False,
            reason=f"Posible dato sensible: {sensitive_pattern}",
            category="privacy_risk",
            safe_response=PRIVACY_WARNING,
        )

    return SecurityResult(
        allowed=True,
        reason="Input permitido",
        category="safe",
        safe_response="",
    )


def sanitize_for_logs(message: str, max_length: int = 500) -> str:
    """
    Reduce exposicion de datos sensibles en logs.

    No cambia el mensaje que usa el agente, solo el texto registrado.
    """
    text = str(message or "")

    text = re.sub(
        r"\b\d{1,2}\.?\d{3}\.?\d{3}-[\dkK]\b",
        "[RUT_OCULTO]",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\b\d{16}\b",
        "[TARJETA_OCULTA]",
        text,
    )

    text = re.sub(
        r"(api[_-]?key|token|password|contraseña|secreto)\s*[:=]\s*\S+",
        r"\1=[OCULTO]",
        text,
        flags=re.IGNORECASE,
    )

    return text[:max_length]


def safe_eval(expression: str) -> str:
    """
    Evaluador matematico seguro para evidencia de IL3.3.

    Solo acepta numeros y operadores matematicos basicos.
    """
    allowed = set("0123456789+-*/(). ")
    if not set(expression) <= allowed:
        return "Expresion no permitida."

    try:
        return str(eval(expression, {"__builtins__": {}}, {}))
    except Exception:
        return "Error en la expresion."