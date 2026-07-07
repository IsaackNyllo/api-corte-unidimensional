"""Testes unitários do motor de otimização."""

from __future__ import annotations

from src.solver import resolver_problema_corte

INSTANCIA_CLASSICA_ITENS = [
    {"id": "item_A", "comprimento": 1150, "quantidade": 3},
    {"id": "item_B", "comprimento": 800, "quantidade": 4},
    {"id": "item_C", "comprimento": 450, "quantidade": 5},
]
COMPRIMENTO_CLASSICO = 3000


def _validar_consistencia_fisica_barras(
    plano_corte: list[dict],
    comprimento_padrao: int,
) -> None:
    for barra in plano_corte:
        soma = barra["comprimento_utilizado"] + barra["sobra"]
        assert soma == comprimento_padrao


def test_solver_instancia_classica_sucesso() -> None:
    resultado = resolver_problema_corte(COMPRIMENTO_CLASSICO, INSTANCIA_CLASSICA_ITENS)
    assert resultado["status_solver"] == "OPTIMAL"
    assert resultado["barras_utilizadas"] == 4
    assert resultado["desperdicio_total_mm"] == 3100
    assert len(resultado["plano_corte"]) == 4
    _validar_consistencia_fisica_barras(resultado["plano_corte"], COMPRIMENTO_CLASSICO)


def test_solver_barra_unica() -> None:
    resultado = resolver_problema_corte(
        comprimento_padrao=3000,
        itens=[{"id": "item_X", "comprimento": 1000, "quantidade": 2}],
    )
    assert resultado["status_solver"] == "OPTIMAL"
    assert resultado["barras_utilizadas"] == 1
    barra = resultado["plano_corte"][0]
    quantidade = sum(i["quantidade"] for i in barra["itens_cortados"])
    assert quantidade >= 2
    _validar_consistencia_fisica_barras(resultado["plano_corte"], 3000)


def test_solver_item_exato_tamanho_da_barra() -> None:
    resultado = resolver_problema_corte(
        comprimento_padrao=3000,
        itens=[{"id": "item_A", "comprimento": 3000, "quantidade": 2}],
    )
    assert resultado["status_solver"] == "OPTIMAL"
    assert resultado["barras_utilizadas"] == 2
    assert resultado["desperdicio_total_mm"] == 0
    for barra in resultado["plano_corte"]:
        assert barra["sobra"] == 0


def test_solver_multiplas_barras_mesmo_item() -> None:
    resultado = resolver_problema_corte(
        comprimento_padrao=1000,
        itens=[{"id": "item_Z", "comprimento": 600, "quantidade": 3}],
    )
    assert resultado["status_solver"] == "OPTIMAL"
    assert resultado["barras_utilizadas"] == 3
    assert resultado["desperdicio_total_mm"] == 1200


def test_solver_demanda_vazia() -> None:
    resultado = resolver_problema_corte(comprimento_padrao=3000, itens=[])
    assert resultado["status_solver"] == "OPTIMAL"
    assert resultado["barras_utilizadas"] == 0
    assert resultado["plano_corte"] == []


def test_solver_respeito_ao_time_limit() -> None:
    resultado = resolver_problema_corte(
        comprimento_padrao=COMPRIMENTO_CLASSICO,
        itens=INSTANCIA_CLASSICA_ITENS,
        time_limit=1,
    )
    assert resultado["status_solver"] in ("OPTIMAL", "FEASIBLE")
    assert resultado["barras_utilizadas"] > 0
    _validar_consistencia_fisica_barras(resultado["plano_corte"], COMPRIMENTO_CLASSICO)
