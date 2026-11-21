
"""Fatores de certeza (cf) do sistema especialista (M5).

Um fator de certeza é um número de 0 a 1 que diz o quanto o sistema acredita num fato:
    1.0  -> certeza total (ex.: resposta dada pelo profissional de triagem)
    0.5  -> resposta "não sei"
    0.0  -> nenhuma confiança

O motor (M2) usa três fórmulas:
    1. cf_condicao:  certeza do SE de uma regra  = menor cf entre as condições
    2. cf_conclusao: certeza do ENTÃO            = cf da condição x cf da regra
    3. combinar:     duas regras, mesmo fato     = a + b x (1 - a)
"""
from __future__ import annotations

from collections.abc import Iterable


def _checar(cf: float, nome: str = "cf") -> None:
    """Garante que a certeza está entre 0 e 1. Pega erros de programação cedo."""
    if not 0.0 <= cf <= 1.0:
        raise ValueError(f"{nome} fora do intervalo [0, 1]: {cf}")


def cf_condicao(cfs: Iterable[float]) -> float:
    """Certeza do SE de uma regra: a MENOR certeza entre as condições.

    Todas as condições de uma regra precisam valer ao mesmo tempo (E lógico).
    Por isso a regra é tão confiável quanto o seu fato mais fraco:
    "a corrente arrebenta no elo mais fraco".

    Exemplo: R04 exige dor_toracica=tipica (cf 1.0) E grupo_risco=sim (cf 0.5)
             -> cf da condição = min(1.0, 0.5) = 0.5

    Lança ValueError se a lista estiver vazia ou tiver valor fora de [0, 1].
    """
    valores = list(cfs)
    if not valores:
        raise ValueError("Uma regra precisa de pelo menos uma condição.")
    for cf in valores:
        _checar(cf)
    return min(valores)


def cf_conclusao(cf_cond: float, cf_regra: float) -> float:
    """Certeza do ENTÃO: certeza da condição x certeza da regra.

    A regra em si já tem uma confiança (o especialista não tem 100% de certeza
    de que o sinal leva ao quadro). Se a condição também é incerta, as duas
    incertezas se acumulam.

    Exemplo: R05 (sinais_avc=sim -> quadro=suspeita_avc, cf 0.9),
             com resposta "não sei" (cf 0.5)
             -> 0.5 x 0.9 = 0.45
    """
    _checar(cf_cond, "cf da condição")
    _checar(cf_regra, "cf da regra")
    return cf_cond * cf_regra


def combinar(a: float, b: float) -> float:
    """Combina duas certezas para o MESMO fato concluído por regras diferentes.

    Fórmula: a + b x (1 - a)
    A segunda regra só "preenche" a parte da dúvida que a primeira deixou (1 - a).
    Assim, duas evidências reforçam a conclusão, mas o resultado nunca passa de 1.
    A ordem não importa: combinar(a, b) == combinar(b, a).

    Exemplo: R03 conclui quadro=suspeita_cardiaca com 0.8 e R04 com 0.6
             -> 0.8 + 0.6 x (1 - 0.8) = 0.92
    """
    _checar(a, "a")
    _checar(b, "b")
    return a + b * (1.0 - a)
