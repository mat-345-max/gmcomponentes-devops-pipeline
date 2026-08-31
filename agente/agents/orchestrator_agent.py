from agents.faq_agent import run_faq_agent
from agents.planner_agent import build_plan, detect_intent
from agents.recommendation_agent import run_recommendation_agent
from ev3_bridge import (
    EV3_AVAILABLE,
    ev3_metrics,
    generate_trace_id,
    log_agent_end,
    log_agent_start,
    log_security_block,
    sanitize_for_logs,
    validate_input,
)
from memory.session_store import session_store
from schemas.agent_schemas import AgentChatRequest, AgentChatResponse
from tools.catalog_pool import search_catalog
from tools.memory_tool import get_memory_context


def should_continue_recommendation(memory, message: str) -> bool:
    if not memory.recommendation.active:
        return False

    text = message.lower().strip()

    continuation_words = [
        "sin preferencia",
        "sin marca",
        "ninguna",
        "cualquiera",
        "gaming",
        "oficina",
        "edicion",
        "edición",
        "diseno",
        "diseño",
        "general",
        "calidad",
        "precio",
        "calidad/precio",
        "calidad precio",
    ]

    return any(word in text for word in continuation_words) or len(text.split()) <= 4


def run_orchestrator(payload: AgentChatRequest) -> AgentChatResponse:
    original_message = payload.message
    ev3_trace_id = generate_trace_id() if EV3_AVAILABLE else "ev3-disabled"

    if EV3_AVAILABLE:
        safe_message = sanitize_for_logs(original_message)

        log_agent_start(
            trace_id=ev3_trace_id,
            session_id=payload.session_id,
            message=safe_message,
        )

        ev3_metrics.start_timer(ev3_trace_id)

        security_result = validate_input(original_message)
        if not security_result.allowed:
            log_security_block(
                trace_id=ev3_trace_id,
                session_id=payload.session_id,
                message=safe_message,
                reason=security_result.reason,
            )

            latency_ms = ev3_metrics.stop_timer(ev3_trace_id)

            ev3_metrics.record_call(
                trace_id=ev3_trace_id,
                session_id=payload.session_id,
                agent_name="security_guard",
                intent="general",
                user_message=safe_message,
                answer=security_result.safe_response,
                status="blocked",
                latency_ms=latency_ms,
                used_tools=["ev3_security_filter"],
                memory_messages=0,
                data={"source": "ev3_security"},
                error=security_result.reason,
            )

            return AgentChatResponse(
                session_id=payload.session_id,
                intent="general",
                answer=security_result.safe_response,
                plan=[],
                memory_messages=0,
                used_tools=["ev3_security_filter"],
                data={
                    "source": "ev3_security",
                    "integration_status": "blocked_by_ev3",
                    "trace_id": ev3_trace_id,
                    "security_reason": security_result.reason,
                },
            )

    memory = session_store.get(payload.session_id)
    memory.add_user_message(payload.message)

    message = payload.message.strip()
    forced_intent = None

    if message.lower().startswith("/rec "):
        forced_intent = "recommendation"
        payload.message = message[5:].strip()

    elif message.lower().startswith("/faq "):
        forced_intent = "faq"
        payload.message = message[5:].strip()

    intent = forced_intent or detect_intent(payload.message)

    if should_continue_recommendation(memory, payload.message):
        intent = "recommendation"

    plan = build_plan(intent)

    used_tools = ["planner_agent", "memory_tool"]
    memory_context = get_memory_context(payload.session_id)

    if intent == "faq":
        answer, tool_names, data = run_faq_agent(
            payload.message,
            payload.products,
            payload.session_id,
        )
        used_tools.extend(tool_names)

    elif intent == "recommendation":
        answer, tool_names, data = run_recommendation_agent(
            payload.message,
            payload.products,
            memory,
            payload.session_id,
        )
        used_tools.extend(tool_names)

    elif intent == "catalog":
        matches = search_catalog(payload.message, payload.products)
        used_tools.append("catalog_tool")
        data = {
            "source": "catalog_tool",
            "matches": matches,
        }

        if matches:
            answer = f"Encontre {len(matches)} productos relacionados en el catalogo."
        else:
            answer = "No encontre productos relacionados en el catalogo recibido."

    else:
        data = {
            "source": "orchestrator_agent",
            "memory_context": memory_context,
        }
        answer = (
            "Puedo ayudarte con preguntas FAQ, busqueda de catalogo o recomendaciones. "
            "Dime que componente buscas o que duda tienes sobre GM-COMPONENTS."
        )

    memory.add_assistant_message(answer)

    if EV3_AVAILABLE:
        latency_ms = ev3_metrics.stop_timer(ev3_trace_id)
        status = "error" if data.get("error") or data.get("detail") else "ok"
        safe_message = sanitize_for_logs(original_message)

        metric_record = ev3_metrics.record_call(
            trace_id=ev3_trace_id,
            session_id=payload.session_id,
            agent_name=str(data.get("source") or "orchestrator_agent"),
            intent=intent,
            user_message=safe_message,
            answer=answer,
            status=status,
            latency_ms=latency_ms,
            used_tools=used_tools,
            memory_messages=memory.count(),
            data=data,
            error=data.get("error") or data.get("detail"),
        )

        log_agent_end(
            trace_id=ev3_trace_id,
            session_id=payload.session_id,
            intent=intent,
            answer=answer,
            used_tools=used_tools,
            latency_ms=latency_ms,
            status=status,
            data=data,
            error=data.get("error") or data.get("detail"),
            precision_score=metric_record.precision_score,      # NUEVO
            consistency_score=metric_record.consistency_score,  # NUEVO
        )

        data = {
            **data,
            "ev3_observability": {
                "enabled": True,
                "trace_id": ev3_trace_id,
                "latency_ms": latency_ms,
                "status": status,
            },
        }

    return AgentChatResponse(
        session_id=payload.session_id,
        intent=intent,
        answer=answer,
        plan=plan,
        memory_messages=memory.count(),
        used_tools=used_tools,
        data=data,
    )