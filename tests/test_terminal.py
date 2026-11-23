"""Testes da interface de terminal (M4)."""
from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

import pytest

import main as main_module
import sistema_especialista.terminal as terminal_module
from sistema_especialista.base_conhecimento import BaseInvalida, carregar
from sistema_especialista.inferencia import inferir
from sistema_especialista.modelos import Condicao, Pergunta
from sistema_especialista.terminal import (
    coletar_entradas,
    exibir_cabecalho,
    exibir_resultado,
    explicar_pergunta,
    iniciar,
    limpar_tela,
    perguntar,
)

CENARIOS = json.loads(
    (Path(__file__).parent / "cenarios.json").read_text(encoding="utf-8")
)


@pytest.fixture(scope="module")
def base():
    return carregar()


def _simular_inputs(monkeypatch, respostas: list[str]) -> None:
    iterador = iter(respostas)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(iterador))


def test_exibir_cabecalho_mostra_empresa_problema_e_aviso(base, capsys):
    exibir_cabecalho(base)
    saida = capsys.readouterr().out
    assert base.empresa["nome"] in saida
    assert base.empresa["problema"] in saida
    assert base.empresa["aviso_legal"] in saida


def test_perguntar_valida_entradas_e_responde_interrogacao(base, monkeypatch, capsys):
    pergunta = base.pergunta("sinais_avc")
    _simular_inputs(monkeypatch, ["", "abc", "99", "?", "2"])

    valor, cf = perguntar(base, pergunta)
    saida = capsys.readouterr().out

    assert (valor, cf) == ("sim", 1.0)
    assert "Entrada vazia" in saida
    assert "Opção inválida" in saida
    assert "Opção fora do intervalo" in saida
    assert "Regra R05" in saida
    assert "Suspeita de AVC" in saida


def test_perguntar_nao_sei_binario_retorna_sim_com_cf_reduzido(base, monkeypatch, capsys):
    pergunta = base.pergunta("sinais_avc")  # opcoes: 1=nao, 2=sim, 3=Nao sei
    _simular_inputs(monkeypatch, ["3"])

    valor, cf = perguntar(base, pergunta)
    saida = capsys.readouterr().out

    assert valor == "sim"
    assert cf == pytest.approx(base.cf_nao_sei)
    assert "50%" in saida


def test_perguntar_nao_sei_multiplas_opcoes_permite_suspeita_ou_pular(base, monkeypatch, capsys):
    pergunta = base.pergunta("febre")  # 1=nao, 2=moderada, 3=alta, 4=Nao sei
    _simular_inputs(monkeypatch, ["4", "?", "9", "2"])

    valor, cf = perguntar(base, pergunta)
    saida = capsys.readouterr().out
    assert valor == "moderada"
    assert cf == pytest.approx(base.cf_nao_sei)
    assert "Por que perguntamos sobre 'febre'" in saida

    _simular_inputs(monkeypatch, ["4", "0"])
    valor_pulado, cf_pulado = perguntar(base, pergunta)
    assert (valor_pulado, cf_pulado) == (None, 0.0)


def test_coletar_entradas_respeita_aplica_se(base, monkeypatch):
    p_condicional = Pergunta(
        atributo="sinais_avc",
        texto="Pergunta condicional de teste",
        opcoes={"nao": "Não", "sim": "Sim"},
        aplica_se=Condicao.de_texto("consciencia=confuso"),
    )
    base_filtrada = replace(
        base,
        perguntas=[base.pergunta("consciencia"), p_condicional],
    )

    # Caso 1: consciencia=alerta -> pula pergunta condicional
    _simular_inputs(monkeypatch, ["1"])
    respostas, cf_entradas = coletar_entradas(base_filtrada)
    assert respostas == {"consciencia": "alerta"}
    assert cf_entradas == {}

    # Caso 2: consciencia=confuso -> faz pergunta condicional e aplica "Não sei"
    _simular_inputs(monkeypatch, ["2", "3"])
    respostas2, cf_entradas2 = coletar_entradas(base_filtrada)
    assert respostas2 == {"consciencia": "confuso", "sinais_avc": "sim"}
    assert cf_entradas2 == {"sinais_avc": pytest.approx(0.5)}


def test_explicar_pergunta_usa_regras_que_usam(base):
    texto = explicar_pergunta(base, base.pergunta("dor_toracica"))
    assert "R03" in texto
    assert "R04" in texto
    assert "R11" in texto


def test_exibir_resultado_completo_com_conflito_e_como(base, monkeypatch, capsys):
    cenario = CENARIOS[8]  # Febre alta com confusão (conflito laranja x verde)
    resultado = inferir(base, cenario["entradas"])
    _simular_inputs(monkeypatch, ["talvez", "s"])

    exibir_resultado(base, resultado)
    saida = capsys.readouterr().out

    assert "LARANJA" in saida
    assert "Até 10 minutos" in saida
    assert "resolução de conflito" in saida
    assert "Febre alta com alteração de consciência" in saida
    assert "consultório médico com prioridade" in saida
    assert "%" in saida
    assert "Regra R08" in saida


def test_exibir_resultado_com_avisos_cenario_1(base, monkeypatch, capsys):
    cenario = CENARIOS[0]
    resultado = inferir(base, cenario["entradas"])
    _simular_inputs(monkeypatch, ["n"])

    exibir_resultado(base, resultado)
    saida = capsys.readouterr().out

    assert "VERMELHO" in saida
    assert "Imediato (0 minutos)" in saida
    assert "Avisos à equipe:" in saida
    assert "Acionar a equipe de emergência imediatamente" in saida


def test_exibir_resultado_sem_conclusao(base, capsys):
    cenario = next(c for c in CENARIOS if c.get("sem_conclusao"))
    resultado = inferir(base, cenario["entradas"])

    exibir_resultado(base, resultado)
    saida = capsys.readouterr().out

    assert "Não foi possível concluir com as informações fornecidas" in saida


def test_iniciar_menu_regras_consulta_completa_e_saida(base, monkeypatch, capsys):
    # Sequência: opção inválida -> 2 (ver regras) -> tentativa inválida -> 0 (voltar) -> 1 (nova consulta) -> ver "como" -> 3 (sair)
    entradas = [
        "9",
        "2",
        "abc",  # mantém na tela de regras
        "0",    # retorna ao menu principal
        "1",
        "1",  # consciencia=alerta
        "1",  # respiracao=normal
        "1",  # dor_toracica=nao
        "3",  # sinais_avc=Não sei -> sim (50%)
        "1",  # sangramento=nao
        "1",  # febre=nao
        "1",  # dor_abdominal=nao
        "1",  # trauma=nenhum
        "2",  # grupo_risco=nao
        "s",  # ver o "como"
        "3",  # sair
    ]
    _simular_inputs(monkeypatch, entradas)

    iniciar(base)
    saida = capsys.readouterr().out

    assert "Opção inválida" in saida
    assert "REGRAS DA BASE DE CONHECIMENTO" in saida
    assert "0. Retornar ao menu principal" in saida
    assert "Camada 1" in saida
    assert "VERMELHO" in saida
    assert "45%" in saida
    assert "Regra R05" in saida
    assert "Encerrando o sistema" in saida


def test_main_executa_e_trata_base_invalida(monkeypatch, capsys):
    _simular_inputs(monkeypatch, ["3"])
    assert main_module.main() == 0

    def _falhar():
        raise BaseInvalida("erro simulado")

    monkeypatch.setattr(main_module, "carregar", _falhar)
    assert main_module.main() == 1
    erro = capsys.readouterr().err
    assert "erro simulado" in erro


def test_limpar_tela_respeita_tty(monkeypatch):
    comandos: list[str] = []
    monkeypatch.setattr(terminal_module.os, "system", lambda cmd: comandos.append(cmd) or 0)

    monkeypatch.setattr(terminal_module.sys.stdout, "isatty", lambda: False)
    limpar_tela()
    assert comandos == []

    monkeypatch.setattr(terminal_module.sys.stdout, "isatty", lambda: True)
    limpar_tela()
    esperado = "cls" if terminal_module.os.name == "nt" else "clear"
    assert comandos == [esperado]


def test_iniciar_limpa_tela_ao_selecionar_opcoes_validas(base, monkeypatch):
    chamadas = 0

    def _contar_limpeza():
        nonlocal chamadas
        chamadas += 1

    monkeypatch.setattr(terminal_module, "limpar_tela", _contar_limpeza)
    entradas = [
        "9",  # inválida -> não limpa
        "2",  # ver regras -> limpa (1)
        "",   # Enter para voltar ao menu -> limpa (2)
        "1",  # nova consulta -> limpa (3)
        "1", "1", "1", "1", "1", "1", "1", "1", "2",
        "n",
        "3",  # sair -> limpa (4)
    ]
    _simular_inputs(monkeypatch, entradas)

    iniciar(base)
    assert chamadas == 4
