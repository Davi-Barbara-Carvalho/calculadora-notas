"""Testes unitários da Calculadora de Notas."""

import pytest

from calculadora.operacoes import (
    NotaInvalidaError,
    boletim,
    calcular_media,
    calcular_media_ponderada,
    nota_necessaria,
    situacao,
    validar_nota,
)


class TestValidarNota:
    @pytest.mark.parametrize("nota", [0, 5, 7.5, 10])
    def test_aceita_notas_dentro_do_intervalo(self, nota):
        assert validar_nota(nota) == float(nota)

    @pytest.mark.parametrize("nota", [-1, 10.1, 100])
    def test_rejeita_notas_fora_do_intervalo(self, nota):
        with pytest.raises(NotaInvalidaError):
            validar_nota(nota)

    @pytest.mark.parametrize("valor", ["oito", None, [8], True])
    def test_rejeita_valores_que_nao_sao_numeros(self, valor):
        with pytest.raises(NotaInvalidaError):
            validar_nota(valor)


class TestCalcularMedia:
    def test_media_de_varias_notas(self):
        assert calcular_media([8, 7, 9]) == 8.0

    def test_media_arredondada_para_duas_casas(self):
        assert calcular_media([7, 8, 10]) == 8.33

    def test_media_de_uma_unica_nota(self):
        assert calcular_media([6.5]) == 6.5

    def test_lista_vazia_gera_erro(self):
        with pytest.raises(NotaInvalidaError):
            calcular_media([])

    def test_nota_invalida_na_lista_gera_erro(self):
        with pytest.raises(NotaInvalidaError):
            calcular_media([8, 15])


class TestMediaPonderada:
    def test_calcula_com_pesos_diferentes(self):
        assert calcular_media_ponderada([6, 9], [1, 3]) == 8.25

    def test_pesos_iguais_equivalem_a_media_simples(self):
        assert calcular_media_ponderada([4, 8], [2, 2]) == calcular_media([4, 8])

    def test_quantidade_diferente_de_pesos_gera_erro(self):
        with pytest.raises(NotaInvalidaError):
            calcular_media_ponderada([7, 8], [1])

    def test_soma_de_pesos_zerada_gera_erro(self):
        with pytest.raises(NotaInvalidaError):
            calcular_media_ponderada([7, 8], [0, 0])


class TestSituacao:
    @pytest.mark.parametrize(
        "media, esperado",
        [
            (10, "Aprovado"),
            (7, "Aprovado"),
            (6.9, "Recuperação"),
            (5, "Recuperação"),
            (4.9, "Reprovado"),
            (0, "Reprovado"),
        ],
    )
    def test_situacao_por_faixa_de_media(self, media, esperado):
        assert situacao(media) == esperado


class TestNotaNecessaria:
    def test_calcula_nota_que_falta_para_aprovacao(self):
        # Precisa de 21 pontos no total; já tem 13 -> faltam 8
        assert nota_necessaria([6, 7], 3) == 8.0

    def test_nunca_retorna_valor_negativo(self):
        # Já tem 30 pontos e precisaria de 28 no total -> a nota necessária é 0
        assert nota_necessaria([10, 10, 10], 4) == 0.0

    def test_total_de_avaliacoes_invalido_gera_erro(self):
        with pytest.raises(NotaInvalidaError):
            nota_necessaria([8, 9], 2)


class TestBoletim:
    def test_monta_resumo_completo(self):
        resultado = boletim("Maria", [8, 9, 10])

        assert resultado["aluno"] == "Maria"
        assert resultado["media"] == 9.0
        assert resultado["situacao"] == "Aprovado"
        assert resultado["notas"] == [8.0, 9.0, 10.0]

    def test_remove_espacos_do_nome(self):
        assert boletim("  João  ", [7])["aluno"] == "João"

    @pytest.mark.parametrize("nome", ["", "   "])
    def test_nome_vazio_gera_erro(self, nome):
        with pytest.raises(ValueError):
            boletim(nome, [7])
