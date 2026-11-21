"""
prom_metrics.py - Métricas en formato Prometheus para el servicio del agente.

Es independiente de ev3_observability/metrics.py (que mide la calidad de los
agentes de IA). Este módulo mide el comportamiento HTTP del servicio:
peticiones, latencia y errores, para que Prometheus las recolecte.
"""

import time

from fastapi import Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total de peticiones HTTP recibidas",
    ["method", "route", "status_code"],
)

HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "Duración de las peticiones HTTP en segundos",
    ["method", "route", "status_code"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)


def _route_label(request: Request) -> str:
    # Se usa la plantilla de la ruta (ej. /agent/session/{session_id}) y no la
    # URL real, para no generar una serie nueva por cada sesión. Las rutas
    # inexistentes se agrupan en una sola etiqueta.
    route = request.scope.get("route")
    return getattr(route, "path", "sin_ruta")


async def metrics_middleware(request: Request, call_next):
    start = time.perf_counter()
    status_code = 500  # si la petición revienta, se cuenta como error 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        labels = {
            "method": request.method,
            "route": _route_label(request),
            "status_code": str(status_code),
        }
        HTTP_REQUESTS_TOTAL.labels(**labels).inc()
        HTTP_REQUEST_DURATION.labels(**labels).observe(time.perf_counter() - start)


def metrics_endpoint() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)