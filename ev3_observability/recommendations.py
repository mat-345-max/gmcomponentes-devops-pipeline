"""
recommendations.py - EV3 Recomendaciones Tecnicas

Genera recomendaciones basadas en metricas y trazabilidad.
Sirve para IL3.4 y para el reporte tecnico de la EV3.
"""

from __future__ import annotations

from typing import Any


def generate_recommendations(stats: dict[str, Any]) -> list[dict[str, str]]:
    recommendations: list[dict[str, str]] = []

    avg_latency = float(stats.get("avg_latency_ms", 0) or 0)
    total_errors = int(stats.get("total_errors", 0) or 0)
    incomplete = int(stats.get("incomplete_traces", 0) or 0)
    security_blocks = int(stats.get("total_security_blocks", 0) or 0)

    if avg_latency > 5000:
        recommendations.append({
            "area": "Desempeño",
            "recommendation": "Implementar cache para consultas frecuentes de FAQ y respuestas de catalogo.",
            "justification": (
                f"La latencia promedio observada es {avg_latency} ms, "
                "lo que puede afectar la experiencia del usuario."
            ),
        })

    if total_errors > 0:
        recommendations.append({
            "area": "Confiabilidad",
            "recommendation": "Agregar manejo diferenciado para errores de Groq, Voyage, MongoDB y FastAPI.",
            "justification": (
                f"Se observaron {total_errors} errores en la trazabilidad. "
                "Separar causas permite diagnosticar fallas con mayor precision."
            ),
        })

    if incomplete > 0:
        recommendations.append({
            "area": "Trazabilidad",
            "recommendation": "Registrar eventos intermedios por etapa: planner, memoria, tool y respuesta final.",
            "justification": (
                f"Hay {incomplete} trazas incompletas. "
                "Mayor granularidad ayudara a detectar en que etapa se interrumpe el flujo."
            ),
        })

    if security_blocks > 0:
        recommendations.append({
            "area": "Seguridad",
            "recommendation": "Mantener filtros preventivos y documentar politicas de privacidad para datos sensibles.",
            "justification": (
                f"La capa EV3 bloqueo {security_blocks} solicitud(es). "
                "Esto demuestra control responsable antes de invocar herramientas o modelos."
            ),
        })

    if not recommendations:
        recommendations.append({
            "area": "Operacion",
            "recommendation": "Mantener monitoreo continuo de latencia, errores, consistencia y uso de tools.",
            "justification": (
                "Las metricas actuales no muestran puntos criticos severos, "
                "pero el monitoreo continuo permite detectar degradacion futura."
            ),
        })

    recommendations.append({
        "area": "Escalabilidad",
        "recommendation": "Evaluar rate limiting por session_id y cola de tareas para consultas concurrentes.",
        "justification": (
            "El proyecto depende de servicios externos con limites de uso. "
            "Controlar concurrencia reduce errores por cuota y mejora sostenibilidad."
        ),
    })

    recommendations.append({
        "area": "Sostenibilidad",
        "recommendation": "Definir retencion de logs y limpieza periodica de memoria larga local.",
        "justification": (
            "La memoria y los logs pueden crecer con el uso. "
            "Una politica de retencion mantiene el sistema liviano y auditable."
        ),
    })

    return recommendations