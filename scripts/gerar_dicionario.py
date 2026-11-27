"""Gera docs/dicionario_regras.md a partir dos JSON da pasta kb/.

Uso: python scripts/gerar_dicionario.py

O dicionário nunca é editado à mão: altere kb/*.json e rode este script de novo.
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from sistema_especialista.base_conhecimento import BaseConhecimento, carregar  # noqa: E402

DESTINO = RAIZ / "docs" / "dicionario_regras.md"

NOMES_CAMADAS = {
    1: "Camada 1 — Sinais → Quadro de triagem",
    2: "Camada 2 — Quadro → Classificação de risco",
    3: "Camada 3 — Classificação → Encaminhamento e avisos",
}


def _celula(texto: str) -> str:
    return texto.replace("|", "\\|")


def _descricao(base: BaseConhecimento, fato: str) -> str:
    atributo, _, valor = fato.partition("=")
    return base.catalogo.get("descricoes", {}).get(atributo, {}).get(valor, fato)


def gerar(base: BaseConhecimento) -> str:
    linhas = [
        "# Dicionário de fatos e regras",
        "",
        "> Gerado automaticamente por `scripts/gerar_dicionario.py` a partir de `kb/`. Não edite à mão.",
        "",
        "## Configuração",
        "",
        f"- **Limiar de certeza (`limiar_cf`):** {base.limiar_cf} — conclusões abaixo disso não são apresentadas.",
        f"- **Certeza da resposta \"não sei\" (`cf_resposta_nao_sei`):** {base.cf_nao_sei}",
        "",
        "## Fatos de entrada (perguntas da triagem)",
        "",
        "Cada resposta vira um fato `atributo=valor` com certeza 1,0 (ou a do \"não sei\").",
        "",
        "| Atributo | Pergunta | Valor | Significado | Usado em |",
        "| --- | --- | --- | --- | --- |",
    ]
    for p in base.perguntas:
        regras = ", ".join(r.id for r in base.regras_que_usam(p.atributo)) or "—"
        for i, (valor, rotulo) in enumerate(p.opcoes.items()):
            if i == 0:
                linhas.append(f"| `{p.atributo}` | {_celula(p.texto)} | `{valor}` | {_celula(rotulo)} | {regras} |")
            else:
                linhas.append(f"| | | `{valor}` | {_celula(rotulo)} | |")

    linhas += [
        "",
        "## Fatos derivados (conclusões do motor)",
        "",
        "| Fato | Descrição | Concluído por | Usado em |",
        "| --- | --- | --- | --- |",
    ]
    for atributo, valores in base.derivados.items():
        for valor in valores:
            fato = f"{atributo}={valor}"
            produz = ", ".join(r.id for r in base.regras_que_concluem(fato)) or "—"
            usam = ", ".join(
                r.id for r in base.regras if any(fato in c.fatos() for c in r.se)
            ) or "—"
            linhas.append(f"| `{fato}` | {_celula(_descricao(base, fato))} | {produz} | {usam} |")

    linhas += [
        "",
        "## Classificações de risco",
        "",
        "Ordem de urgência (da mais para a menos urgente): "
        + " > ".join(f"`{c}`" for c in base.catalogo["ordem_urgencia"])
        + ".",
        "",
        "| Cor | Nome | Tempo máximo de espera |",
        "| --- | --- | --- |",
    ]
    for cor, info in base.catalogo["classificacoes"].items():
        tempo = "imediato" if info["tempo_max_espera_min"] == 0 else f"{info['tempo_max_espera_min']} min"
        linhas.append(f"| {cor} | {info['nome']} | {tempo} |")

    linhas += ["", f"## Regras ({len(base.regras)})", ""]
    for camada in base.camadas():
        linhas += [
            f"### {NOMES_CAMADAS.get(camada, f'Camada {camada}')}",
            "",
            "| ID | SE (todas as condições) | ENTÃO (certeza da regra) | Justificativa |",
            "| --- | --- | --- | --- |",
        ]
        for r in base.regras_da_camada(camada):
            se = " E ".join(f"`{c}`" for c in r.se)
            entao = "<br>".join(f"`{c.fato}` ({c.cf})" for c in r.entao)
            linhas.append(f"| {r.id} | {_celula(se)} | {entao} | {_celula(r.justificativa)} |")
        linhas.append("")

    return "\n".join(linhas)


def main() -> int:
    DESTINO.write_text(gerar(carregar()), encoding="utf-8")
    print(f"Dicionário gerado em {DESTINO.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
