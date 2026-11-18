"""Configuração do Gunicorn para a API (usada no Compose e no Kubernetes).

    gunicorn -c python:calculadora.gunicorn_conf "calculadora.api:create_app()"

Prepara a pasta de métricas compartilhada entre os workers
(PROMETHEUS_MULTIPROC_DIR) e avisa o prometheus_client quando um worker morre.
"""

import os
import shutil

bind = os.environ.get("GUNICORN_BIND", "0.0.0.0:8000")
workers = int(os.environ.get("GUNICORN_WORKERS", "2"))
accesslog = "-"


def on_starting(server):
    """Antes de criar os workers: começa com a pasta de métricas vazia."""
    pasta = os.environ.get("PROMETHEUS_MULTIPROC_DIR")
    if pasta:
        shutil.rmtree(pasta, ignore_errors=True)
        os.makedirs(pasta, exist_ok=True)


def child_exit(server, worker):
    """Remove os arquivos de gauges "live" do worker que terminou."""
    if os.environ.get("PROMETHEUS_MULTIPROC_DIR"):
        from prometheus_client import multiprocess

        multiprocess.mark_process_dead(worker.pid)
