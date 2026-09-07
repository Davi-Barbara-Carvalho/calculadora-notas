"""Calculadora de Notas - aplicação simples usada no exercício de CI/CD."""

from calculadora.operacoes import (
    NotaInvalidaError,
    boletim,
    calcular_media,
    calcular_media_ponderada,
    nota_necessaria,
    situacao,
    validar_nota,
)

__version__ = "0.1.0"

__all__ = [
    "NotaInvalidaError",
    "boletim",
    "calcular_media",
    "calcular_media_ponderada",
    "nota_necessaria",
    "situacao",
    "validar_nota",
    "__version__",
]
