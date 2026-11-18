"""Métricas Prometheus da API da Calculadora de Notas.

As métricas ficam no nível do módulo (são registradas uma única vez) e são
expostas em GET /metrics no formato texto do Prometheus.

O Gunicorn roda vários *workers* (processos). Cada um teria seus próprios
contadores, e o Prometheus veria um valor diferente a cada coleta. Por isso,
quando a variável PROMETHEUS_MULTIPROC_DIR está definida, o prometheus_client
grava os valores de todos os workers em arquivos nessa pasta e o /metrics
soma tudo (modo "multiprocess"). Veja calculadora/gunicorn_conf.py.
"""

from __future__ import annotations

import os

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    REGISTRY,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

from calculadora import __version__

# --- Métricas HTTP (padrão RED: Rate, Errors, Duration) ----------------------

REQUISICOES = Counter(
    "calculadora_http_requests_total",
    "Total de requisições HTTP recebidas pela API.",
    ["metodo", "endpoint", "status"],
)

DURACAO = Histogram(
    "calculadora_http_request_duration_seconds",
    "Tempo de resposta das requisições HTTP, em segundos.",
    ["metodo", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5),
)

EM_ANDAMENTO = Gauge(
    "calculadora_http_requests_in_progress",
    "Requisições sendo processadas neste momento.",
    multiprocess_mode="livesum",
)

# --- Métricas de negócio -------------------------------------------------------

BOLETINS = Counter(
    "calculadora_boletins_total",
    "Boletins calculados e gravados no banco, por situação do aluno.",
    ["situacao"],
)

MEDIAS = Histogram(
    "calculadora_boletim_media",
    "Distribuição das médias calculadas.",
    buckets=(1, 2, 3, 4, 5, 6, 7, 8, 9, 10),
)

NOTAS_INVALIDAS = Counter(
    "calculadora_notas_invalidas_total",
    "Requisições rejeitadas por dados inválidos (HTTP 400).",
)

# --- Cache e banco ------------------------------------------------------------

CACHE = Counter(
    "calculadora_cache_requests_total",
    "Consultas ao cache do histórico (resultado = hit ou miss).",
    ["resultado"],
)

DURACAO_BANCO = Histogram(
    "calculadora_db_query_duration_seconds",
    "Tempo das consultas ao PostgreSQL, em segundos.",
    ["operacao"],
    buckets=(0.001, 0.0025, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1),
)

# --- Informações da aplicação -------------------------------------------------

INFO = Gauge(
    "calculadora_app_info",
    "Versão da aplicação em execução (valor sempre 1).",
    ["versao"],
    multiprocess_mode="max",
)
INFO.labels(versao=__version__).set(1)


def gerar_metricas() -> tuple[bytes, str]:
    """Retorna o corpo e o Content-Type da resposta de GET /metrics."""
    if os.environ.get("PROMETHEUS_MULTIPROC_DIR"):
        from prometheus_client import multiprocess

        registro = CollectorRegistry()
        multiprocess.MultiProcessCollector(registro)
    else:
        registro = REGISTRY
    return generate_latest(registro), CONTENT_TYPE_LATEST
