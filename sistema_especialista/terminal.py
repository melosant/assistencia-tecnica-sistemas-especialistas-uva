"""Interface de terminal (M4) do Sistema Especialista da Clínica Vida Plena."""
from __future__ import annotations

import os
import sys

from .base_conhecimento import BaseConhecimento, carregar
from .explicacao import explicar_como
from .inferencia import classificacao_final, inferir
from .modelos import Condicao, Pergunta, ResultadoInferencia

_RESET = "\033[0m"
_NEGRITO = "\033[1m"
_CIANO = "\033[1;36m"
_CINZA = "\033[2m"

_CORES_CLASSIFICACAO = {
    "vermelho": "\033[1;31m",
    "laranja": "\033[1;38;5;208m",
    "amarelo": "\033[1;33m",
    "verde": "\033[1;32m",
}

_NOMES_CAMADAS = {
    1: "Camada 1 — Sinais -> Quadro de triagem",
    2: "Camada 2 — Quadro -> Classificação de risco",
    3: "Camada 3 — Classificação -> Encaminhamento e avisos",
}

_SEPARADOR = "=" * 64
_SUBSEPARADOR = "-" * 64


def _cores_ativas() -> bool:
    """Ativa cores ANSI apenas em terminais interativos e sem NO_COLOR."""
    if os.environ.get("NO_COLOR"):
        return False
    if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
        return False
    try:
        import colorama  # type: ignore

        colorama.just_fix_windows_console()
    except Exception:
        pass
    return True


def limpar_tela() -> None:
    """Limpa o terminal quando executado em sessão interativa."""
    if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
        return
    os.system("cls" if os.name == "nt" else "clear")


def _estilizar(texto: str, codigo: str, usar_cores: bool | None = None) -> str:
    ativo = _cores_ativas() if usar_cores is None else usar_cores
    if not ativo or not codigo:
        return texto
    return f"{codigo}{texto}{_RESET}"


def _descrever_fato(base: BaseConhecimento, fato: str) -> str:
    """Traduz 'atributo=valor' usando catalogo.json -> descricoes, com fallback."""
    atributo, _, valor = fato.partition("=")
    return base.catalogo.get("descricoes", {}).get(atributo, {}).get(valor, fato)


def _condicao_satisfeita(condicao: Condicao | None, respostas: dict[str, str]) -> bool:
    if condicao is None:
        return True
    return respostas.get(condicao.atributo) in condicao.valores


def exibir_cabecalho(base: BaseConhecimento) -> None:
    """Exibe identificação da clínica, contexto do problema e aviso legal."""
    empresa = base.empresa
    print(_SEPARADOR)
    print(_estilizar(empresa["nome"], _CIANO))
    if empresa.get("segmento"):
        print(empresa["segmento"])
    print(_SUBSEPARADOR)
    print(f"Sobre: {empresa['problema']}")
    print()
    print(_estilizar(f"AVISO LEGAL: {empresa['aviso_legal']}", _NEGRITO))
    print(_SEPARADOR)


def explicar_pergunta(base: BaseConhecimento, pergunta: Pergunta) -> str:
    """Explica por que uma pergunta está sendo feita usando base.regras_que_usam."""
    regras = base.regras_que_usam(pergunta.atributo)
    if not regras:
        return "Esta informação auxilia na avaliação geral da triagem."

    linhas = [
        f"Por que perguntamos sobre '{pergunta.atributo}':",
    ]
    for regra in regras:
        condicoes_alvo = [str(c) for c in regra.se if c.atributo == pergunta.atributo]
        conclusoes_legiveis = [
            f"{_descrever_fato(base, c.fato)} ({c.cf:.0%})" for c in regra.entao
        ]
        linhas.append(
            f"  - Regra {regra.id} (camada {regra.camada}): avalia "
            f"{', '.join(condicoes_alvo)} para concluir {', '.join(conclusoes_legiveis)}."
        )
        linhas.append(f"    Motivo: {regra.justificativa}")
    return "\n".join(linhas)


def _perguntar_suspeita_nao_sei(
    base: BaseConhecimento,
    pergunta: Pergunta,
    opcoes: list[tuple[str, str]],
) -> tuple[str | None, float]:
    """Para perguntas com 3+ opções, coleta qual opção o atendente suspeita (cf reduzido)."""
    print(
        f"Como não há certeza (certeza registrada será {base.cf_nao_sei:.0%}), "
        "qual opção parece mais provável?"
    )
    for indice, (_, rotulo) in enumerate(opcoes, start=1):
        print(f"  {indice}. {rotulo}")
    print("  0. Nenhuma suspeita / pular esta pergunta")

    while True:
        entrada = input(f"Escolha uma opção (0 a {len(opcoes)}) ou '?': ").strip()
        if not entrada:
            print("Entrada vazia. Digite o número da opção mais provável ou 0 para pular.")
            continue
        if entrada == "?":
            print()
            print(explicar_pergunta(base, pergunta))
            print()
            continue
        if not entrada.isdigit():
            print(f"Opção inválida. Digite apenas um número entre 0 e {len(opcoes)}.")
            continue
        escolha = int(entrada)
        if escolha == 0:
            print("Pergunta pulada sem registro de sinal.")
            return None, 0.0
        if 1 <= escolha <= len(opcoes):
            valor, rotulo = opcoes[escolha - 1]
            print(f"Registrado '{rotulo}' com certeza de {base.cf_nao_sei:.0%}.")
            return valor, base.cf_nao_sei
        print(f"Opção fora do intervalo. Escolha um número entre 0 e {len(opcoes)}.")


def perguntar(base: BaseConhecimento, pergunta: Pergunta) -> tuple[str | None, float]:
    """Faz uma pergunta numerada ao usuário, validando a entrada e aceitando '?' e 'Não sei'."""
    opcoes = list(pergunta.opcoes.items())
    indice_nao_sei = len(opcoes) + 1

    def _mostrar_opcoes() -> None:
        print(f"\n{pergunta.texto}")
        for indice, (_, rotulo) in enumerate(opcoes, start=1):
            print(f"  {indice}. {rotulo}")
        print(f"  {indice_nao_sei}. Não sei")

    _mostrar_opcoes()
    while True:
        entrada = input(
            f"Escolha uma opção (1 a {indice_nao_sei}, ou '?' para saber o porquê): "
        ).strip()

        if not entrada:
            print(
                f"Entrada vazia. Por favor, digite um número de 1 a {indice_nao_sei} ou '?'."
            )
            continue

        if entrada == "?":
            print()
            print(explicar_pergunta(base, pergunta))
            _mostrar_opcoes()
            continue

        if not entrada.isdigit():
            print(
                f"Opção inválida. Digite apenas um número entre 1 e {indice_nao_sei} ou '?'."
            )
            continue

        escolha = int(entrada)
        if 1 <= escolha <= len(opcoes):
            valor, _ = opcoes[escolha - 1]
            return valor, 1.0

        if escolha == indice_nao_sei:
            if set(pergunta.opcoes) == {"sim", "nao"}:
                print(
                    f"Como não há certeza, registrando 'Sim' com certeza de "
                    f"{base.cf_nao_sei:.0%} (protocolo de segurança)."
                )
                return "sim", base.cf_nao_sei
            return _perguntar_suspeita_nao_sei(base, pergunta, opcoes)

        print(f"Opção fora do intervalo. Escolha um número entre 1 e {indice_nao_sei}.")


def coletar_entradas(base: BaseConhecimento) -> tuple[dict[str, str], dict[str, float]]:
    """Percorre base.perguntas respeitando aplica_se e coleta respostas e certezas."""
    respostas: dict[str, str] = {}
    cf_entradas: dict[str, float] = {}

    print("\n--- Início da Triagem ---")
    print("Responda às perguntas abaixo. Digite '?' a qualquer momento para entender o motivo.")

    numero_pergunta = 0
    for pergunta in base.perguntas:
        if not _condicao_satisfeita(pergunta.aplica_se, respostas):
            continue
        numero_pergunta += 1
        print(f"\n[Pergunta {numero_pergunta}]", end="")
        valor, cf = perguntar(base, pergunta)
        if valor is not None:
            respostas[pergunta.atributo] = valor
            if cf < 1.0:
                cf_entradas[pergunta.atributo] = cf

    return respostas, cf_entradas


def exibir_regras(base: BaseConhecimento) -> None:
    """Lista todas as regras da base organizadas por camada."""
    print(f"\n{_SEPARADOR}")
    print(_estilizar("REGRAS DA BASE DE CONHECIMENTO", _CIANO))
    print(_SEPARADOR)

    for camada in base.camadas():
        titulo = _NOMES_CAMADAS.get(camada, f"Camada {camada}")
        print(f"\n{_estilizar(titulo, _NEGRITO)}")
        print(_SUBSEPARADOR)
        for regra in base.regras_da_camada(camada):
            condicoes = " E ".join(str(c) for c in regra.se)
            conclusoes = ", ".join(f"{c.fato} ({c.cf:.0%})" for c in regra.entao)
            print(f"[{regra.id}] SE {condicoes}")
            print(f"       ENTÃO {conclusoes}")
            print(f"       Justificativa: {regra.justificativa}")
    print(_SEPARADOR)


def _conclusoes_por_prefixo(
    resultado: ResultadoInferencia,
    prefixo: str,
) -> list[tuple[str, float]]:
    pares = [
        (fato, cf)
        for fato, cf in resultado.conclusoes.items()
        if fato.startswith(f"{prefixo}=")
    ]
    return sorted(pares, key=lambda item: item[1], reverse=True)


def exibir_resultado(base: BaseConhecimento, resultado: ResultadoInferencia) -> None:
    """Exibe classificação final, tempo máximo, quadros, encaminhamento, avisos e o 'como'."""
    print(f"\n{_SEPARADOR}")
    print(_estilizar("RESULTADO DA TRIAGEM", _CIANO))
    print(_SEPARADOR)

    cor = classificacao_final(base, resultado)
    if not resultado.conclusoes:
        print("Não foi possível concluir com as informações fornecidas")
        print(
            "Nenhum sinal de alerta atingiu o limiar de certeza. "
            "Em caso de dúvida clínica ou persistência dos sintomas, procure avaliação presencial."
        )
        print(_SEPARADOR)
        return

    if cor is not None:
        info_cor = base.catalogo["classificacoes"][cor]
        nome_cor = info_cor["nome"]
        desc_cor = _descrever_fato(base, f"classificacao={cor}")
        cf_cor = resultado.conclusoes[f"classificacao={cor}"]
        tempo = info_cor["tempo_max_espera_min"]
        tempo_txt = "Imediato (0 minutos)" if tempo == 0 else f"Até {tempo} minutos"

        codigo_cor = _CORES_CLASSIFICACAO.get(cor, _NEGRITO)
        print(
            f"Classificação de risco: "
            f"{_estilizar(f'{cor.upper()} — {nome_cor}', codigo_cor)} "
            f"(certeza: {cf_cor:.0%})"
        )
        print(f"Descrição: {desc_cor}")
        print(f"Tempo máximo de espera: {tempo_txt}")
        outras_cores = [
            (c, resultado.conclusoes[f"classificacao={c}"])
            for c in base.catalogo["ordem_urgencia"]
            if c != cor and f"classificacao={c}" in resultado.conclusoes
        ]
        if outras_cores:
            lista = ", ".join(f"{c} ({cf:.0%})" for c, cf in outras_cores)
            print(
                f"Observação (resolução de conflito): também foram sugeridas [{lista}]; "
                f"prevalece a mais urgente ({cor})."
            )
    else:
        print("Classificação de risco: inconclusiva (nenhuma cor atingiu o limiar de certeza).")

    quadros = _conclusoes_por_prefixo(resultado, "quadro")
    if quadros:
        print("\nQuadros suspeitados:")
        for fato, cf in quadros:
            print(f"  - {_descrever_fato(base, fato)} (certeza: {cf:.0%})")

    encaminhamentos = _conclusoes_por_prefixo(resultado, "encaminhamento")
    if encaminhamentos:
        print("\nEncaminhamento:")
        for fato, cf in encaminhamentos:
            print(f"  - {_descrever_fato(base, fato)} (certeza: {cf:.0%})")

    avisos = _conclusoes_por_prefixo(resultado, "aviso")
    if avisos:
        print(_estilizar("\nAvisos à equipe:", _NEGRITO))
        for fato, cf in avisos:
            print(f"  ! {_descrever_fato(base, fato)} (certeza: {cf:.0%})")

    print(_SEPARADOR)

    while True:
        ver_como = input(
            "Deseja ver o 'como' (cadeia de regras que levou à conclusão)? (s/n): "
        ).strip().lower()
        if ver_como in {"s", "sim"}:
            print()
            print(explicar_como(base, resultado))
            print(_SEPARADOR)
            break
        if ver_como in {"n", "nao", "não"}:
            break
        print("Resposta inválida. Digite 's' para sim ou 'n' para não.")


def _aguardar_retorno_menu() -> None:
    """Mantém a tela atual visível até o usuário optar por voltar ao menu."""
    print("\n  0. Retornar ao menu principal")
    while True:
        try:
            escolha = input("Digite 0 ou pressione Enter para retornar ao menu: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if escolha in {"", "0"}:
            return
        print("Opção inválida. Digite 0 ou pressione Enter para retornar ao menu.")


def iniciar(base: BaseConhecimento | None = None) -> None:
    """Executa o menu principal em laço no terminal."""
    base = base or carregar()
    exibir_cabecalho(base)

    while True:
        print("\nMenu Principal:")
        print("  1. Nova consulta")
        print("  2. Ver as regras da base")
        print("  3. Sair")

        try:
            opcao = input("Escolha uma opção (1 a 3): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nEncerrando o sistema. Até logo!")
            break

        if opcao == "1":
            limpar_tela()
            try:
                respostas, cf_entradas = coletar_entradas(base)
            except (EOFError, KeyboardInterrupt):
                print("\nConsulta interrompida. Retornando ao menu principal.")
                continue
            resultado = inferir(base, respostas, cf_entradas)
            try:
                exibir_resultado(base, resultado)
            except (EOFError, KeyboardInterrupt):
                print("\nRetornando ao menu principal.")
        elif opcao == "2":
            limpar_tela()
            exibir_regras(base)
            _aguardar_retorno_menu()
            limpar_tela()
            exibir_cabecalho(base)
        elif opcao == "3":
            limpar_tela()
            print("Encerrando o sistema. Até logo!")
            break
        else:
            print("Opção inválida. Por favor, digite 1, 2 ou 3.")
