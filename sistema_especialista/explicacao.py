
"""Módulo de explicação (M3).

Responsável por explicar como e por que o sistema especialista
chegou às suas conclusões, utilizando as regras acionadas
durante o processo de inferência.
"""

from __future__ import annotations

from .base_conhecimento import BaseConhecimento
from .modelos import ResultadoInferencia


def explicar_como(
    base: BaseConhecimento,
    resultado: ResultadoInferencia,
    fato: str | None = None,
) -> str:
    """Explica como o sistema chegou a uma ou mais conclusões."""

    explicacoes = []

    for disparo in resultado.disparos:
        regra = base.regra(disparo.regra_id)

        # Identifica as conclusões produzidas pelo disparo.
        conclusoes = disparo.conclusoes

        if fato is not None:
            conclusoes = tuple(
                (conclusao, cf)
                for conclusao, cf in conclusoes
                if conclusao == fato
            )

        if not conclusoes:
            continue

        explicacoes.append(
            f"Regra {regra.id} (camada {regra.camada}):"
        )

        # Recupera as condições utilizadas pela regra.
        condicoes = []

        for condicao in regra.se:
            presentes = [
                (f, resultado.memoria[f])
                for f in condicao.fatos()
                if f in resultado.memoria
            ]

            if presentes:
                usado, cf = max(presentes, key=lambda item: item[1])
                condicoes.append(
                    f"{usado} (certeza: {cf:.0%})"
                )

        if condicoes:
            explicacoes.append(
                "  Condições utilizadas: " + "; ".join(condicoes)
            )

        # Apresenta as conclusões geradas.
        for conclusao, cf in conclusoes:
            explicacoes.append(
                f"  Conclusão: {conclusao} "
                f"(fator de certeza: {cf:.0%})"
            )

        explicacoes.append("")

    if not explicacoes:
        return "Não foram encontrados disparos que sustentem essa conclusão."

    return "\n".join(explicacoes).strip()

def explicar_por_que(
    base: BaseConhecimento,
    resultado: ResultadoInferencia,
    fato: str,
) -> str:
    """Explica por que o sistema chegou a uma conclusão específica."""

    explicacoes = []

    for disparo in resultado.disparos:
        # Verifica se o disparo produziu o fato solicitado.
        conclusoes = [
            (conclusao, cf)
            for conclusao, cf in disparo.conclusoes
            if conclusao == fato
        ]

        if not conclusoes:
            continue

        regra = base.regra(disparo.regra_id)

        explicacoes.append(
            f"Regra {regra.id} (camada {regra.camada}):"
        )

        explicacoes.append(
            f"Justificativa: {regra.justificativa}"
        )

        for conclusao, cf in conclusoes:
            explicacoes.append(
                f"Conclusão: {conclusao} "
                f"(fator de certeza: {cf:.0%})"
            )

        explicacoes.append("")

    if not explicacoes:
        return (
            f"Não foi encontrada uma regra acionada "
            f"que justifique a conclusão '{fato}'."
        )

    return "\n".join(explicacoes).strip()


def explicar_resultado(
    base: BaseConhecimento,
    resultado: ResultadoInferencia,
    fato: str | None = None,
) -> str:
    """Reúne as explicações de como e por que o sistema chegou ao resultado."""

    # Identifica as conclusões produzidas durante a inferência.
    conclusoes = []

    for disparo in resultado.disparos:
        for conclusao, _ in disparo.conclusoes:
            if conclusao not in conclusoes:
                conclusoes.append(conclusao)

    # Permite explicar apenas uma conclusão específica.
    if fato is not None:
        conclusoes = [conclusao for conclusao in conclusoes if conclusao == fato]

    if not conclusoes:
        return "Não foram encontradas conclusões para explicar."

    relatorio = [
        "=" * 50,
        "           EXPLICAÇÃO DO RESULTADO",
        "=" * 50,
    ]

    for conclusao in conclusoes:
        relatorio.append("")
        relatorio.append(f"RESULTADO: {conclusao}")
        relatorio.append("-" * 50)

        # Explica como o sistema chegou à conclusão.
        relatorio.append("\n1. COMO O SISTEMA CHEGOU À CONCLUSÃO")

        explicacao_como = explicar_como(base, resultado, conclusao)
        relatorio.append(explicacao_como)

        # Explica por que a conclusão foi gerada.
        relatorio.append("\n2. POR QUE ESSA CONCLUSÃO FOI GERADA")

        explicacao_por_que = explicar_por_que(
            base,
            resultado,
            conclusao,
        )
        relatorio.append(explicacao_por_que)

        relatorio.append("")

    relatorio.append("=" * 50)
    relatorio.append("             FIM DA EXPLICAÇÃO")
    relatorio.append("=" * 50)

    return "\n".join(relatorio)
