"""Testes da base de conhecimento (M1). Já passam: protegem a base contra erros de edição."""
import pytest

from sistema_especialista.base_conhecimento import carregar, validar


@pytest.fixture(scope="module")
def base():
    return carregar()


def test_base_nao_tem_inconsistencias(base):
    assert validar(base) == []


def test_tem_exatamente_20_regras(base):
    assert len(base.regras) == 20


def test_ids_das_regras_sao_sequenciais(base):
    assert [r.id for r in base.regras] == [f"R{n:02d}" for n in range(1, 21)]


def test_toda_regra_tem_justificativa(base):
    assert all(r.justificativa.strip() for r in base.regras)


def test_tres_camadas(base):
    assert base.camadas() == [1, 2, 3]


def test_ordem_de_urgencia_cobre_todas_as_classificacoes(base):
    assert set(base.catalogo["ordem_urgencia"]) == set(base.derivados["classificacao"])
    assert base.catalogo["ordem_urgencia"][0] == "vermelho"


def test_regras_que_usam_e_concluem(base):
    assert base.regras_que_usam("grupo_risco")
    assert [r.id for r in base.regras_que_concluem("classificacao=vermelho")] == ["R13"]


def test_eh_derivado(base):
    assert base.eh_derivado("quadro=suspeita_avc")
    assert not base.eh_derivado("sinais_avc=sim")
