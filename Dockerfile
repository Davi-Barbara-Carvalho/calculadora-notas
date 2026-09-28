# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.12

# ---------------------------------------------------------------------------
# Estágio 1: build - gera o pacote (wheel) do projeto
# ---------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim AS build

WORKDIR /app

RUN pip install --no-cache-dir build==1.2.2

COPY pyproject.toml README.md ./
COPY src ./src

RUN python -m build --wheel --outdir /dist

# ---------------------------------------------------------------------------
# Estágio 2: test - roda os testes dentro do container
# Uso: docker build --target test -t calculadora-notas:test .
# ---------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim AS test

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY pyproject.toml README.md ./
COPY src ./src
COPY tests ./tests

CMD ["pytest", "--cov=src/calculadora", "--cov-report=term-missing"]

# ---------------------------------------------------------------------------
# Estágio 3: runtime - imagem final, enxuta, só com o pacote instalado
# ---------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim AS runtime

LABEL org.opencontainers.image.title="calculadora-notas" \
      org.opencontainers.image.description="Calcula médias escolares e informa a situação do aluno" \
      org.opencontainers.image.source="https://github.com/Davi-Barbara-Carvalho/calculadora-notas" \
      org.opencontainers.image.licenses="MIT"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY --from=build /dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm -f /tmp/*.whl

# Executa como usuário sem privilégios
RUN useradd --create-home --uid 1000 appuser
USER appuser
WORKDIR /home/appuser

ENTRYPOINT ["calculadora"]
CMD ["--help"]
