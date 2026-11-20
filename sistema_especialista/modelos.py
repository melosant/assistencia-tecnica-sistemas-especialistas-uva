"""Estruturas de dados do sistema especialista.

Convenção: um fato é sempre um texto "atributo=valor", por exemplo "sinais_avc=sim" ou "quadro=suspeita_avc".
Fatos de ENTRADA são as respostas do cliente; fatos DERIVADOS são os que o motor conclui.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Condicao:
    """Condição de uma regra.

    'sinais_avc=sim' vale quando o fato sinais_avc=sim está na memória.
    'febre=moderada|alta' vale quando QUALQUER um dos valores listados está na memória.
    """

    atributo: str
    valores: tuple[str, ...]

    @classmethod
    def de_texto(cls, texto: str) -> "Condicao":
        atributo, valores = texto.split("=", 1)
        return cls(atributo.strip(), tuple(v.strip() for v in valores.split("|")))

    def fatos(self) -> list[str]:
        """Fatos no formato 'atributo=valor' aceitos por esta condição."""
        return [f"{self.atributo}={v}" for v in self.valores]

    def __str__(self) -> str:
        return f"{self.atributo}={'|'.join(self.valores)}"


@dataclass(frozen=True)
class Conclusao:
    """O que uma regra conclui: um fato derivado e a certeza (cf) da regra."""

    fato: str
    cf: float


@dataclass(frozen=True)
class Regra:
    """SE todas as condições valem ENTÃO as conclusões são acrescentadas à memória."""

    id: str
    camada: int
    se: tuple[Condicao, ...]
    entao: tuple[Conclusao, ...]
    justificativa: str


@dataclass(frozen=True)
class Pergunta:
    """Pergunta feita ao cliente para obter um fato de entrada."""

    atributo: str
    texto: str
    opcoes: dict[str, str]  # valor -> rótulo exibido
    aplica_se: Condicao | None = None  # só pergunta se esta condição valer


@dataclass(frozen=True)
class Disparo:
    """Registro de uma regra que disparou. É a matéria-prima do módulo de explicação."""

    regra_id: str
    cf_condicao: float
    fatos_usados: tuple[tuple[str, float], ...]  # (fato, cf) que satisfizeram o SE
    conclusoes: tuple[tuple[str, float], ...]  # (fato, cf gerado por ESTE disparo)


@dataclass
class ResultadoInferencia:
    """Resultado de uma consulta ao motor."""

    memoria: dict[str, float] = field(default_factory=dict)  # fato -> cf (entradas e derivados)
    disparos: list[Disparo] = field(default_factory=list)  # na ordem em que ocorreram
    conclusoes: dict[str, float] = field(default_factory=dict)  # derivados com cf >= limiar
