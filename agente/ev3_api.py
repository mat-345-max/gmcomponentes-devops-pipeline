# agente/ev3_api.py
# Capa EV3: lógica de datos para los endpoints de observabilidad

from ev3_bridge import EV3Bridge

bridge = EV3Bridge()


def _read_raw_traces():
    """Lee el JSONL de trazas y retorna lista de dicts."""
    import json

    log_path = bridge.get_log_path()
    if log_path is None or not log_path.exists():
        return []
    traces = []
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    traces.append(json.loads(line))
    except Exception:
        pass
    return traces


def get_ev3_health():
    return {
        "status": "ok",
        "ev3_enabled": bridge.ev3_available,
        "message": "EV3 Observabilidad activa"
        if bridge.ev3_available
        else "EV3 no disponible",
    }


def get_ev3_metrics():
    if not bridge.ev3_available:
        return {"error": "EV3 no disponible", "metrics": {}}
    try:
        collector = bridge.get_metrics_collector()
        if collector is None:
            return {"error": "MetricsCollector no inicializado", "metrics": {}}
        return {"status": "ok", "metrics": collector.summary()}
    except Exception as e:
        return {"error": str(e), "metrics": {}}


def get_ev3_traces():
    if not bridge.ev3_available:
        return {"error": "EV3 no disponible", "traces": [], "analysis": {}}
    try:
        analyzer_module = bridge.get_analyzer()
        if analyzer_module is None:
            return {"error": "Analyzer no disponible", "traces": [], "analysis": {}}

        analysis = analyzer_module.analyze_traces()  # CAMBIO
        analysis["findings"] = analyzer_module.build_findings()  # NUEVO

        # Alias para compatibilidad con el frontend Angular
        analysis["total_events"] = analysis.get("total_trace_events")
        analysis["agent_starts"] = analysis.get("total_agent_starts")
        analysis["agent_ends"] = analysis.get("total_agent_ends")
        analysis["errors"] = analysis.get("total_errors")
        analysis["security_blocks"] = analysis.get("total_security_blocks")

        traces = _read_raw_traces()
        return {"status": "ok", "analysis": analysis, "traces": traces[-50:]}
    except Exception as e:
        return {"error": str(e), "traces": [], "analysis": {}}


def get_ev3_recommendations():
    if not bridge.ev3_available:
        return {"error": "EV3 no disponible", "recommendations": []}
    try:
        analyzer_module = bridge.get_analyzer()
        recommendations_module = bridge.get_recommendations()
        if analyzer_module is None or recommendations_module is None:
            return {"error": "Módulos EV3 no disponibles", "recommendations": []}

        analysis = analyzer_module.analyze_traces()  # CAMBIO
        recs = recommendations_module.generate_recommendations(analysis)  # CAMBIO
        return {"status": "ok", "recommendations": recs}
    except Exception as e:
        return {"error": str(e), "recommendations": []}


def get_ev3_security_check(message: str):
    if not bridge.ev3_available:
        return {"safe": True, "reason": "EV3 no disponible, sin filtro activo"}
    try:
        security_mod = bridge.get_security()
        if security_mod is None:
            return {"safe": True, "reason": "Módulo seguridad no disponible"}

        result = security_mod.validate_input(message)

        return {
            "safe": result.allowed,
            "reason": result.reason,
            "category": result.category,
            "safe_response": result.safe_response,
        }
    except Exception as e:
        return {"error": str(e), "safe": True}
