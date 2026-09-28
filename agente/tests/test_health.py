from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_health_responde_200():
    response = client.get("/health")
    assert response.status_code == 200


def test_ruta_inexistente_devuelve_404():
    response = client.get("/ruta-que-no-existe")
    assert response.status_code == 404