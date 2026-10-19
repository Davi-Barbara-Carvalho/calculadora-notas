# Calculadora de Notas

[![CI](https://github.com/Davi-Barbara-Carvalho/calculadora-notas/actions/workflows/ci.yml/badge.svg)](https://github.com/Davi-Barbara-Carvalho/calculadora-notas/actions/workflows/ci.yml)

Aplicação simples em Python que calcula médias escolares e informa a situação do aluno.
O projeto foi criado para praticar testes unitários e integração contínua com GitHub Actions.


## Funcionalidades

- Validação de notas (precisa ser um número entre 0 e 10)
- Média aritmética e média ponderada
- Situação do aluno: Aprovado (>= 7), Recuperação (>= 5) ou Reprovado
- Cálculo da nota necessária na última avaliação para ser aprovado
- Boletim resumido do aluno
- Interface de linha de comando

## Instalação

```bash
git clone https://github.com/Davi-Barbara-Carvalho/calculadora-notas.git
cd calculadora-notas

python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

pip install -r requirements.txt
pip install -e .
```

## Uso

```bash
calculadora --aluno "Maria" --notas 8 7.5 9
```

Saída:

```
Aluno:    Maria
Notas:    8.0, 7.5, 9.0
Média:    8.17
Situação: Aprovado
```

Também é possível usar o pacote diretamente:

```python
from calculadora import boletim

boletim("Maria", [8, 7.5, 9])
# {'aluno': 'Maria', 'notas': [8.0, 7.5, 9.0], 'media': 8.17, 'situacao': 'Aprovado'}
```

## Testes

```bash
pytest                                  # roda todos os testes
pytest --cov=src/calculadora            # com relatório de cobertura
```

## Docker

O projeto tem um `Dockerfile` multi-stage com três estágios:

| Estágio   | Para que serve                                             |
|-----------|------------------------------------------------------------|
| `build`   | Gera o pacote (wheel) com `python -m build`                |
| `test`    | Instala as dependências de teste e roda o `pytest`         |
| `runtime` | Imagem final enxuta, com o pacote instalado e usuário sem privilégios |

### Rodando a calculadora

```bash
docker build -t calculadora-notas .
docker run --rm calculadora-notas --aluno "Maria" --notas 8 7.5 9
```

### Rodando os testes no container

```bash
docker build --target test -t calculadora-notas:test .
docker run --rm calculadora-notas:test
```


### Com Docker Compose

O `docker-compose.yml` usa a imagem do projeto e sobe uma stack completa:

| Serviço       | Imagem                                    | Função                                                  | Rede                 | Volume       |
|---------------|-------------------------------------------|---------------------------------------------------------|----------------------|--------------|
| `api`         | `ghcr.io/davi-barbara-carvalho/calculadora-notas` | API HTTP (Gunicorn + Flask) na porta 8000         | `frontend`, `backend`| -            |
| `db`          | `postgres:16-alpine`                      | Guarda o histórico de boletins                          | `backend`            | `pgdata`     |
| `cache`       | `redis:7-alpine`                          | Cache da listagem `GET /boletins`                       | `backend`            | `redisdata`  |
| `calculadora` | `ghcr.io/davi-barbara-carvalho/calculadora-notas` | CLI da atividade anterior (profile `cli`)         | nenhuma              | -            |

- **Redes:** `frontend` publica a porta da API; `backend` é `internal`, então banco e cache não ficam expostos.
- **Volumes:** `pgdata` e `redisdata` mantêm os dados entre um `down` e um `up` (só `down -v` apaga).
- **Reinício:** `restart: unless-stopped` em `api`, `db` e `cache`; a CLI usa `restart: "no"`.
- **Healthchecks:** a API só sobe depois de banco e cache saudáveis (`depends_on: condition: service_healthy`).

```bash
docker compose up -d --build --wait                                # sobe a stack
docker compose ps                                                  # status
curl -X POST localhost:8000/boletins -H 'Content-Type: application/json' \
     -d '{"aluno": "Maria", "notas": [8, 7.5, 9]}'                 # cria um boletim
curl -i localhost:8000/boletins                                    # histórico (X-Cache: MISS/HIT)
docker compose run --rm calculadora --aluno "João" --notas 5 6 4   # CLI
docker compose down                                                # para (mantém os volumes)
```

Endpoints da API: `GET /health`, `POST /boletins`, `GET /boletins`.

### Testes automáticos com Compose

O `docker-compose.test.yml` cria um ambiente descartável (Postgres em `tmpfs` e Redis) e roda
toda a suíte, incluindo os testes de integração da API (`tests/test_api.py`):

```bash
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from testes
docker compose -f docker-compose.test.yml down -v
```

### GitHub Codespaces

O repositório tem um `.devcontainer/devcontainer.json` com Python e Docker (imagem `universal:2`). Em
**Code → Codespaces → Create codespace on main**, os comandos acima funcionam no terminal.
Ao terminar, pare o Codespace para não gastar horas: `gh codespace stop` ou, na página
github.com/codespaces, **⋯ → Stop codespace**.

### Imagem publicada

A cada push na `main`, o CI publica a imagem no GitHub Container Registry:

```bash
docker run --rm ghcr.io/davi-barbara-carvalho/calculadora-notas:latest --aluno "Maria" --notas 8 7.5 9
```

## Pipeline de CI

O workflow fica em `.github/workflows/ci.yml` e roda a cada `push` e `pull request` na branch `main`.
Ele executa, nas versões 3.10, 3.11 e 3.12 do Python:

1. Instalação das dependências (`pip install -r requirements.txt`)
2. Execução dos testes (`pytest` com cobertura)
3. Build do pacote (`python -m build`)
4. Publicação dos arquivos gerados em `dist/` como artefato

Depois disso, o job **Docker Compose**:

1. Roda os testes com `docker-compose.test.yml` (Postgres e Redis reais)
2. Sobe a stack do `docker-compose.yml` e faz testes de fumaça na API e na CLI
3. Em push na `main`, publica a imagem no GHCR (tags `latest` e SHA do commit)

## Estrutura do projeto

```
calculadora-notas/
├── .devcontainer/devcontainer.json
├── .github/workflows/ci.yml
├── .dockerignore
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── docker-compose.test.yml
├── db/init.sql
├── src/calculadora/
│   ├── __init__.py
│   ├── api.py
│   ├── cli.py
│   └── operacoes.py
├── tests/
│   ├── test_api.py
│   ├── test_cli.py
│   └── test_operacoes.py
├── pyproject.toml
├── requirements.txt
├── requirements-api.txt
└── README.md
```

## Licença

MIT
