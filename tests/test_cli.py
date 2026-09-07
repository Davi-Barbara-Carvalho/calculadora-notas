"""Testes da interface de linha de comando."""

import pytest

from calculadora.cli import main


def test_saida_com_notas_validas(capsys):
    codigo = main(["--aluno", "Ana", "--notas", "8", "9", "10"])
    saida = capsys.readouterr().out

    assert codigo == 0
    assert "Ana" in saida
    assert "9.0" in saida
    assert "Aprovado" in saida


def test_retorna_erro_com_nota_invalida(capsys):
    codigo = main(["--aluno", "Ana", "--notas", "11"])
    erro = capsys.readouterr().err

    assert codigo == 1
    assert "Erro" in erro


def test_nome_vazio_retorna_erro():
    assert main(["--aluno", "  ", "--notas", "7"]) == 1


def test_argumentos_obrigatorios():
    with pytest.raises(SystemExit):
        main(["--notas", "7"])
