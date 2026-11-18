"""Confere se o monitoramento está funcionando (usado no CI, serve para testar à mão).

    python scripts/verificar_monitoramento.py \
        --prometheus http://localhost:9090 --grafana http://localhost:3000

    # teste de ponta a ponta do alerta (depois de derrubar a API):
    python scripts/verificar_monitoramento.py --mailpit http://localhost:8025 \
        --esperar-alerta "API fora do ar"

Só usa a biblioteca padrão do Python.
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
import time
import urllib.request

JOBS = ["prometheus", "calculadora-api", "postgres", "redis", "cadvisor"]
DASHBOARDS = ["calculadora-api", "calculadora-containers"]
ALERTAS = 7


def get_json(url: str, usuario: str | None = None, senha: str | None = None):
    req = urllib.request.Request(url)
    if usuario:
        token = base64.b64encode(f"{usuario}:{senha}".encode()).decode()
        req.add_header("Authorization", f"Basic {token}")
    with urllib.request.urlopen(req, timeout=10) as resposta:
        return json.load(resposta)


def tentar(descricao: str, verificacao, timeout: int) -> None:
    """Repete a verificação até dar certo ou estourar o tempo."""
    limite = time.time() + timeout
    ultimo_erro = None
    while time.time() < limite:
        try:
            resultado = verificacao()
            print(f"OK   {descricao}: {resultado}", flush=True)
            return
        except Exception as erro:  # noqa: BLE001 - mostra qualquer falha
            ultimo_erro = erro
            time.sleep(5)
    print(f"FALHA {descricao}: {ultimo_erro}", flush=True)
    sys.exit(1)


def verificar_prometheus(base: str, jobs: list[str], timeout: int) -> None:
    def alvos_no_ar():
        alvos = get_json(f"{base}/api/v1/targets?state=active")["data"]["activeTargets"]
        saude: dict[str, list[str]] = {}
        for alvo in alvos:
            saude.setdefault(alvo["labels"]["job"], []).append(alvo["health"])
        faltando = [j for j in jobs if j not in saude]
        fora = {j: h for j, h in saude.items() if j in jobs and "up" not in h}
        if faltando or fora:
            raise RuntimeError(f"faltando={faltando} fora={fora}")
        return {j: saude[j] for j in jobs}

    tentar("Prometheus: alvos coletados", alvos_no_ar, timeout)

    def metrica_da_api():
        dados = get_json(f"{base}/api/v1/query?query=sum(calculadora_http_requests_total)")
        resultado = dados["data"]["result"]
        if not resultado:
            raise RuntimeError("calculadora_http_requests_total ainda não apareceu")
        return f"{resultado[0]['value'][1]} requisições"

    tentar("Prometheus: métricas da API", metrica_da_api, timeout)


def verificar_grafana(base: str, usuario: str, senha: str, dashboards: list[str], timeout: int) -> None:
    def fonte_de_dados():
        dados = get_json(f"{base}/api/datasources/uid/prometheus/health", usuario, senha)
        if dados.get("status") != "OK":
            raise RuntimeError(dados)
        return dados["message"]

    tentar("Grafana: fonte de dados Prometheus", fonte_de_dados, timeout)

    def paineis():
        achados = {d["uid"] for d in get_json(f"{base}/api/search?type=dash-db", usuario, senha)}
        faltando = [d for d in dashboards if d not in achados]
        if faltando:
            raise RuntimeError(f"dashboards faltando: {faltando}")
        return sorted(achados)

    tentar("Grafana: dashboards provisionados", paineis, timeout)

    def regras():
        dados = get_json(f"{base}/api/v1/provisioning/alert-rules", usuario, senha)
        if len(dados) < ALERTAS:
            raise RuntimeError(f"só {len(dados)} regras")
        return [r["title"] for r in dados]

    tentar("Grafana: regras de alerta", regras, timeout)

    def ponto_de_contato():
        dados = get_json(f"{base}/api/v1/provisioning/contact-points", usuario, senha)
        nomes = [c["name"] for c in dados]
        if "email-equipe" not in nomes:
            raise RuntimeError(nomes)
        return nomes

    tentar("Grafana: ponto de contato", ponto_de_contato, timeout)


def esperar_alerta(base: str, texto: str, timeout: int) -> None:
    def email_recebido():
        mensagens = get_json(f"{base}/api/v1/messages")["messages"]
        assuntos = [m["Subject"] for m in mensagens]
        if not any(texto in a for a in assuntos):
            raise RuntimeError(f"assuntos recebidos: {assuntos}")
        return [a for a in assuntos if texto in a]

    tentar(f"Mailpit: e-mail de alerta '{texto}'", email_recebido, timeout)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--prometheus")
    parser.add_argument("--jobs", nargs="*", default=JOBS)
    parser.add_argument("--grafana")
    parser.add_argument("--dashboards", nargs="*", default=DASHBOARDS)
    parser.add_argument("--usuario", default="admin")
    parser.add_argument("--senha", default="admin")
    parser.add_argument("--mailpit")
    parser.add_argument("--esperar-alerta")
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()

    if args.prometheus:
        verificar_prometheus(args.prometheus.rstrip("/"), args.jobs, args.timeout)
    if args.grafana:
        verificar_grafana(args.grafana.rstrip("/"), args.usuario, args.senha, args.dashboards, args.timeout)
    if args.mailpit and args.esperar_alerta:
        esperar_alerta(args.mailpit.rstrip("/"), args.esperar_alerta, args.timeout)


if __name__ == "__main__":
    main()
