"""Leitura e validação da base de conhecimento (pasta kb/).

Esta parte já está pronta: o motor (M2) recebe um objeto BaseConhecimento e não lê JSON.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .modelos import Condicao, Conclusao, Pergunta, Regra

CAMINHO_KB_PADRAO = Path(__file__).resolve().parent.parent / "kb"


class BaseInvalida(Exception):
    """A base de conhecimento tem referências ou valores inconsistentes."""


@dataclass
class BaseConhecimento:
    empresa: dict
    config: dict
    perguntas: list[Pergunta]
    derivados: dict[str, list[str]]  # atributo derivado -> valores possíveis
    regras: list[Regra]
    catalogo: dict

    @property
    def limiar_cf(self) -> float:
        return self.config["limiar_cf"]

    @property
    def cf_nao_sei(self) -> float:
        return self.config["cf_resposta_nao_sei"]

    def eh_derivado(self, fato: str) -> bool:
        """True para fatos como 'quadro=suspeita_avc' (conclusões), False para respostas da triagem."""
        return fato.split("=", 1)[0] in self.derivados

    def regra(self, regra_id: str) -> Regra:
        for r in self.regras:
            if r.id == regra_id:
                return r
        raise KeyError(regra_id)

    def regras_da_camada(self, camada: int) -> list[Regra]:
        return [r for r in self.regras if r.camada == camada]

    def camadas(self) -> list[int]:
        return sorted({r.camada for r in self.regras})

    def regras_que_concluem(self, fato: str) -> list[Regra]:
        """Regras que podem produzir o fato (usado no 'como')."""
        return [r for r in self.regras if any(c.fato == fato for c in r.entao)]

    def regras_que_usam(self, atributo: str) -> list[Regra]:
        """Regras que têm o atributo em alguma condição (usado no 'por quê' de uma pergunta)."""
        return [r for r in self.regras if any(c.atributo == atributo for c in r.se)]

    def pergunta(self, atributo: str) -> Pergunta:
        for p in self.perguntas:
            if p.atributo == atributo:
                return p
        raise KeyError(atributo)


def _ler_json(caminho: Path) -> dict:
    with caminho.open(encoding="utf-8") as arquivo:
        return json.load(arquivo)


def carregar(caminho_kb: Path | str | None = None, validar_base: bool = True) -> BaseConhecimento:
    """Lê fatos.json, regras.json e catalogo.json e devolve a base pronta para o motor."""
    pasta = Path(caminho_kb) if caminho_kb else CAMINHO_KB_PADRAO
    fatos = _ler_json(pasta / "fatos.json")
    regras_json = _ler_json(pasta / "regras.json")
    catalogo = _ler_json(pasta / "catalogo.json")

    perguntas = [
        Pergunta(
            atributo=e["id"],
            texto=e["pergunta"],
            opcoes={o["valor"]: o["rotulo"] for o in e["opcoes"]},
            aplica_se=Condicao.de_texto(e["aplica_se"]) if e.get("aplica_se") else None,
        )
        for e in fatos["entradas"]
    ]
    regras = [
        Regra(
            id=r["id"],
            camada=r["camada"],
            se=tuple(Condicao.de_texto(c) for c in r["se"]),
            entao=tuple(Conclusao(c["fato"], c["cf"]) for c in r["entao"]),
            justificativa=r["justificativa"],
        )
        for r in regras_json["regras"]
    ]
    base = BaseConhecimento(
        empresa=fatos["empresa"],
        config=fatos["config"],
        perguntas=perguntas,
        derivados={d["id"]: list(d["valores"]) for d in fatos["derivados"]},
        regras=regras,
        catalogo=catalogo,
    )
    if validar_base:
        erros = validar(base)
        if erros:
            raise BaseInvalida("\n".join(erros))
    return base


def validar(base: BaseConhecimento) -> list[str]:
    """Confere a coerência da base. Devolve a lista de problemas (vazia = tudo certo)."""
    erros: list[str] = []
    valores = {p.atributo: set(p.opcoes) for p in base.perguntas}
    valores.update({atributo: set(v) for atributo, v in base.derivados.items()})
    descricoes = base.catalogo.get("descricoes", {})

    ids = [r.id for r in base.regras]
    if len(ids) != len(set(ids)):
        erros.append("Há IDs de regra repetidos.")

    for p in base.perguntas:
        if p.aplica_se and p.aplica_se.atributo not in valores:
            erros.append(f"Pergunta {p.atributo}: aplica_se usa atributo desconhecido.")

    # todo valor derivado precisa de um texto em catalogo.json -> "descricoes"
    for atributo, lista in base.derivados.items():
        for valor in lista:
            if valor not in descricoes.get(atributo, {}):
                erros.append(f"{atributo}={valor} não tem descrição em catalogo.json.")

    # a ordem de urgência precisa listar exatamente as classificações possíveis
    ordem = base.catalogo.get("ordem_urgencia")
    if ordem is not None and set(ordem) != set(base.derivados.get("classificacao", [])):
        erros.append("catalogo.json: ordem_urgencia difere dos valores de 'classificacao'.")

    camada_que_produz: dict[str, set[int]] = {}
    for r in base.regras:
        for c in r.entao:
            camada_que_produz.setdefault(c.fato, set()).add(r.camada)

    for r in base.regras:
        for cond in r.se:
            if cond.atributo not in valores:
                erros.append(f"{r.id}: atributo desconhecido '{cond.atributo}'.")
                continue
            for v in cond.valores:
                if v not in valores[cond.atributo]:
                    erros.append(f"{r.id}: valor inválido {cond.atributo}={v}.")
                for camada in camada_que_produz.get(f"{cond.atributo}={v}", ()):
                    if camada >= r.camada:
                        erros.append(
                            f"{r.id} (camada {r.camada}) usa {cond.atributo}={v}, "
                            f"que só é produzido na camada {camada}."
                        )
        for c in r.entao:
            atributo, _, valor = c.fato.partition("=")
            if atributo not in base.derivados or valor not in base.derivados[atributo]:
                erros.append(f"{r.id}: conclusão inválida '{c.fato}'.")
            if not 0 < c.cf <= 1:
                erros.append(f"{r.id}: cf de '{c.fato}' deve estar em (0, 1].")
    return erros
