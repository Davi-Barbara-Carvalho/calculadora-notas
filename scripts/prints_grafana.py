"""Tira prints (PNG) dos dashboards do Grafana, dos alvos do Prometheus e do Mailpit.

Usado no CI (os prints ficam nos artefatos do workflow), mas também roda
na sua máquina com a stack no ar:

    pip install playwright && python -m playwright install chromium
    python scripts/prints_grafana.py --saida prints/

Os endereços padrão são os do Docker Compose (ou dos port-forwards do README).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright

DASHBOARDS = ["calculadora-api", "calculadora-containers"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--grafana", default="http://localhost:3000")
    parser.add_argument("--prometheus", default="http://localhost:9090")
    parser.add_argument("--mailpit", default="http://localhost:8025")
    parser.add_argument("--usuario", default="admin")
    parser.add_argument("--senha", default="admin")
    parser.add_argument("--dashboards", nargs="*", default=DASHBOARDS)
    parser.add_argument("--intervalo", default="now-15m", help="início do período dos gráficos")
    parser.add_argument("--prefixo", default="", help="prefixo dos nomes dos arquivos")
    parser.add_argument("--saida", default="prints")
    parser.add_argument(
        "--terminal", nargs="*", default=[],
        help="arquivos .txt (ex.: saída do kubectl get) para virar print de terminal",
    )
    args = parser.parse_args()

    saida = Path(args.saida)
    saida.mkdir(parents=True, exist_ok=True)

    def salvar(pagina, nome: str) -> None:
        arquivo = saida / f"{args.prefixo}{nome}.png"
        pagina.screenshot(path=str(arquivo), full_page=True)
        print(f"print salvo: {arquivo}", flush=True)

    with sync_playwright() as p:
        navegador = p.chromium.launch()
        pagina = navegador.new_page(viewport={"width": 1600, "height": 1000}, device_scale_factor=1)

        # Login no Grafana.
        pagina.goto(f"{args.grafana}/login")
        pagina.fill("input[name='user']", args.usuario)
        pagina.fill("input[name='password']", args.senha)
        pagina.click("button[type='submit']")
        pagina.wait_for_load_state("networkidle")
        # Primeiro login com admin/admin: o Grafana pede para trocar a senha.
        if "/login" in pagina.url:
            try:
                pagina.get_by_role("button", name="Skip").click(timeout=3000)
            except Exception:  # noqa: BLE001
                pass

        for uid in args.dashboards:
            pagina.goto(f"{args.grafana}/d/{uid}?orgId=1&from={args.intervalo}&to=now&kiosk")
            pagina.wait_for_load_state("networkidle")
            pagina.wait_for_timeout(4000)  # tempo para os gráficos desenharem
            # Rola até o fim para carregar os painéis "lazy" e volta ao topo.
            pagina.mouse.wheel(0, 20000)
            pagina.wait_for_timeout(3000)
            pagina.mouse.wheel(0, -20000)
            pagina.set_viewport_size({"width": 1600, "height": 2600})
            pagina.wait_for_timeout(3000)
            salvar(pagina, f"grafana-{uid}")
            pagina.set_viewport_size({"width": 1600, "height": 1000})

        pagina.goto(f"{args.grafana}/alerting/list?view=list")
        pagina.wait_for_load_state("networkidle")
        pagina.wait_for_timeout(3000)
        salvar(pagina, "grafana-alertas")

        for nome, url in [
            ("prometheus-alvos", f"{args.prometheus}/targets"),
            ("mailpit-alertas", f"{args.mailpit}/"),
        ]:
            try:
                pagina.goto(url, timeout=15000)
                pagina.wait_for_load_state("networkidle")
                pagina.wait_for_timeout(2000)
                salvar(pagina, nome)
            except Exception as erro:  # noqa: BLE001
                print(f"sem print de {nome}: {erro}", flush=True)

        # Saídas de terminal (kubectl get...) viram imagem com cara de terminal.
        for arquivo in args.terminal:
            texto = Path(arquivo).read_text(encoding="utf-8")
            pagina.set_viewport_size({"width": 1900, "height": 600})
            pagina.set_content(
                "<body style='margin:0;background:#1e1e1e'>"
                "<pre style='margin:0;padding:20px;color:#d4d4d4;font:13px/1.45 monospace;"
                "white-space:pre'></pre></body>"
            )
            pagina.eval_on_selector("pre", "(el, t) => { el.textContent = t; }", texto)
            largura = pagina.eval_on_selector("pre", "el => el.scrollWidth")
            pagina.set_viewport_size({"width": max(800, largura), "height": 600})
            salvar(pagina, f"terminal-{Path(arquivo).stem}")

        navegador.close()


if __name__ == "__main__":
    main()
