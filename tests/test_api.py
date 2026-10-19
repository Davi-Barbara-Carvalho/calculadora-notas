"""Testes de integração da API (precisam de PostgreSQL e Redis).

Rodam com: docker compose -f docker-compose.test.yml up --build \
    --abort-on-container-exit --exit-code-from testes
Sem DATABASE_URL/REDIS_URL definidos, são pulados.
"""

import os

import pytest

pytest.importorskip("flask")

if not (os.environ.get("DATABASE_URL") and os.environ.get("REDIS_URL")):
    pytest.skip("DATABASE_URL e REDIS_URL não definidos", allow_module_level=True)

import psycopg  # noqa: E402
import redis  # noqa: E402

from calculadora.api import create_app  # noqa: E402


@pytest.fixture
def cliente():
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        conn.execute("TRUNCATE boletins RESTART IDENTITY")
    redis.Redis.from_url(os.environ["REDIS_URL"]).flushdb()

    return create_app().test_client()


def test_health(cliente):
    resposta = cliente.get("/health")

    assert resposta.status_code == 200
    assert resposta.get_json() == {"status": "ok", "banco": "ok", "cache": "ok"}


def test_cria_boletim_e_salva_no_banco(cliente):
    resposta = cliente.post("/boletins", json={"aluno": "Maria", "notas": [8, 7.5, 9]})

    assert resposta.status_code == 201
    assert resposta.get_json() == {
        "id": 1,
        "aluno": "Maria",
        "notas": [8.0, 7.5, 9.0],
        "media": 8.17,
        "situacao": "Aprovado",
    }

    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        assert conn.execute("SELECT count(*) FROM boletins").fetchone() == (1,)


@pytest.mark.parametrize(
    "corpo",
    [
        {"aluno": "Ana", "notas": [11]},
        {"aluno": "Ana", "notas": "8"},
        {"aluno": "", "notas": [7]},
        {},
    ],
)
def test_rejeita_dados_invalidos(cliente, corpo):
    resposta = cliente.post("/boletins", json=corpo)

    assert resposta.status_code == 400
    assert "erro" in resposta.get_json()


def test_historico_usa_cache_e_e_invalidado(cliente):
    cliente.post("/boletins", json={"aluno": "Ana", "notas": [5, 6]})

    primeira = cliente.get("/boletins")
    segunda = cliente.get("/boletins")

    assert primeira.headers["X-Cache"] == "MISS"
    assert segunda.headers["X-Cache"] == "HIT"
    assert [b["aluno"] for b in segunda.get_json()] == ["Ana"]

    # Um novo boletim invalida o cache.
    cliente.post("/boletins", json={"aluno": "João", "notas": [3, 4]})
    terceira = cliente.get("/boletins")

    assert terceira.headers["X-Cache"] == "MISS"
    assert [b["aluno"] for b in terceira.get_json()] == ["João", "Ana"]
