"""Motor de otimização — formulação de Kantorovich (MIP / SCIP)."""

from __future__ import annotations

import time
from typing import Any

from ortools.linear_solver import pywraplp

TIME_LIMIT_PADRAO_SEGUNDOS = 60
TIME_LIMIT_MAXIMO_SEGUNDOS = 120

_STATUS_PARA_STRING: dict[int, str] = {
    pywraplp.Solver.OPTIMAL: "OPTIMAL",
    pywraplp.Solver.FEASIBLE: "FEASIBLE",
    pywraplp.Solver.INFEASIBLE: "INFEASIBLE",
    pywraplp.Solver.UNBOUNDED: "UNBOUNDED",
    pywraplp.Solver.ABNORMAL: "ABNORMAL",
    pywraplp.Solver.NOT_SOLVED: "NOT_SOLVED",
}


def _limitar_time_limit(time_limit: int) -> int:
    return min(time_limit, TIME_LIMIT_MAXIMO_SEGUNDOS)


def _mapear_status_solver(status: int) -> str:
    return _STATUS_PARA_STRING.get(status, "UNKNOWN")


def _extrair_plano_corte(
    solver: pywraplp.Solver,
    x: list[list[pywraplp.Variable]],
    y: list[pywraplp.Variable],
    itens: list[dict[str, Any]],
    comprimento_padrao: int,
) -> tuple[list[dict[str, Any]], int]:
    plano_corte: list[dict[str, Any]] = []
    desperdicio_total_mm = 0
    barra_id = 0

    for j, variavel_y in enumerate(y):
        if variavel_y.solution_value() <= 0.5:
            continue

        barra_id += 1
        itens_cortados: list[dict[str, Any]] = []
        comprimento_utilizado = 0

        for i, item in enumerate(itens):
            quantidade = int(round(x[i][j].solution_value()))
            if quantidade <= 0:
                continue

            itens_cortados.append(
                {"item_id": item["id"], "quantidade": quantidade}
            )
            comprimento_utilizado += item["comprimento"] * quantidade

        sobra = comprimento_padrao - comprimento_utilizado
        desperdicio_total_mm += sobra

        plano_corte.append(
            {
                "barra_id": barra_id,
                "itens_cortados": itens_cortados,
                "comprimento_utilizado": comprimento_utilizado,
                "sobra": sobra,
            }
        )

    return plano_corte, desperdicio_total_mm


def resolver_problema_corte(
    comprimento_padrao: int,
    itens: list[dict],
    time_limit: int = TIME_LIMIT_PADRAO_SEGUNDOS,
) -> dict:
    """Resolve o CSP 1D pelo modelo de Kantorovich.

    Objetivo: minimizar ``Σ y_j``. Restrições de demanda mínima
    (``Σ x_ij ≥ d_i``) e capacidade por barra (``Σ l_i x_ij ≤ L y_j``).

    Args:
        comprimento_padrao: Comprimento útil L da barra (mm).
        itens: Lista com ``id``, ``comprimento`` e ``quantidade``.
        time_limit: Limite de execução do SCIP em segundos (máx. 120).

    Returns:
        Status do solver, tempo de execução, métricas e plano de corte.
    """
    time_limit_ms = _limitar_time_limit(time_limit) * 1000
    n_barras = sum(item["quantidade"] for item in itens)
    num_itens = len(itens)

    solver = pywraplp.Solver.CreateSolver("SCIP")
    if solver is None:
        return {
            "status_solver": "SOLVER_UNAVAILABLE",
            "tempo_execucao_segundos": 0.0,
            "barras_utilizadas": 0,
            "desperdicio_total_mm": 0,
            "plano_corte": [],
        }

    solver.SetTimeLimit(time_limit_ms)

    y = [solver.BoolVar(f"y_{j}") for j in range(n_barras)]
    x = [
        [
            solver.IntVar(0, solver.infinity(), f"x_{i}_{j}")
            for j in range(n_barras)
        ]
        for i in range(num_itens)
    ]

    for i, item in enumerate(itens):
        solver.Add(
            solver.Sum(x[i][j] for j in range(n_barras)) >= item["quantidade"],
            f"demanda_item_{i}",
        )

    for j in range(n_barras):
        solver.Add(
            solver.Sum(
                itens[i]["comprimento"] * x[i][j] for i in range(num_itens)
            )
            <= comprimento_padrao * y[j],
            f"capacidade_barra_{j}",
        )

    solver.Minimize(solver.Sum(y))

    inicio = time.perf_counter()
    status = solver.Solve()
    tempo_execucao_segundos = time.perf_counter() - inicio
    status_solver = _mapear_status_solver(status)

    if status not in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        return {
            "status_solver": status_solver,
            "tempo_execucao_segundos": tempo_execucao_segundos,
            "barras_utilizadas": 0,
            "desperdicio_total_mm": 0,
            "plano_corte": [],
        }

    plano_corte, desperdicio_total_mm = _extrair_plano_corte(
        solver, x, y, itens, comprimento_padrao
    )

    return {
        "status_solver": status_solver,
        "tempo_execucao_segundos": tempo_execucao_segundos,
        "barras_utilizadas": len(plano_corte),
        "desperdicio_total_mm": desperdicio_total_mm,
        "plano_corte": plano_corte,
    }
