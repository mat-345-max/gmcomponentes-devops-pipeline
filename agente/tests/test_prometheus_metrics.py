import re

from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_metrics_responde_en_formato_prometheus():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    assert "http_request_duration_seconds" in response.text


def test_metrics_cuenta_las_peticiones_por_ruta():
    client.get("/health")
    response = client.get("/metrics")
    patron = (
        r'http_requests_total\{[^}]*route="/health"[^}]*status_code="200"[^}]*\}\s+\d'
    )
    assert re.search(patron, response.text)


def test_metrics_agrupa_rutas_inexistentes():
    client.get("/ruta-que-no-existe")
    response = client.get("/metrics")
    assert 'route="sin_ruta"' in response.text
    assert 'status_code="404"' in response.text