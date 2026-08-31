"""
traceability.py - EV3 Trazabilidad GM-COMPONENTS

Registra cada ejecucion del agente en formato JSONL para auditoria:
- trace_id
- session_id
- intent
- tools usadas
- latencia
- errores
- resultado resumido

Este modulo sirve para IL3.2.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
TRACE_LOG_FILE = LOG_DIR / "ev3_agent_traces.jsonl"


def generate_trace_id() -> str:
    """Genera un identificador unico para seguir una ejecucion."""
    return f"ev3-{uuid.uuid4().hex[:12]}"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_log_dir() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def to_serializable(value: Any) -> Any:
    """Convierte objetos a tipos serializables por JSON."""
    if is_dataclass(value):
        return asdict(value)

    if isinstance(value, Path):
        return str(value)

    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


def append_trace(event: dict[str, Any]) -> None:
    """Agrega una linea JSONL al archivo de trazabilidad."""
    ensure_log_dir()

    payload = {
        "logged_at": utc_now(),
        **{key: to_serializable(value) for key, value in event.items()},
    }

    with TRACE_LOG_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(payload, ensure_ascii=False) + "\n")


def log_agent_start(
    trace_id: str,
    session_id: str,
    message: str,
    source: str = "ev2_orchestrator",
) -> None:
    append_trace(
        {
            "event": "agent_start",
            "trace_id": trace_id,
            "session_id": session_id,
            "source": source,
            "message_preview": str(message or "")[:500],
        }
    )


def log_agent_end(
    trace_id: str,
    session_id: str,
    intent: str,
    answer: str,
    used_tools: list[str],
    latency_ms: float,
    status: str,
    data: dict[str, Any] | None = None,
    error: str | None = None,
    precision_score: float | None = None,  # NUEVO
    consistency_score: float | None = None,  # NUEVO
) -> None:
    data = data or {}
    append_trace(
        {
            "event": "agent_end",
            "trace_id": trace_id,
            "session_id": session_id,
            "intent": intent,
            "answer_preview": str(answer or "")[:500],
            "used_tools": used_tools,
            "latency_ms": latency_ms,
            "status": status,
            "source": data.get("source"),
            "integration_status": data.get("integration_status"),
            "error": error,
            "precision_score": precision_score,  # NUEVO
            "consistency_score": consistency_score,  # NUEVO
        }
    )


def log_security_block(
    trace_id: str,
    session_id: str,
    message: str,
    reason: str,
) -> None:
    append_trace(
        {
            "event": "security_block",
            "trace_id": trace_id,
            "session_id": session_id,
            "message_preview": str(message or "")[:500],
            "reason": reason,
            "status": "blocked",
        }
    )


def read_traces(limit: int | None = None) -> list[dict[str, Any]]:
    """Lee trazas desde el archivo JSONL."""
    if not TRACE_LOG_FILE.exists():
        return []

    rows: list[dict[str, Any]] = []

    with TRACE_LOG_FILE.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue

            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                rows.append(
                    {
                        "logged_at": utc_now(),
                        "event": "parse_error",
                        "raw": line,
                    }
                )

    if limit is not None:
        return rows[-limit:]

    return rows


def clear_traces() -> None:
    """Limpia el archivo de trazabilidad."""
    ensure_log_dir()
    TRACE_LOG_FILE.write_text("", encoding="utf-8")
