import json

import pytest

from ci_metrics import generar_metricas, leer_cobertura, main


def _escribir_json(ruta, contenido):
    ruta.write_text(json.dumps(contenido), encoding="utf-8")
    return ruta


def test_genera_metricas_de_cobertura_y_duracion():
    texto = generar_metricas(
        [
            {"service": "groq-proxy", "coverage_percent": 9.92},
            {"service": "agente", "coverage_percent": 36.81},
        ],
        deploy_seconds=87,
    )
    assert 'ci_test_coverage_percent{service="agente"} 36.81' in texto
    assert 'ci_test_coverage_percent{service="groq-proxy"} 9.92' in texto
    assert "ci_deploy_duration_seconds 87.0" in texto
    assert "# TYPE ci_test_coverage_percent gauge" in texto
    assert "# TYPE ci_deploy_duration_seconds gauge" in texto
    assert texto.endswith("\n")


def test_ordena_los_servicios_por_nombre():
    texto = generar_metricas(
        [
            {"service": "groq-proxy", "coverage_percent": 1},
            {"service": "agente", "coverage_percent": 2},
        ]
    )
    assert texto.index('service="agente"') < texto.index('service="groq-proxy"')


def test_sin_duracion_no_incluye_esa_metrica():
    texto = generar_metricas([{"service": "agente", "coverage_percent": 50}])
    assert "ci_deploy_duration_seconds" not in texto


def test_rechaza_una_duracion_negativa():
    with pytest.raises(ValueError):
        generar_metricas([], deploy_seconds=-1)


def test_escapa_caracteres_especiales_en_las_etiquetas():
    texto = generar_metricas([{"service": 'a"b', "coverage_percent": 10}])
    assert 'service="a\\"b"' in texto


def test_lee_un_archivo_de_cobertura(tmp_path):
    ruta = _escribir_json(
        tmp_path / "cobertura.json", {"service": "agente", "coverage_percent": 36.81}
    )
    assert leer_cobertura(ruta) == {"service": "agente", "coverage_percent": 36.81}


@pytest.mark.parametrize(
    "contenido",
    [
        {"coverage_percent": 40},
        {"service": "agente"},
        {"service": "agente", "coverage_percent": "alto"},
        {"service": "agente", "coverage_percent": 140},
        {"service": "agente", "coverage_percent": -5},
    ],
)
def test_rechaza_archivos_de_cobertura_invalidos(tmp_path, contenido):
    ruta = _escribir_json(tmp_path / "cobertura.json", contenido)
    with pytest.raises(ValueError):
        leer_cobertura(ruta)


def test_main_escribe_el_archivo_de_salida(tmp_path):
    agente = _escribir_json(
        tmp_path / "a.json", {"service": "agente", "coverage_percent": 36.81}
    )
    proxy = _escribir_json(
        tmp_path / "g.json", {"service": "groq-proxy", "coverage_percent": 9.92}
    )
    salida = tmp_path / "metricas.prom"

    codigo = main(
        [
            "--cobertura", str(agente), str(proxy),
            "--deploy-seconds", "87",
            "--salida", str(salida),
        ]
    )

    assert codigo == 0
    contenido = salida.read_text(encoding="utf-8")
    assert 'ci_test_coverage_percent{service="agente"} 36.81' in contenido
    assert "ci_deploy_duration_seconds 87.0" in contenido


def test_main_devuelve_error_si_falta_el_archivo(tmp_path, capsys):
    codigo = main(["--cobertura", str(tmp_path / "no-existe.json")])
    assert codigo == 1
    assert "Error" in capsys.readouterr().err