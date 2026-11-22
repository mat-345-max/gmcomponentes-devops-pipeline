"""
ci_metrics.py - Genera métricas del CI/CD en formato Prometheus (EP3, IE3).

Toma los archivos de cobertura que exportan los jobs de pruebas
(cobertura-agente.json y cobertura-groq-proxy.json) y la duración del
despliegue en Kubernetes, y produce texto en el formato de exposición de
Prometheus. Ese texto se puede enviar a un Pushgateway para verlo en Grafana.

Solo usa la biblioteca estándar de Python, así corre en cualquier runner.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _etiqueta(valor: str) -> str:
    # Escapa los caracteres que el formato de Prometheus no admite en una etiqueta
    return str(valor).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def leer_cobertura(ruta) -> dict:
    datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
    servicio = datos.get("service")
    porcentaje = datos.get("coverage_percent")

    es_numero = isinstance(porcentaje, (int, float)) and not isinstance(porcentaje, bool)
    if not servicio or not es_numero:
        raise ValueError(f"Archivo de cobertura inválido: {ruta}")
    if not 0 <= porcentaje <= 100:
        raise ValueError(f"Cobertura fuera de rango (0-100) en {ruta}: {porcentaje}")

    return {"service": str(servicio), "coverage_percent": float(porcentaje)}


def generar_metricas(coberturas: list[dict], deploy_seconds: float | None = None) -> str:
    lineas = [
        "# HELP ci_test_coverage_percent Cobertura de pruebas por servicio, en porcentaje.",
        "# TYPE ci_test_coverage_percent gauge",
    ]
    for item in sorted(coberturas, key=lambda c: c["service"]):
        servicio = _etiqueta(item["service"])
        valor = repr(float(item["coverage_percent"]))
        lineas.append(f'ci_test_coverage_percent{{service="{servicio}"}} {valor}')

    if deploy_seconds is not None:
        if deploy_seconds < 0:
            raise ValueError("La duración del despliegue no puede ser negativa")
        lineas += [
            "# HELP ci_deploy_duration_seconds Duración del despliegue en Kubernetes, en segundos.",
            "# TYPE ci_deploy_duration_seconds gauge",
            f"ci_deploy_duration_seconds {float(deploy_seconds)!r}",
        ]

    return "\n".join(lineas) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Genera métricas del CI en formato Prometheus."
    )
    parser.add_argument(
        "--cobertura",
        nargs="+",
        required=True,
        help="Archivos JSON de cobertura (uno por servicio).",
    )
    parser.add_argument(
        "--deploy-seconds",
        type=float,
        default=None,
        help="Duración del despliegue en segundos.",
    )
    parser.add_argument(
        "--salida",
        default=None,
        help="Archivo donde escribir el resultado. Si se omite, imprime por pantalla.",
    )
    args = parser.parse_args(argv)

    try:
        coberturas = [leer_cobertura(ruta) for ruta in args.cobertura]
        texto = generar_metricas(coberturas, args.deploy_seconds)
    except (ValueError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    if args.salida:
        Path(args.salida).write_text(texto, encoding="utf-8")
    else:
        sys.stdout.write(texto)
    return 0


if __name__ == "__main__":
    sys.exit(main())