import os
from pathlib import Path

from playwright.sync_api import sync_playwright


def main():
    base_url = os.environ.get("GRAFANA_URL", "http://127.0.0.1:3000").rstrip("/")
    output = Path("artifacts/grafana-dashboard.png")
    output.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 1200})

        page.goto(f"{base_url}/login")
        page.locator('input[name="user"]').fill(os.environ["GRAFANA_USER"])
        page.locator('input[name="password"]').fill(os.environ["GRAFANA_PASSWORD"])
        page.get_by_role("button", name="Log in").click()
        page.wait_for_url(lambda url: "/login" not in url, timeout=30_000)

        page.goto(
            f"{base_url}/d/gmcomponentes-devops/gm-components-devops-ep3"
            "?from=now-5m&to=now&kiosk"
        )

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