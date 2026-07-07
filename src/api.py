"""API REST para otimização de corte unidimensional."""

from __future__ import annotations

import asyncio
import logging

from fastapi import Depends, FastAPI, HTTPException

from src.auth import verificar_api_key
from src.schemas import OtimizarInput, OtimizarOutput
from src.solver import resolver_problema_corte

logger = logging.getLogger(__name__)

TAGS_METADATA = [
    {
        "name": "Otimização",
        "description": "Resolução do problema de corte via MIP (OR-Tools / SCIP).",
    },
    {
        "name": "Monitoramento",
        "description": "Verificação de disponibilidade do serviço.",
    },
]

app = FastAPI(
    title="API de Otimização - Corte Unidimensional",
    description=(
        "Serviço **Optimization-as-a-Service** para o Problema de Corte "
        "Unidimensional (CSP 1D).\n\n"
        "Modela a instância pela formulação de **Kantorovich** e retorna o "
        "plano de corte que minimiza o número de barras utilizadas.\n\n"
        "**Autenticação:** rotas protegidas exigem o cabeçalho `X-API-Key`."
    ),
    version="1.0.0",
    openapi_tags=TAGS_METADATA,
)


@app.get("/health", tags=["Monitoramento"], summary="Verificar saúde da API")
async def health() -> dict[str, str]:
    """Retorna o status operacional do serviço.

    Endpoint público para health checks de balanceadores e monitoramento.
    """
    return {"status": "healthy"}


@app.post(
    "/otimizar",
    tags=["Otimização"],
    response_model=OtimizarOutput,
    summary="Otimizar plano de corte unidimensional",
)
async def otimizar(
    payload: OtimizarInput,
    _: str = Depends(verificar_api_key),
) -> OtimizarOutput:
    """Resolve a instância de corte e retorna o plano ótimo de barras.

    Valida a entrada, executa o modelo de Kantorovich (SCIP) e devolve o
    status do solver, métricas agregadas e alocação item a item por barra.

    Requer o cabeçalho `X-API-Key`.
    """
    itens_solver = [item.model_dump() for item in payload.itens]

    try:
        resultado = await asyncio.to_thread(
            resolver_problema_corte,
            payload.comprimento_padrao,
            itens_solver,
            payload.time_limit,
        )
    except Exception:
        logger.exception("Falha ao executar o solver.")
        raise HTTPException(
            status_code=500,
            detail="Erro interno no servidor ao processar o modelo de otimização",
        ) from None

    return OtimizarOutput.model_validate(resultado)
