"""API HTTP da Calculadora de Notas.

Salva cada boletim calculado no PostgreSQL e guarda o histórico em cache
no Redis. As conexões vêm das variáveis de ambiente DATABASE_URL e
REDIS_URL (definidas no docker-compose.yml).

Rodando: gunicorn --bind 0.0.0.0:8000 "calculadora.api:create_app()"
"""

from __future__ import annotations

import json
import os

import psycopg
import redis
from flask import Flask, jsonify, request

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

    @app.get("/health")
    def health():
        with conectar() as conn:
            conn.execute("SELECT 1")
        cache.ping()
        return jsonify(status="ok", banco="ok", cache="ok")

    @app.post("/boletins")
    def criar_boletim():
        dados = request.get_json(silent=True) or {}
        notas = dados.get("notas")

        if not isinstance(notas, list):
            return jsonify(erro="Envie 'notas' como uma lista de números."), 400

        try:
            resultado = boletim(dados.get("aluno") or "", notas)
        except (NotaInvalidaError, ValueError) as erro:
            return jsonify(erro=str(erro)), 400

        with conectar() as conn:
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

        # O histórico mudou: o cache antigo não vale mais.
        cache.delete(CHAVE_HISTORICO)
        return jsonify(id=id_, **resultado), 201

    @app.get("/boletins")
    def listar_boletins():
        em_cache = cache.get(CHAVE_HISTORICO)
        if em_cache is not None:
            return app.response_class(
                em_cache, mimetype="application/json", headers={"X-Cache": "HIT"}
            )

        with conectar() as conn:
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
