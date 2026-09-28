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

```bash
docker compose up --build                                          # roda o exemplo padrão
docker compose run --rm calculadora --aluno "João" --notas 5 6 4   # com outros argumentos
docker compose --profile test run --rm testes                      # roda os testes
```

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

Depois disso, o job **Imagem Docker**:

1. Faz o build da imagem de testes e roda o `pytest` dentro do container
2. Faz o build da imagem final e executa um teste de fumaça
3. Em push na `main`, publica a imagem no GHCR (tags `latest` e SHA do commit)

## Estrutura do projeto

```
calculadora-notas/
├── .github/workflows/ci.yml
├── .dockerignore
├── Dockerfile
├── docker-compose.yml
├── src/calculadora/
│   ├── __init__.py
│   ├── cli.py
│   └── operacoes.py
├── tests/
│   ├── test_cli.py
│   └── test_operacoes.py
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Licença

MIT
