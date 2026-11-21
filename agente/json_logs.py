"""
json_logs.py - Logs estructurados en JSON para el servicio del agente.

Cada petición escribe una línea JSON por stdout con un request_id. Si groq-proxy
envía el encabezado X-Request-ID, se reutiliza el mismo id, así una consulta se
puede seguir de un servicio al otro (Alloy recoge stdout y lo manda a Loki).
"""

import json
import re
import sys
import time
import uuid
from datetime import datetime, timezone

from fastapi import Request

SERVICE = "agente"

# Rutas que Prometheus y las probes de salud consultan todo el tiempo.
# No se registran en el log para no llenar Loki de ruido.
RUTAS_SILENCIADAS = {"/metrics", "/health"}

_ID_VALIDO = re.compile(r"^[A-Za-z0-9._-]{8,64}$")


def _escribir(level: str, message: str, **fields) -> None:
    linea = {
        "timestamp": datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z"),
        "level": level,
        "service": SERVICE,
        "message": message,
        **fields,
    }
    sys.stdout.write(json.dumps(linea, ensure_ascii=False) + "\n")
    sys.stdout.flush()


class _Logger:
    def info(self, message: str, **fields) -> None:
        _escribir("info", message, **fields)

    def warn(self, message: str, **fields) -> None:
        _escribir("warn", message, **fields)

    def error(self, message: str, **fields) -> None:
        _escribir("error", message, **fields)


logger = _Logger()


def _obtener_request_id(request: Request) -> str:
    entrante = request.headers.get("x-request-id", "")
    # Solo se acepta un id con formato razonable, para no copiar al log texto arbitrario
    if _ID_VALIDO.match(entrante):
        return entrante
    return str(uuid.uuid4())


def _route_label(request: Request) -> str:
    route = request.scope.get("route")
    return getattr(route, "path", "sin_ruta")


async def request_log_middleware(request: Request, call_next):
    request_id = _obtener_request_id(request)
    request.state.request_id = request_id
    inicio = time.perf_counter()
    status_code = 500  # si la petición revienta, se registra como error 500

    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception as error:
        logger.error(
            "unhandled_exception",
            request_id=request_id,
            route=_route_label(request),
            error=str(error),
        )
        raise
    finally:
        if request.url.path not in RUTAS_SILENCIADAS:
            duracion_ms = round((time.perf_counter() - inicio) * 1000, 2)
            nivel = "error" if status_code >= 500 else "warn" if status_code >= 400 else "info"
            _escribir(
                nivel,
                "http_request",
                request_id=request_id,
                method=request.method,
                route=_route_label(request),
                status_code=status_code,
                duration_ms=duracion_ms,
            )