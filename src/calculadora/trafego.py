"""Gerador de tráfego para a API, para os gráficos do Grafana terem dados.

    python -m calculadora.trafego --url http://localhost:8000 --rps 5

No Docker Compose:  docker compose --profile carga up -d trafego
No Kubernetes:      kubectl apply -f k8s/trafego.yaml

Mistura boletins aprovados, em recuperação e reprovados, alguns dados
inválidos (HTTP 400) e várias leituras do histórico (cache HIT/MISS).
Usa só a biblioteca padrão do Python.
"""

from __future__ import annotations

import argparse
import json
import random
import time
import urllib.error
import urllib.request

ALUNOS = ["Ana", "Bruno", "Carla", "Davi", "Eduarda", "Felipe", "Gabriela", "Heitor"]


def requisicao(url: str, metodo: str = "GET", corpo: dict | None = None) -> int:
    dados = json.dumps(corpo).encode() if corpo is not None else None
    req = urllib.request.Request(
        url, data=dados, method=metodo, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resposta:
            return resposta.status
    except urllib.error.HTTPError as erro:
        return erro.code
    except OSError:
        return 0  # API fora do ar


def uma_rodada(base: str) -> int:
    sorteio = random.random()
    if sorteio < 0.35:
        notas = [round(random.uniform(0, 10), 1) for _ in range(random.randint(2, 4))]
        return requisicao(
            f"{base}/boletins", "POST", {"aluno": random.choice(ALUNOS), "notas": notas}
        )
    if sorteio < 0.40:
        return requisicao(f"{base}/boletins", "POST", {"aluno": "Teste", "notas": [11]})
    if sorteio < 0.95:
        return requisicao(f"{base}/boletins")
    return requisicao(f"{base}/health")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--url", default="http://localhost:8000", help="endereço da API")
    parser.add_argument("--rps", type=float, default=5, help="requisições por segundo")
    parser.add_argument("--total", type=int, default=0, help="0 = roda para sempre")
    args = parser.parse_args(argv)

    base = args.url.rstrip("/")
    intervalo = 1 / args.rps if args.rps > 0 else 0
    feitas = 0
    contagem: dict[int, int] = {}
    print(f"Gerando tráfego em {base} ({args.rps} req/s)", flush=True)
    while args.total == 0 or feitas < args.total:
        status = uma_rodada(base)
        contagem[status] = contagem.get(status, 0) + 1
        feitas += 1
        if feitas % 100 == 0:
            print(f"{feitas} requisições, status: {contagem}", flush=True)
        time.sleep(intervalo)
    print(f"Fim: {feitas} requisições, status: {contagem}", flush=True)


if __name__ == "__main__":
    main()
