"""
analyzer.py - EV3 Analisis de Logs y Trazabilidad

Lee ev3_agent_traces.jsonl y calcula hallazgos:
- cantidad de ejecuciones
- errores
- bloqueos de seguridad
- latencia promedio
- intents mas frecuentes
- tools mas usadas
- trazas incompletas

Este modulo sirve para IL3.2 e IL3.4.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean
from typing import Any

from traceability import read_traces


def analyze_traces() -> dict[str, Any]:
    traces = read_traces()

    starts = [item for item in traces if item.get("event") == "agent_start"]
    ends = [item for item in traces if item.get("event") == "agent_end"]
    blocks = [item for item in traces if item.get("event") == "security_block"]

    end_by_trace = {item.get("trace_id"): item for item in ends}
    incomplete = [
        item for item in starts
        if item.get("trace_id") not in end_by_trace
    ]

    latencies = [
        float(item.get("latency_ms", 0))
        for item in ends
        if isinstance(item.get("latency_ms"), (int, float))
    ]

    precision_scores = [
        float(value)
        for item in ends
        if isinstance(value := item.get("precision_score"), (int, float))
    ]

    consistency_scores = [
        float(value)
        for item in ends
        if isinstance(value := item.get("consistency_score"), (int, float))
    ]

    errors = [
        item for item in ends
        if item.get("status") == "error" or item.get("error")
    ]

    

    intents = Counter(
        item.get("intent", "unknown")
        for item in ends
    )

    sources = Counter(
        item.get("source", "unknown")
        for item in ends
    )

    tools = Counter()
    for item in ends:
        for tool in item.get("used_tools", []) or []:
            tools[tool] += 1

    latencies_by_intent: dict[str, list[float]] = defaultdict(list)
    for item in ends:
        intent = item.get("intent", "unknown")
        latency = item.get("latency_ms")
        if isinstance(latency, (int, float)):
            latencies_by_intent[intent].append(float(latency))

    avg_latency_by_intent = {
        intent: round(mean(values), 2)
        for intent, values in latencies_by_intent.items()
        if values
    }

    return {
        "total_trace_events": len(traces),
        "total_agent_starts": len(starts),
        "total_agent_ends": len(ends),
        "total_security_blocks": len(blocks),
        "total_errors": len(errors),
        "incomplete_traces": len(incomplete),
        "avg_latency_ms": round(mean(latencies), 2) if latencies else 0.0,
        "max_latency_ms": max(latencies) if latencies else 0.0,
        "avg_precision_score": round(mean(precision_scores), 2) if precision_scores else 0.0,
        "avg_consistency_score": round(mean(consistency_scores), 2) if consistency_scores else 0.0,
        "intents": dict(intents),
        "sources": dict(sources),
        "tools": dict(tools),
        "avg_latency_by_intent": avg_latency_by_intent,
        "recent_errors": errors[-10:],
        "recent_blocks": blocks[-10:],
        "recent_traces": traces[-50:],
    }


def build_findings() -> list[str]:
    """
    Genera hallazgos tecnicos redactados desde los datos observados.
    """
    stats = analyze_traces()
    findings: list[str] = []

    if stats["total_agent_ends"] == 0 and stats["total_security_blocks"] == 0:
        return [
            "Aun no existen ejecuciones registradas para analizar. Ejecuta consultas EV3 para generar evidencia."
        ]

    if stats["total_errors"] > 0:
        findings.append(
            f"Se detectaron {stats['total_errors']} ejecuciones con error. "
            "Conviene revisar proveedores externos, timeouts y manejo de excepciones."
        )

    if stats["incomplete_traces"] > 0:
        findings.append(
            f"Existen {stats['incomplete_traces']} trazas incompletas. "
            "Esto puede indicar interrupciones durante la ejecucion del agente."
        )

    if stats["avg_latency_ms"] > 5000:
        findings.append(
            f"La latencia promedio es alta ({stats['avg_latency_ms']} ms). "
            "Se recomienda evaluar cache, reduccion de llamadas externas o timeouts diferenciados."
        )
    elif stats["avg_latency_ms"] > 0:
        findings.append(
            f"La latencia promedio observada es {stats['avg_latency_ms']} ms."
        )

    if stats["total_security_blocks"] > 0:
        findings.append(
            f"La capa de seguridad bloqueo {stats['total_security_blocks']} solicitud(es), "
            "lo que evidencia control preventivo antes de ejecutar el agente."
        )

    if stats["tools"]:
        most_used_tool = max(stats["tools"].items(), key=lambda item: item[1])
        findings.append(
            f"La tool mas usada fue {most_used_tool[0]} con {most_used_tool[1]} ejecucion(es)."
        )


    return findings
