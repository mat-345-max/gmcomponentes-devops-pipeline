import time
from fastapi import FastAPI, Query, Body
from agents.orchestrator_agent import run_orchestrator
from memory.session_store import session_store
from schemas.agent_schemas import AgentChatRequest, AgentChatResponse
from ev3_api import (
    get_ev3_health,
    get_ev3_metrics,
    get_ev3_traces,
    get_ev3_recommendations,
    get_ev3_security_check,
)
from ev3_bridge import (
    EV3_AVAILABLE,
    ev3_metrics as ev3_metrics_instance,
    generate_trace_id,
    log_agent_end,
    log_agent_start,
    sanitize_for_logs,
)

app = FastAPI(
    title="GM-COMPONENTS Agent Service",
    version="0.2.0",
    description="Servicio Python 3.11 para agentes EV2 + EV3 Observabilidad.",
)

# ─── EV2 endpoints ────────────────────────────────────────────────────────────

@app.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "service": "gm-components-agent",
        "python": "3.11",
    }

@app.post("/agent/chat", response_model=AgentChatResponse)
def agent_chat(payload: AgentChatRequest) -> AgentChatResponse:
    return run_orchestrator(payload)

@app.delete("/agent/session/{session_id}")
def clear_session(session_id: str) -> dict:
    session_store.clear(session_id)
    return {
        "ok": True,
        "session_id": session_id,
        "message": "Sesion limpiada.",
    }

# ─── EV3 endpoints ────────────────────────────────────────────────────────────

@app.get("/ev3/health")
def ev3_health():
    return get_ev3_health()

@app.get("/ev3/metrics")
def ev3_metrics():
    return get_ev3_metrics()

@app.get("/ev3/traces")
def ev3_traces():
    return get_ev3_traces()

@app.get("/ev3/recommendations")
def ev3_recommendations():
    return get_ev3_recommendations()

@app.get("/ev3/security-check")
def ev3_security_check(message: str = Query(..., description="Texto a validar")):
    return get_ev3_security_check(message)

@app.post("/ev3/log-event")
def ev3_log_event(payload: dict = Body(...)):
    """Recibe eventos desde groq-proxy Node y los registra en EV3."""
    if not EV3_AVAILABLE:
        return {"ok": False, "reason": "EV3 no disponible"}
    try:
        trace_id  = generate_trace_id() if generate_trace_id else f"ev3-node-{int(time.time())}"
        source    = payload.get("source", "node_proxy")
        intent    = payload.get("intent", "general")
        message   = payload.get("message", "")
        latency   = payload.get("latency_ms", 0)
        status    = payload.get("status", "ok")
        error     = payload.get("error")
        safe_msg  = sanitize_for_logs(message) if sanitize_for_logs else message

        log_agent_start(
            trace_id=trace_id,
            session_id=f"node_{source}",
            message=safe_msg,
        )

        ev3_metrics_instance.record_call(
            trace_id=trace_id,
            session_id=f"node_{source}",
            agent_name=source,
            intent=intent,
            user_message=message[:200],
            answer="",
            status=status,
            latency_ms=latency,
            used_tools=[source],
            memory_messages=0,
            data=payload,
            error=error,
        )

        log_agent_end(
            trace_id=trace_id,
            session_id=f"node_{source}",
            intent=intent,
            answer="",
            used_tools=[source],
            latency_ms=latency,
            status=status,
            data=payload,
            error=error,
        )

        return {"ok": True, "trace_id": trace_id}
    except Exception as e:
        return {"ok": False, "error": str(e)}