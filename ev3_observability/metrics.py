"""
metrics.py - EV3 Observabilidad GM-COMPONENTS

Este modulo implementa metricas para evaluar agentes de IA existentes:
- Latencia
- Frecuencia de errores
- Consistencia aproximada
- Precision estimada por reglas
- Uso de tools
- Intent detectado
- Agente ejecutado

La idea es usarlo como capa EV3 separada, sin reemplazar EV1 ni EV2.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from statistics import mean
from typing import Any


@dataclass
class AgentMetricRecord:
    trace_id: str
    session_id: str
    timestamp: str
    agent_name: str
    intent: str
    user_message: str
    answer_preview: str
    status: str
    latency_ms: float
    used_tools: list[str]
    memory_messages: int
    error: str | None
    precision_score: float
    consistency_score: float


class EV3MetricsCollector:
    """
    Recolector de metricas en memoria para la EV3.

    Se puede usar desde el Orchestrator Agent o desde un wrapper externo.
    No depende de FastAPI, Angular ni Node.
    """

    def __init__(self) -> None:
        self.records: list[AgentMetricRecord] = []
        self._active_calls: dict[str, float] = {}

    def start_timer(self, trace_id: str) -> None:
        """Marca el inicio de una ejecucion."""
        self._active_calls[trace_id] = time.perf_counter()

    def stop_timer(self, trace_id: str) -> float:
        """Calcula latencia en milisegundos."""
        start = self._active_calls.pop(trace_id, None)
        if start is None:
            return 0.0

        return round((time.perf_counter() - start) * 1000, 2)

    def estimate_precision(
        self,
        intent: str,
        answer: str,
        data: dict[str, Any] | None = None,
    ) -> float:
        """
        Estima precision funcional con reglas simples.

        No reemplaza una evaluacion humana, pero sirve como metrica academica:
        - FAQ con respuesta y evidencia obtiene mayor puntaje.
        - Recommendation con sugerencias obtiene mayor puntaje.
        - Error o respuesta vacia obtiene 0.
        """
        data = data or {}
        answer_text = str(answer or "").strip()

        if not answer_text:
            return 0.0

        if data.get("error") or data.get("detail"):
            return 0.2

        if intent == "faq":
            score = 0.45

            if len(answer_text) >= 40:
                score += 0.2

            if data.get("productoDestacado"):
                score += 0.2

            related = data.get("productosRelacionados")
            if isinstance(related, list) and len(related) > 0:
                score += 0.1

            suggestions = data.get("sugerencias")
            if isinstance(suggestions, list) and len(suggestions) > 0:
                score += 0.05

            return round(min(score, 1.0), 2)

        if intent == "recommendation":
            score = 0.4

            if len(answer_text) >= 40:
                score += 0.15

            suggestions = data.get("suggestions")
            if isinstance(suggestions, list) and len(suggestions) > 0:
                score += 0.25

            if data.get("nextStep"):
                score += 0.1

            if data.get("state"):
                score += 0.1

            return round(min(score, 1.0), 2)

        if intent == "catalog":
            matches = data.get("matches")
            if isinstance(matches, list) and len(matches) > 0:
                return 0.75
            return 0.45

        return 0.5 if answer_text else 0.0

    def estimate_consistency(
        self,
        intent: str,
        used_tools: list[str],
        data: dict[str, Any] | None = None,
    ) -> float:
        """
        Estima consistencia revisando si intent, tools y fuente coinciden.

        Ejemplos:
        - intent faq deberia usar gm_components_faq_rag_ev1.
        - intent recommendation deberia usar gm_components_recommendation_ev1.
        """
        data = data or {}
        tools = used_tools or []
        score = 0.5

        if intent == "faq":
            if "gm_components_faq_rag_ev1" in tools:
                score += 0.3
            if data.get("source") == "faq_agent":
                score += 0.2

        elif intent == "recommendation":
            if "gm_components_recommendation_ev1" in tools:
                score += 0.3
            if data.get("source") == "recommendation_agent":
                score += 0.2

        elif intent == "catalog":
            if "catalog_tool" in tools or "gm_components_catalog_search" in tools:
                score += 0.3
            if data.get("source") == "catalog_tool":
                score += 0.2

        elif intent == "general":
            if data.get("source") == "orchestrator_agent":
                score += 0.3

        return round(min(score, 1.0), 2)

    def record_call(
        self,
        trace_id: str,
        session_id: str,
        agent_name: str,
        intent: str,
        user_message: str,
        answer: str,
        status: str,
        latency_ms: float,
        used_tools: list[str] | None = None,
        memory_messages: int = 0,
        data: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> AgentMetricRecord:
        """Registra una ejecucion del agente."""
        used_tools = used_tools or []
        data = data or {}

        record = AgentMetricRecord(
            trace_id=trace_id,
            session_id=session_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent_name=agent_name,
            intent=intent,
            user_message=user_message[:500],
            answer_preview=str(answer or "")[:500],
            status=status,
            latency_ms=latency_ms,
            used_tools=used_tools,
            memory_messages=memory_messages,
            error=error,
            precision_score=self.estimate_precision(intent, answer, data),
            consistency_score=self.estimate_consistency(intent, used_tools, data),
        )

        self.records.append(record)
        return record

    def summary(self) -> dict[str, Any]:
        """Devuelve resumen general para dashboard o API."""
        total = len(self.records)
        errors = [item for item in self.records if item.status == "error" or item.error]
        successful = [item for item in self.records if item.status == "ok"]

        latencies = [item.latency_ms for item in self.records]
        precision_scores = [item.precision_score for item in self.records]
        consistency_scores = [item.consistency_score for item in self.records]

        by_intent: dict[str, int] = {}
        by_agent: dict[str, int] = {}
        tool_usage: dict[str, int] = {}

        for item in self.records:
            by_intent[item.intent] = by_intent.get(item.intent, 0) + 1
            by_agent[item.agent_name] = by_agent.get(item.agent_name, 0) + 1

            for tool in item.used_tools:
                tool_usage[tool] = tool_usage.get(tool, 0) + 1

        return {
            "total_requests": total,
            "successful_requests": len(successful),
            "total_errors": len(errors),
            "error_rate": round(len(errors) / total, 3) if total else 0.0,
            "avg_latency_ms": round(mean(latencies), 2) if latencies else 0.0,
            "max_latency_ms": max(latencies) if latencies else 0.0,
            "avg_precision_score": round(mean(precision_scores), 2) if precision_scores else 0.0,
            "avg_consistency_score": round(mean(consistency_scores), 2) if consistency_scores else 0.0,
            "by_intent": by_intent,
            "by_agent": by_agent,
            "tool_usage": tool_usage,
        }

    def records_as_dicts(self) -> list[dict[str, Any]]:
        """Convierte registros a diccionarios para guardar o visualizar."""
        return [asdict(record) for record in self.records]

    def reset(self) -> None:
        """Limpia metricas en memoria."""
        self.records = []
        self._active_calls = {}


ev3_metrics = EV3MetricsCollector()