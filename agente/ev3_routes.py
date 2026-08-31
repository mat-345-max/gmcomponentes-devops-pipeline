"""
ev3_routes.py - API REST EV3 para observabilidad GM-COMPONENTS

Expone metricas, trazabilidad, analisis y seguridad sin modificar EV1/EV2.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ev3_bridge import (
    EV3_AVAILABLE,
    EV3_LOAD_ERROR,
    ev3_metrics,
    validate_input,
)


EV3_PATH = Path(__file__).resolve().parents[1] / "ev3_observability"
if str(EV3_PATH) not in sys.path:
    sys.path.insert(0, str(EV3_PATH))

from analyzer import analyze_traces, build_findings
from recommendations import generate_recommendations
from traceability import clear_traces, read_traces


router = APIRouter(prefix="/ev3", tags=["EV3 Observability"])


class SecurityValidateRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Mensaje a validar con el filtro EV3.")


@router.get("/health")
def ev3_health() -> dict[str, Any]:
    return {
        "ok": True,
        "service": "gm-components-ev3-observability",
        "ev3_available": EV3_AVAILABLE,
        "load_error": EV3_LOAD_ERROR or None,
    }


@router.get("/summary")
def ev3_summary() -> dict[str, Any]:
    trace_stats = analyze_traces()

    metrics_summary: dict[str, Any] = {}
    if EV3_AVAILABLE and ev3_metrics is not None:
        metrics_summary = ev3_metrics.summary()

    return {
        "ev3_available": EV3_AVAILABLE,
        "metrics": metrics_summary,
        "traces": {
            "total_events": trace_stats.get("total_trace_events", 0),
            "total_starts": trace_stats.get("total_agent_starts", 0),
            "total_ends": trace_stats.get("total_agent_ends", 0),
            "total_errors": trace_stats.get("total_errors", 0),
            "total_security_blocks": trace_stats.get("total_security_blocks", 0),
            "incomplete_traces": trace_stats.get("incomplete_traces", 0),
            "avg_latency_ms": trace_stats.get("avg_latency_ms", 0),
            "max_latency_ms": trace_stats.get("max_latency_ms", 0),
            "avg_precision_score": metrics_summary.get("avg_precision_score", 0),
            "avg_consistency_score": metrics_summary.get("avg_consistency_score", 0),
            "error_rate": metrics_summary.get("error_rate", 0),
        },
        "by_intent": trace_stats.get("intents", {}),
        "by_agent": metrics_summary.get("by_agent", {}),
        "tool_usage": trace_stats.get("tools", {}),
        "avg_latency_by_intent": trace_stats.get("avg_latency_by_intent", {}),
    }


@router.get("/traces")
def ev3_traces(limit: int = 50) -> dict[str, Any]:
    safe_limit = max(1, min(limit, 200))
    traces = read_traces(limit=safe_limit)

    return {
        "total_returned": len(traces),
        "limit": safe_limit,
        "traces": traces,
    }


@router.get("/analysis")
def ev3_analysis() -> dict[str, Any]:
    stats = analyze_traces()
    findings = build_findings()

    return {
        "stats": stats,
        "findings": findings,
        "recent_errors": stats.get("recent_errors", []),
        "recent_blocks": stats.get("recent_blocks", []),
    }


@router.get("/recommendations")
def ev3_recommendations() -> dict[str, Any]:
    stats = analyze_traces()
    items = generate_recommendations(stats)

    return {
        "total": len(items),
        "recommendations": items,
    }


@router.post("/security/validate")
def ev3_security_validate(payload: SecurityValidateRequest) -> dict[str, Any]:
    if not EV3_AVAILABLE or validate_input is None:
        return {
            "allowed": True,
            "reason": "EV3 no disponible, validacion omitida.",
            "category": "ev3_disabled",
            "safe_response": "",
        }

    result = validate_input(payload.message)

    return {
        "allowed": result.allowed,
        "reason": result.reason,
        "category": result.category,
        "safe_response": result.safe_response,
    }


@router.delete("/traces")
def ev3_clear_traces() -> dict[str, Any]:
    clear_traces()

    if EV3_AVAILABLE and ev3_metrics is not None:
        ev3_metrics.reset()

    return {
        "ok": True,
        "message": "Trazas EV3 y metricas en memoria fueron limpiadas.",
    }