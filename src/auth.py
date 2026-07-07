"""Autenticação via API Key."""

from __future__ import annotations

from fastapi import HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader

from src import config

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verificar_api_key(
    api_key_header_value: str | None = Security(api_key_header),
) -> str:
    """Valida o cabeçalho X-API-Key contra o segredo configurado."""
    if api_key_header_value is None or api_key_header_value != config.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Credenciais inválidas ou ausentes",
        )
    return api_key_header_value
