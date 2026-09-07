"""Interface de linha de comando da Calculadora de Notas."""

from __future__ import annotations

import argparse
import sys

from calculadora.operacoes import NotaInvalidaError, boletim


def montar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="calculadora",
        description="Calcula a média e a situação de um aluno.",
    )
    parser.add_argument("--aluno", required=True, help="Nome do aluno")
    parser.add_argument(
        "--notas",
        required=True,
        nargs="+",
        type=float,
        help="Notas do aluno separadas por espaço (ex: --notas 8 7.5 9)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = montar_parser().parse_args(argv)

    try:
        resultado = boletim(args.aluno, args.notas)
    except (NotaInvalidaError, ValueError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 1

    print(f"Aluno:    {resultado['aluno']}")
    print(f"Notas:    {', '.join(str(nota) for nota in resultado['notas'])}")
    print(f"Média:    {resultado['media']}")
    print(f"Situação: {resultado['situacao']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
