"""Testes do motor de inferência (M2): roda os 12 cenários de cenarios.json contra a kb/ real."""
import json
from pathlib import Path

import pytest

from sistema_especialista.base_conhecimento import carregar
from sistema_especialista.inferencia import classificacao_final, inferir

CENARIOS = json.loads(
    (Path(__file__).parent / "cenarios.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def base():
    return carregar()


def _rodar(base, cenario):
    return inferir(base, cenario["entradas"], cenario.get("cf_entradas"))


@pytest.mark.parametrize("cenario", CENARIOS, ids=[f"{i + 1:02d}" for i in range(len(CENARIOS))])
def test_cenario(base, cenario):
    res = _rodar(base, cenario)

    for fato in cenario.get("esperado", []):
        assert fato in res.conclusoes, f"faltou concluir {fato}; obtido: {sorted(res.conclusoes)}"
    for fato in cenario.get("nao_esperado", []):
        assert fato not in res.conclusoes, f"não deveria concluir {fato}"

    if cenario.get("sem_conclusao"):
        assert res.conclusoes == {}
        assert classificacao_final(base, res) is None
    if "classificacao_final" in cenario:
        assert classificacao_final(base, res) == cenario["classificacao_final"]


# ---------- propriedades gerais do motor ----------

def test_memoria_guarda_entradas_com_cf_1(base):
    res = _rodar(base, CENARIOS[1])
    assert res.memoria["sinais_avc=sim"] == 1.0


def test_cf_entradas_e_respeitado(base):
    cenario = next(c for c in CENARIOS if "cf_entradas" in c)
    res = _rodar(base, cenario)
    assert res.memoria["sinais_avc=sim"] == pytest.approx(0.5)
    assert res.memoria["quadro=suspeita_avc"] == pytest.approx(
        0.45)  # R05: 0.5 x 0.9


def test_conclusoes_so_tem_derivados_acima_do_limiar(base):
    for cenario in CENARIOS:
        res = _rodar(base, cenario)
        for fato, cf in res.conclusoes.items():
            assert base.eh_derivado(fato)
            assert cf >= base.limiar_cf


def test_certezas_combinadas_cenario_1(base):
    res = _rodar(base, CENARIOS[0])
    assert res.memoria["quadro=suspeita_cardiaca"] == pytest.approx(
        0.92)  # R03 (0.8) + R04 (0.6)


def test_cada_regra_dispara_no_maximo_uma_vez_e_em_ordem_de_camada(base):
    for cenario in CENARIOS:
        res = _rodar(base, cenario)
        ids = [d.regra_id for d in res.disparos]
        assert len(ids) == len(set(ids))
        camadas = [base.regra(i).camada for i in ids]
        assert camadas == sorted(camadas)


def test_disparo_registra_o_que_a_explicacao_precisa(base):
    res = _rodar(base, CENARIOS[0])
    disparo = next(d for d in res.disparos if d.regra_id == "R04")
    assert disparo.cf_condicao == 1.0
    assert ("grupo_risco=sim", 1.0) in disparo.fatos_usados
    assert disparo.conclusoes == (
        ("quadro=suspeita_cardiaca", pytest.approx(0.6)),)


def test_sem_alerta_nao_dispara_nenhuma_regra(base):
    res = _rodar(base, CENARIOS[-1])
    assert res.disparos == []
    assert res.conclusoes == {}
