"""API HTTP da Calculadora de Notas.

Salva cada boletim calculado no PostgreSQL e guarda o histórico em cache
no Redis. As conexões vêm das variáveis de ambiente DATABASE_URL e
REDIS_URL (definidas no docker-compose.yml).

Também expõe métricas para o Prometheus em GET /metrics (ver metricas.py).

Rodando: gunicorn -c python:calculadora.gunicorn_conf "calculadora.api:create_app()"
"""

from __future__ import annotations

import json
import os
import time
from contextlib import contextmanager

import psycopg
import redis
from flask import Flask, g, jsonify, request
from werkzeug.exceptions import HTTPException

from calculadora import __version__, metricas
from calculadora.operacoes import NotaInvalidaError, boletim

CHAVE_HISTORICO = "boletins:historico"
LIMITE_HISTORICO = 50


def create_app(database_url: str | None = None, redis_url: str | None = None) -> Flask:
    app = Flask(__name__)
    app.json.ensure_ascii = False

    database_url = database_url or os.environ["DATABASE_URL"]
    cache = redis.Redis.from_url(
        redis_url or os.environ["REDIS_URL"], decode_responses=True
    )
    cache_ttl = int(os.environ.get("CACHE_TTL", "60"))

    def conectar() -> psycopg.Connection:
        return psycopg.connect(database_url)

    @contextmanager
    def medir_banco(operacao: str):
        inicio = time.perf_counter()
        try:
            yield
        finally:
            metricas.DURACAO_BANCO.labels(operacao=operacao).observe(
                time.perf_counter() - inicio
            )

    # --- Instrumentação: mede todas as requisições -------------------------

    @app.before_request
    def iniciar_medicao():
        g.inicio = time.perf_counter()
        metricas.EM_ANDAMENTO.inc()

    @app.after_request
    def registrar_metricas(resposta):
        # Usa a rota (ex.: "/boletins") e não a URL crua, para não criar
        # uma série nova a cada URL diferente (cardinalidade controlada).
        endpoint = request.url_rule.rule if request.url_rule else "desconhecido"
        if "inicio" in g:
            metricas.DURACAO.labels(request.method, endpoint).observe(
                time.perf_counter() - g.inicio
            )
            metricas.EM_ANDAMENTO.dec()
        metricas.REQUISICOES.labels(request.method, endpoint, resposta.status_code).inc()
        return resposta

    @app.errorhandler(Exception)
    def erro_interno(erro):
        # Erros HTTP normais (404, 405...) seguem como estão.
        if isinstance(erro, HTTPException):
            return erro
        app.logger.exception("Erro ao processar a requisição")
        return jsonify(erro="Erro interno", detalhe=type(erro).__name__), 500

    @app.get("/metrics")
    def metrics():
        corpo, tipo = metricas.gerar_metricas()
        return app.response_class(corpo, mimetype=None, content_type=tipo)

    @app.get("/health")
    def health():
        with medir_banco("health"), conectar() as conn:
            conn.execute("SELECT 1")
        cache.ping()
        return jsonify(status="ok", banco="ok", cache="ok", versao=__version__)

    @app.post("/boletins")
    def criar_boletim():
        dados = request.get_json(silent=True) or {}
        notas = dados.get("notas")

        if not isinstance(notas, list):
            metricas.NOTAS_INVALIDAS.inc()
            return jsonify(erro="Envie 'notas' como uma lista de números."), 400

        try:
            resultado = boletim(dados.get("aluno") or "", notas)
        except (NotaInvalidaError, ValueError) as erro:
            metricas.NOTAS_INVALIDAS.inc()
            return jsonify(erro=str(erro)), 400

        with medir_banco("insert"), conectar() as conn:
            (id_,) = conn.execute(
                "INSERT INTO boletins (aluno, notas, media, situacao)"
                " VALUES (%s, %s, %s, %s) RETURNING id",
                (
                    resultado["aluno"],
                    resultado["notas"],
                    resultado["media"],
                    resultado["situacao"],
                ),
            ).fetchone()

        metricas.BOLETINS.labels(situacao=resultado["situacao"]).inc()
        metricas.MEDIAS.observe(resultado["media"])

        # O histórico mudou: o cache antigo não vale mais.
        cache.delete(CHAVE_HISTORICO)
        return jsonify(id=id_, **resultado), 201

    @app.get("/boletins")
    def listar_boletins():
        em_cache = cache.get(CHAVE_HISTORICO)
        if em_cache is not None:
            metricas.CACHE.labels(resultado="hit").inc()
            return app.response_class(
                em_cache, mimetype="application/json", headers={"X-Cache": "HIT"}
            )

        metricas.CACHE.labels(resultado="miss").inc()
        with medir_banco("select"), conectar() as conn:
            linhas = conn.execute(
                "SELECT id, aluno, notas, media, situacao, criado_em"
                " FROM boletins ORDER BY id DESC LIMIT %s",
                (LIMITE_HISTORICO,),
            ).fetchall()

        corpo = json.dumps(
            [
                {
                    "id": id_,
                    "aluno": aluno,
                    "notas": notas,
                    "media": media,
                    "situacao": situacao,
                    "criado_em": criado_em.isoformat(),
                }
                for id_, aluno, notas, media, situacao, criado_em in linhas
            ],
            ensure_ascii=False,
        )
        cache.set(CHAVE_HISTORICO, corpo, ex=cache_ttl)
        return app.response_class(
            corpo, mimetype="application/json", headers={"X-Cache": "MISS"}
        )

    return app
