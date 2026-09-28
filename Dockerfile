# syntax=docker/dockerfile:1
# Ativa a sintaxe mais recente do Dockerfile (BuildKit).

# Versão do Python em um só lugar: dá para trocar com
#   docker build --build-arg PYTHON_VERSION=3.11 .
ARG PYTHON_VERSION=3.12

# ---------------------------------------------------------------------------
# Estágio 1: build - gera o pacote (wheel) do projeto
# Tudo o que é usado só para empacotar (a ferramenta "build", o código-fonte)
# fica neste estágio e NÃO vai para a imagem final.
# ---------------------------------------------------------------------------
# Imagem "slim": Debian mínimo com Python, bem menor que a imagem
# padrão python:3.12, que traz compiladores e ferramentas que não usamos.
FROM python:${PYTHON_VERSION}-slim AS build

WORKDIR /app

# Instala a ferramenta de build ANTES de copiar o código: esta camada
# fica em cache e não é refeita quando só o código muda.
# --no-cache-dir: não guarda o cache do pip dentro da imagem.
RUN pip install --no-cache-dir build==1.2.2

# Copia só o necessário para empacotar (o .dockerignore bloqueia o resto).
COPY pyproject.toml README.md ./
COPY src ./src

# Gera o arquivo .whl em /dist, que será copiado para o estágio final.
RUN python -m build --wheel --outdir /dist

# ---------------------------------------------------------------------------
# Estágio 2: test - roda os testes dentro do container
# Uso: docker build --target test -t calculadora-notas:test .
# Não faz parte da imagem final: é usado no CI e para validar a aplicação.
# ---------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim AS test

WORKDIR /app

# Dependências primeiro (mudam pouco) -> camada reaproveitada do cache.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Código e testes por último (mudam muito) -> só estas camadas são refeitas.
COPY pyproject.toml README.md ./
COPY src ./src
COPY tests ./tests

# Comando padrão: roda o pytest com relatório de cobertura.
CMD ["pytest", "--cov=src/calculadora", "--cov-report=term-missing"]

# ---------------------------------------------------------------------------
# Estágio 3: runtime - imagem final, enxuta, só com o pacote instalado
# É o último estágio, então é o que "docker build ." gera por padrão.
# ---------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim AS runtime

# Metadados padrão OCI (aparecem no GitHub Container Registry).
LABEL org.opencontainers.image.title="calculadora-notas" \
      org.opencontainers.image.description="Calcula médias escolares e informa a situação do aluno" \
      org.opencontainers.image.source="https://github.com/Davi-Barbara-Carvalho/calculadora-notas" \
      org.opencontainers.image.licenses="MIT"

# PYTHONDONTWRITEBYTECODE: não cria arquivos .pyc (menos lixo no container).
# PYTHONUNBUFFERED: a saída aparece na hora no "docker logs".
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Traz do estágio "build" APENAS o .whl pronto. Instala e apaga o arquivo
# no mesmo RUN, para ele não ficar guardado em nenhuma camada.
COPY --from=build /dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm -f /tmp/*.whl

# Segurança: cria um usuário comum e roda o app com ele, não como root.
RUN useradd --create-home --uid 1000 appuser
USER appuser
WORKDIR /home/appuser

# ENTRYPOINT fixa o executável; CMD é o argumento padrão (mostra a ajuda).
# Assim: docker run calculadora-notas --aluno "Maria" --notas 8 7.5 9
ENTRYPOINT ["calculadora"]
CMD ["--help"]
