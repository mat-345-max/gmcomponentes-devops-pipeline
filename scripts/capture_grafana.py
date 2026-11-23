import os
from base64 import b64encode
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright


def main():
    base_url = os.environ.get("GRAFANA_URL", "http://127.0.0.1:3000").rstrip("/")
    output = Path("artifacts/grafana-dashboard.png")
    output.parent.mkdir(parents=True, exist_ok=True)

    user = os.environ["GRAFANA_USER"]
    password = os.environ["GRAFANA_PASSWORD"]
    credentials = b64encode(f"{user}:{password}".encode("utf-8")).decode("ascii")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 1200})

        def authorize_grafana(route):
            headers = dict(route.request.headers)
            headers["authorization"] = f"Basic {credentials}"
            route.continue_(headers=headers)

        def log_grafana_response(response):
            path = urlsplit(response.url).path
            if path == "/api/ds/query" or path.startswith("/api/datasources"):
                print(f"Grafana {response.status} {path}", flush=True)
                if response.status >= 400:
                    print(response.text()[:1500], flush=True)

        page.route(f"{base_url}/**", authorize_grafana)
        page.on("response", log_grafana_response)
        page.on(
            "pageerror",
            lambda error: print(f"Error del navegador: {error}", flush=True),
        )

        response = page.goto(
            f"{base_url}/d/gmcomponentes-devops/gm-components-devops-ep3"
            "?from=now-5m&to=now&kiosk"
        )

        if urlsplit(page.url).path.rstrip("/") == "/login":
            raise RuntimeError("Grafana redirigió al login al abrir el dashboard.")
        if response is None or not response.ok:
            status = response.status if response is not None else "sin respuesta"
            raise RuntimeError(f"Grafana no pudo abrir el dashboard: {status}")

        for title in (
            "Latencia HTTP p95 en 1 minuto",
            "Memoria por pod",
            "Cobertura de pruebas por servicio",
            "Duración del despliegue en Kubernetes",
        ):
            page.get_by_text(title, exact=True).wait_for(timeout=30_000)

        page.screenshot(path=str(output), full_page=True)
        browser.close()

    print(f"Captura guardada en {output}")


if __name__ == "__main__":
    main()