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

## Pipeline de CI

O workflow fica em `.github/workflows/ci.yml` e roda a cada `push` e `pull request` na branch `main`.
Ele executa, nas versões 3.10, 3.11 e 3.12 do Python:

1. Instalação das dependências (`pip install -r requirements.txt`)
2. Execução dos testes (`pytest` com cobertura)
3. Build do pacote (`python -m build`)
4. Publicação dos arquivos gerados em `dist/` como artefato

## Estrutura do projeto

```
calculadora-notas/
├── .github/workflows/ci.yml
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
