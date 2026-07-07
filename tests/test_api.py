"""Testes de integração da API."""

from __future__ import annotations

import os

os.environ["API_KEY"] = "chave_de_teste_secreta"

import pytest
from fastapi.testclient import TestClient

from src.api import app

API_KEY_VALIDA = "chave_de_teste_secreta"
HEADERS_AUTENTICADOS = {"X-API-Key": API_KEY_VALIDA}

PAYLOAD_EXEMPLO_PDF = {
    "comprimento_padrao": 3000,
    "itens": [
        {"id": "item_A", "comprimento": 1150, "quantidade": 3},
        {"id": "item_B", "comprimento": 800, "quantidade": 4},
        {"id": "item_C", "comprimento": 450, "quantidade": 5},
    ],
    "time_limit": 60,
}


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health_check(client: TestClient) -> None:
    resposta = client.get("/health")
    assert resposta.status_code == 200
    assert resposta.json() == {"status": "healthy"}


def test_otimizar_sucesso(client: TestClient) -> None:
    resposta = client.post(
        "/otimizar",
        json=PAYLOAD_EXEMPLO_PDF,
        headers=HEADERS_AUTENTICADOS,
    )
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["status_solver"] in ("OPTIMAL", "FEASIBLE")
    assert len(corpo["plano_corte"]) > 0
    assert corpo["barras_utilizadas"] > 0
    assert corpo["desperdicio_total_mm"] >= 0
    assert corpo["tempo_execucao_segundos"] >= 0


def test_otimizar_sem_api_key(client: TestClient) -> None:
    resposta = client.post("/otimizar", json=PAYLOAD_EXEMPLO_PDF)
    assert resposta.status_code == 403
    assert resposta.json()["detail"] == "Credenciais inválidas ou ausentes"


def test_otimizar_api_key_invalida(client: TestClient) -> None:
    resposta = client.post(
        "/otimizar",
        json=PAYLOAD_EXEMPLO_PDF,
        headers={"X-API-Key": "chave_errada"},
    )
    assert resposta.status_code == 403
    assert resposta.json()["detail"] == "Credenciais inválidas ou ausentes"


def test_otimizar_comprimento_negativo(client: TestClient) -> None:
    payload = {**PAYLOAD_EXEMPLO_PDF, "comprimento_padrao": 0}
    resposta = client.post(
        "/otimizar", json=payload, headers=HEADERS_AUTENTICADOS
    )
    assert resposta.status_code == 422


def test_otimizar_item_maior_que_barra(client: TestClient) -> None:
    payload = {
        "comprimento_padrao": 3000,
        "itens": [{"id": "item_gigante", "comprimento": 3500, "quantidade": 1}],
    }
    resposta = client.post(
        "/otimizar", json=payload, headers=HEADERS_AUTENTICADOS
    )
    assert resposta.status_code == 422


def test_otimizar_quantidade_invalida(client: TestClient) -> None:
    payload = {
        "comprimento_padrao": 3000,
        "itens": [{"id": "item_A", "comprimento": 1150, "quantidade": 0}],
    }
    resposta = client.post(
        "/otimizar", json=payload, headers=HEADERS_AUTENTICADOS
    )
    assert resposta.status_code == 422


def test_otimizar_time_limit_estourado(client: TestClient) -> None:
    payload = {**PAYLOAD_EXEMPLO_PDF, "time_limit": 200}
    resposta = client.post(
        "/otimizar", json=payload, headers=HEADERS_AUTENTICADOS
    )
    assert resposta.status_code == 422
