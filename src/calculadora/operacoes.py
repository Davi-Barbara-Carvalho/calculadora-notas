from __future__ import annotations

from typing import Iterable

NOTA_MINIMA = 0.0
NOTA_MAXIMA = 10.0
MEDIA_APROVACAO = 7.0
MEDIA_RECUPERACAO = 5.0


class NotaInvalidaError(ValueError):
    """Lançada quando uma nota não é válida."""


def validar_nota(nota: float) -> float:
    """Valida uma nota e a devolve como float.

    A nota precisa ser um número entre 0 e 10.
    """
    if isinstance(nota, bool) or not isinstance(nota, (int, float)):
        raise NotaInvalidaError(f"A nota precisa ser um número, recebido: {nota!r}")

    if nota < NOTA_MINIMA or nota > NOTA_MAXIMA:
        raise NotaInvalidaError(
            f"A nota precisa estar entre {NOTA_MINIMA} e {NOTA_MAXIMA}, recebido: {nota}"
        )

    return float(nota)


def calcular_media(notas: Iterable[float]) -> float:
    """Calcula a média aritmética de uma lista de notas, com 2 casas decimais."""
    valores = [validar_nota(nota) for nota in notas]

    if not valores:
        raise NotaInvalidaError("A lista de notas não pode estar vazia.")

    return round(sum(valores) / len(valores), 2)


def calcular_media_ponderada(notas: Iterable[float], pesos: Iterable[float]) -> float:
    """Calcula a média ponderada das notas de acordo com os pesos informados."""
    valores = [validar_nota(nota) for nota in notas]
    lista_pesos = list(pesos)

    if len(valores) != len(lista_pesos):
        raise NotaInvalidaError("A quantidade de notas e de pesos precisa ser igual.")

    soma_pesos = sum(lista_pesos)
    if soma_pesos <= 0:
        raise NotaInvalidaError("A soma dos pesos precisa ser maior que zero.")

    total = sum(nota * peso for nota, peso in zip(valores, lista_pesos))
    return round(total / soma_pesos, 2)


def situacao(media: float) -> str:
    """Devolve a situação do aluno a partir da média."""
    media = validar_nota(media)

    if media >= MEDIA_APROVACAO:
        return "Aprovado"
    if media >= MEDIA_RECUPERACAO:
        return "Recuperação"
    return "Reprovado"


def nota_necessaria(notas: Iterable[float], total_avaliacoes: int) -> float:
    """Calcula a nota necessária na última avaliação para atingir a média de aprovação."""
    valores = [validar_nota(nota) for nota in notas]

    if total_avaliacoes <= len(valores):
        raise NotaInvalidaError(
            "O total de avaliações precisa ser maior que a quantidade de notas já lançadas."
        )

    necessaria = MEDIA_APROVACAO * total_avaliacoes - sum(valores)
    return round(max(necessaria, 0.0), 2)


def boletim(nome: str, notas: Iterable[float]) -> dict:
    """Monta um resumo com média e situação do aluno."""
    if not nome or not nome.strip():
        raise ValueError("O nome do aluno não pode ser vazio.")

    media = calcular_media(notas)

    return {
        "aluno": nome.strip(),
        "notas": [validar_nota(nota) for nota in notas],
        "media": media,
        "situacao": situacao(media),
    }
