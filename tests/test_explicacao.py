
"""Testes do módulo de explicação (M3)."""

import json
from pathlib import Path

import pytest

from sistema_especialista.base_conhecimento import carregar
from sistema_especialista.inferencia import inferir
from sistema_especialista.explicacao import (
    explicar_como,
    explicar_por_que,
    explicar_resultado,
)

CENARIOS = json.loads(
    (Path(__file__).parent / "cenarios.json").read_text(encoding="utf-8")
)


@pytest.fixture(scope="module")
def base():
    return carregar()


@pytest.fixture(scope="module")
def resultado(base):
    cenario = CENARIOS[0]
    return inferir(
        base,
        cenario["entradas"],
        cenario.get("cf_entradas"),
    )


def test_explicar_como_apresenta_regras(base, resultado):
    fato = next(iter(resultado.conclusoes))

    explicacao = explicar_como(base, resultado, fato)

    assert "Regra" in explicacao
    assert "Conclusão:" in explicacao


def test_explicar_por_que_apresenta_justificativa(base, resultado):
    fato = next(iter(resultado.conclusoes))

    explicacao = explicar_por_que(base, resultado, fato)

    assert "Justificativa:" in explicacao
    assert fato in explicacao


def test_explicar_resultado_reune_explicacoes(base, resultado):
    explicacao = explicar_resultado(base, resultado)

    assert "EXPLICAÇÃO DO RESULTADO" in explicacao
    assert "COMO O SISTEMA CHEGOU À CONCLUSÃO" in explicacao
    assert "POR QUE ESSA CONCLUSÃO FOI GERADA" in explicacao
    assert "FIM DA EXPLICAÇÃO" in explicacao


def test_explicar_resultado_filtra_fato_especifico(base, resultado):
    fato = next(iter(resultado.conclusoes))

    explicacao = explicar_resultado(base, resultado, fato)

    assert f"RESULTADO: {fato}" in explicacao


def test_explicar_resultado_sem_conclusoes(base):
    cenario = next(c for c in CENARIOS if c.get("sem_conclusao"))

    res = inferir(
        base,
        cenario["entradas"],
        cenario.get("cf_entradas"),
    )

    explicacao = explicar_resultado(base, res)

    assert explicacao == "Não foram encontradas conclusões para explicar."
