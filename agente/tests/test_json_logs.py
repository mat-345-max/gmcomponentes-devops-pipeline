import json

from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def _registros_http(capsys):
    salida = capsys.readouterr().out
    registros = []
    for linea in salida.splitlines():
        try:
            dato = json.loads(linea)
        except ValueError:
            continue
        if dato.get("message") == "http_request":
            registros.append(dato)
    return registros


def test_genera_request_id_y_lo_escribe_en_el_log(capsys):
    response = client.get("/ruta-que-no-existe")
    request_id = response.headers["x-request-id"]
    assert request_id

    registro = _registros_http(capsys)[0]
    assert registro["level"] == "warn"
    assert registro["service"] == "agente"
    assert registro["request_id"] == request_id
    assert registro["method"] == "GET"
    assert registro["route"] == "sin_ruta"
    assert registro["status_code"] == 404
    assert isinstance(registro["duration_ms"], float)


def test_respeta_el_request_id_que_llega_de_groq_proxy(capsys):
    response = client.get(
        "/ruta-que-no-existe", headers={"X-Request-ID": "abc-12345678"}
    )
    assert response.headers["x-request-id"] == "abc-12345678"
    assert _registros_http(capsys)[0]["request_id"] == "abc-12345678"


def test_descarta_un_request_id_invalido(capsys):
    response = client.get(
        "/ruta-que-no-existe", headers={"X-Request-ID": "mal formato!!"}
    )
    assert response.headers["x-request-id"] != "mal formato!!"


def test_no_registra_health_ni_metrics(capsys):
    client.get("/health")
    client.get("/metrics")
    assert _registros_http(capsys) == []