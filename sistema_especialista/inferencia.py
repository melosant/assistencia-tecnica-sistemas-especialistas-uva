"""Motor de inferência (M2): encadeamento para frente com fatores de certeza.

Fluxo de uma consulta:
    1. As respostas do cliente viram fatos de entrada "atributo=valor" (cf 1.0 ou o de cf_entradas).
    2. Para cada camada (1, 2, 3...), em ordem, cada regra é avaliada:
         - cada condição precisa ter pelo menos um dos seus valores na memória;
         - cf da condição = menor cf entre as condições (incerteza.cf_condicao);
         - cf da conclusão = cf da condição x cf da regra (incerteza.cf_conclusao);
         - se o fato já existe, as certezas são combinadas (incerteza.combinar).
    3. Cada regra disparada gera um Disparo (matéria-prima da explicação).
    4. Derivados com cf >= limiar_cf formam `conclusoes`.
    5. classificacao_final escolhe a cor MAIS URGENTE entre as conclusões, não a de maior cf.
"""
from __future__ import annotations

from .base_conhecimento import BaseConhecimento
from .incerteza import cf_condicao, cf_conclusao, combinar
from .modelos import Disparo, Regra, ResultadoInferencia


def _montar_memoria(respostas: dict[str, str], cf_entradas: dict[str, float] | None) -> dict[str, float]:
    """Transforma {'sinais_avc': 'sim'} em {'sinais_avc=sim': 1.0}.

    cf_entradas pode usar como chave o atributo ('grupo_risco') ou o fato ('grupo_risco=sim').
    """
    cf_entradas = cf_entradas or {}
    memoria: dict[str, float] = {}
    for atributo, valor in respostas.items():
        fato = f"{atributo}={valor}"
        memoria[fato] = cf_entradas.get(fato, cf_entradas.get(atributo, 1.0))
    return memoria


def _avaliar_se(regra: Regra, memoria: dict[str, float]) -> tuple[float, tuple[tuple[str, float], ...]] | None:
    """Devolve (cf do SE, fatos usados) se a regra pode disparar; None caso contrário.

    Numa condição com 'a|b', vale o valor presente na memória com maior cf.
    """
    usados: list[tuple[str, float]] = []
    for cond in regra.se:
        presentes = [(f, memoria[f]) for f in cond.fatos() if memoria.get(f, 0.0) > 0.0]
        if not presentes:
            return None
        usados.append(max(presentes, key=lambda par: par[1]))
    return cf_condicao(cf for _, cf in usados), tuple(usados)


def inferir(
    base: BaseConhecimento,
    respostas: dict[str, str],
    cf_entradas: dict[str, float] | None = None,
) -> ResultadoInferencia:
    """Executa o encadeamento para frente, camada por camada."""
    memoria = _montar_memoria(respostas, cf_entradas)
    disparos: list[Disparo] = []

    for camada in base.camadas():
        for regra in base.regras_da_camada(camada):
            avaliacao = _avaliar_se(regra, memoria)
            if avaliacao is None:
                continue
            cf_se, usados = avaliacao

            gerados: list[tuple[str, float]] = []
            for conclusao in regra.entao:
                cf = cf_conclusao(cf_se, conclusao.cf)
                gerados.append((conclusao.fato, cf))
                if conclusao.fato in memoria:
                    memoria[conclusao.fato] = combinar(memoria[conclusao.fato], cf)
                else:
                    memoria[conclusao.fato] = cf

            disparos.append(Disparo(regra.id, cf_se, usados, tuple(gerados)))

    conclusoes = {
        fato: cf
        for fato, cf in memoria.items()
        if base.eh_derivado(fato) and cf >= base.limiar_cf
    }
    return ResultadoInferencia(memoria=memoria, disparos=disparos, conclusoes=conclusoes)


def classificacao_final(base: BaseConhecimento, resultado: ResultadoInferencia) -> str | None:
    """Cor final: a mais urgente (pela ordem do catálogo) entre as que passaram do limiar.

    catalogo.json -> 'ordem_urgencia' é lida da mais urgente para a menos urgente.
    Devolve None se nenhuma cor passou do limiar.
    """
    for cor in base.catalogo["ordem_urgencia"]:
        if f"classificacao={cor}" in resultado.conclusoes:
            return cor
    return None
