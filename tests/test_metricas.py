"""Testes da instrumentação Prometheus (não precisam de banco nem de cache).

As rotas testadas aqui não abrem conexão com o PostgreSQL nem com o Redis,
então basta passar URLs quaisquer para o create_app.
"""

import pytest

pytest.importorskip("flask")
pytest.importorskip("prometheus_client")

from prometheus_client import REGISTRY  # noqa: E402

from calculadora import __version__  # noqa: E402
from calculadora.api import create_app  # noqa: E402


def valor(nome, **labels):
    return REGISTRY.get_sample_value(nome, labels) or 0.0


@pytest.fixture
def cliente(monkeypatch):
    monkeypatch.delenv("PROMETHEUS_MULTIPROC_DIR", raising=False)
    app = create_app("postgresql://ninguem@127.0.0.1:1/nada", "redis://127.0.0.1:1/0")
    return app.test_client()


def test_metrics_no_formato_do_prometheus(cliente):
    resposta = cliente.get("/metrics")

    assert resposta.status_code == 200
    assert resposta.content_type.startswith("text/plain")
    corpo = resposta.get_data(as_text=True)
    assert "# TYPE calculadora_http_requests_total counter" in corpo
    assert f'calculadora_app_info{{versao="{__version__}"}} 1.0' in corpo


def test_conta_requisicoes_e_notas_invalidas(cliente):
    antes_400 = valor(
        "calculadora_http_requests_total", metodo="POST", endpoint="/boletins", status="400"
    )
    antes_invalidas = valor("calculadora_notas_invalidas_total")

    resposta = cliente.post("/boletins", json={"aluno": "Ana", "notas": [11]})

    assert resposta.status_code == 400
    assert valor(
        "calculadora_http_requests_total", metodo="POST", endpoint="/boletins", status="400"
    ) == antes_400 + 1
    assert valor("calculadora_notas_invalidas_total") == antes_invalidas + 1
    assert valor(
        "calculadora_http_request_duration_seconds_count", metodo="POST", endpoint="/boletins"
    ) >= 1


def test_rota_inexistente_nao_cria_serie_nova(cliente):
    antes = valor(
        "calculadora_http_requests_total", metodo="GET", endpoint="desconhecido", status="404"
    )

    cliente.get("/qualquer/coisa/123")
    cliente.get("/outra")

    assert valor(
        "calculadora_http_requests_total", metodo="GET", endpoint="desconhecido", status="404"
    ) == antes + 2


def test_erro_interno_vira_500_e_e_contado(cliente):
    # Banco inacessível: o /health falha e deve responder 500 em JSON.
    antes = valor(
        "calculadora_http_requests_total", metodo="GET", endpoint="/health", status="500"
    )

    resposta = cliente.get("/health")

    assert resposta.status_code == 500
    assert resposta.get_json()["erro"] == "Erro interno"
    assert valor(
        "calculadora_http_requests_total", metodo="GET", endpoint="/health", status="500"
    ) == antes + 1
    assert valor("calculadora_http_requests_in_progress") == 0
