
"""Testes das fórmulas de fator de certeza (M5)."""
import pytest
from sistema_especialista.base_conhecimento import carregar
from sistema_especialista.incerteza import cf_condicao, cf_conclusao, combinar


@pytest.fixture(scope="module")
def base():
    return carregar()


# ---------- cf_condicao: menor valor entre as condições ----------

def test_condicao_usa_o_menor_valor():
    assert cf_condicao([1.0, 0.5, 0.8]) == 0.5


def test_condicao_com_um_unico_valor():
    assert cf_condicao([0.7]) == 0.7


def test_condicao_aceita_qualquer_iteravel():
    assert cf_condicao(x for x in (0.9, 0.6)) == 0.6


def test_condicao_lista_vazia_da_erro():
    with pytest.raises(ValueError):
        cf_condicao([])


# ---------- cf_conclusao: condição x regra ----------

def test_conclusao_multiplica():
    assert cf_conclusao(0.5, 0.9) == pytest.approx(0.45)


def test_conclusao_com_entrada_certa_mantem_cf_da_regra():
    assert cf_conclusao(1.0, 0.85) == pytest.approx(0.85)


# ---------- combinar: a + b x (1 - a) ----------

def test_combinar_exemplo_do_enunciado():
    assert combinar(0.6, 0.8) == pytest.approx(0.92)


def test_combinar_e_comutativa():
    assert combinar(0.3, 0.7) == pytest.approx(combinar(0.7, 0.3))


def test_combinar_com_zero_nao_muda_nada():
    assert combinar(0.6, 0.0) == pytest.approx(0.6)
    assert combinar(0.0, 0.0) == pytest.approx(0.0)


def test_combinar_com_um_vira_certeza_total():
    assert combinar(0.6, 1.0) == pytest.approx(1.0)


def test_combinar_nunca_passa_de_um():
    assert combinar(0.99, 0.99) <= 1.0


def test_combinar_reforca_a_certeza():
    assert combinar(0.6, 0.8) > max(0.6, 0.8)


# ---------- valores inválidos ----------

@pytest.mark.parametrize("ruim", [-0.1, 1.5])
def test_valores_fora_da_faixa_dao_erro(ruim):
    with pytest.raises(ValueError):
        combinar(ruim, 0.5)
    with pytest.raises(ValueError):
        cf_conclusao(ruim, 0.5)
    with pytest.raises(ValueError):
        cf_condicao([ruim])


# ---------- casos ligados à base de conhecimento ----------

def test_nao_sei_em_tudo_ainda_passa_do_limiar(base):
    nao_sei = base.cf_nao_sei  # 0.5
    cf = cf_conclusao(cf_condicao([nao_sei, nao_sei]), 0.9)
    assert cf == pytest.approx(0.45)
    assert cf >= base.limiar_cf


def test_cadeia_do_cenario_avc_com_nao_sei(base):
    """Cenário 11: o alerta de AVC se mantém mesmo com 'não sei' nas 3 camadas."""
    quadro = cf_conclusao(base.cf_nao_sei, base.regra("R05").entao[0].cf)  # 0.45
    cor = cf_conclusao(quadro, base.regra("R13").entao[0].cf)              # 0.4275
    encaminhamento = cf_conclusao(cor, base.regra("R18").entao[0].cf)      # ~0.406
    assert quadro == pytest.approx(0.45)
    assert cor == pytest.approx(0.4275)
    assert encaminhamento == pytest.approx(0.406125)
    assert min(quadro, cor, encaminhamento) >= base.limiar_cf


def test_idoso_com_dor_no_peito_combina_r03_e_r04(base):
    """Cenário 1: R03 (0.8) e R04 (0.6) concluem suspeita_cardiaca -> 0.92."""
    r03 = cf_conclusao(cf_condicao([1.0]), base.regra("R03").entao[0].cf)
    r04 = cf_conclusao(cf_condicao([1.0, 1.0]), base.regra("R04").entao[0].cf)
    assert combinar(r03, r04) == pytest.approx(0.92)
