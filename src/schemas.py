"""Contratos Pydantic de entrada e saída da API."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

TIME_LIMIT_PADRAO_SEGUNDOS = 60
TIME_LIMIT_MAXIMO_SEGUNDOS = 120
TIME_LIMIT_MINIMO_SEGUNDOS = 1


class ItemInput(BaseModel):
    """Item demandado no plano de corte."""

    id: str = Field(
        ...,
        description="Identificador único do item (ex.: item_A).",
        min_length=1,
        json_schema_extra={"examples": ["item_A", "item_B", "item_C"]},
    )
    comprimento: int = Field(
        ...,
        description="Comprimento solicitado l_i da peça, em milímetros (deve ser > 0).",
        json_schema_extra={"examples": [1150, 800, 450]},
    )
    quantidade: int = Field(
        ...,
        description="Quantidade demandada d_i do item (deve ser > 0).",
        json_schema_extra={"examples": [3, 4, 5]},
    )

    @field_validator("comprimento")
    @classmethod
    def validar_comprimento_positivo(cls, valor: int) -> int:
        if valor <= 0:
            raise ValueError(
                "O comprimento do item deve ser estritamente maior que zero."
            )
        return valor

    @field_validator("quantidade")
    @classmethod
    def validar_quantidade_positiva(cls, valor: int) -> int:
        if valor <= 0:
            raise ValueError(
                "A quantidade demandada deve ser estritamente maior que zero."
            )
        return valor


class OtimizarInput(BaseModel):
    """Payload de otimização."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "comprimento_padrao": 3000,
                    "itens": [
                        {"id": "item_A", "comprimento": 1150, "quantidade": 3},
                        {"id": "item_B", "comprimento": 800, "quantidade": 4},
                        {"id": "item_C", "comprimento": 450, "quantidade": 5},
                    ],
                    "time_limit": 60,
                }
            ]
        }
    )

    comprimento_padrao: int = Field(
        ...,
        description="Comprimento útil L da barra padrão, em milímetros (deve ser > 0).",
        json_schema_extra={"examples": [3000]},
    )
    itens: list[ItemInput] = Field(
        ...,
        description="Lista de itens demandados (mínimo de 1 item).",
        min_length=1,
    )
    time_limit: int = Field(
        default=TIME_LIMIT_PADRAO_SEGUNDOS,
        description=(
            "Tempo máximo de execução do solver em segundos "
            f"(padrão: {TIME_LIMIT_PADRAO_SEGUNDOS}, máximo: {TIME_LIMIT_MAXIMO_SEGUNDOS})."
        ),
        json_schema_extra={"examples": [60]},
    )

    @field_validator("comprimento_padrao")
    @classmethod
    def validar_comprimento_padrao_positivo(cls, valor: int) -> int:
        if valor <= 0:
            raise ValueError(
                "O comprimento padrão da barra deve ser estritamente maior que zero."
            )
        return valor

    @field_validator("time_limit")
    @classmethod
    def validar_time_limit(cls, valor: int) -> int:
        if valor < TIME_LIMIT_MINIMO_SEGUNDOS or valor > TIME_LIMIT_MAXIMO_SEGUNDOS:
            raise ValueError(
                f"O time_limit deve estar entre {TIME_LIMIT_MINIMO_SEGUNDOS} e "
                f"{TIME_LIMIT_MAXIMO_SEGUNDOS} segundos."
            )
        return valor

    @model_validator(mode="after")
    def validar_itens_cabem_na_barra(self) -> OtimizarInput:
        for item in self.itens:
            if item.comprimento > self.comprimento_padrao:
                raise ValueError(
                    f"O item '{item.id}' possui comprimento {item.comprimento} mm, "
                    f"que excede o comprimento padrão da barra "
                    f"({self.comprimento_padrao} mm). "
                    "Nenhum item individual pode ser maior que L."
                )
        return self


class ItemCortadoOutput(BaseModel):
    """Item alocado em uma barra."""

    item_id: str = Field(
        ...,
        description="Identificador do item cortado nesta barra.",
        json_schema_extra={"examples": ["item_A"]},
    )
    quantidade: int = Field(
        ...,
        description="Quantidade de peças deste item cortadas na barra.",
        json_schema_extra={"examples": [2]},
    )


class BarraPlanoOutput(BaseModel):
    """Detalhe de corte de uma barra utilizada."""

    barra_id: int = Field(
        ...,
        description="Índice sequencial da barra no plano final (1, 2, 3, ...).",
        json_schema_extra={"examples": [1]},
    )
    itens_cortados: list[ItemCortadoOutput] = Field(
        ...,
        description="Lista de itens cortados nesta barra (apenas quantidades > 0).",
    )
    comprimento_utilizado: int = Field(
        ...,
        description="Soma dos comprimentos das subpeças cortadas nesta barra (mm).",
        json_schema_extra={"examples": [2950]},
    )
    sobra: int = Field(
        ...,
        description="Comprimento não utilizado (desperdício) desta barra (mm).",
        json_schema_extra={"examples": [50]},
    )


class OtimizarOutput(BaseModel):
    """Resposta da otimização."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status_solver": "OPTIMAL",
                    "tempo_execucao_segundos": 0.17,
                    "barras_utilizadas": 4,
                    "desperdicio_total_mm": 3100,
                    "plano_corte": [
                        {
                            "barra_id": 1,
                            "itens_cortados": [
                                {"item_id": "item_A", "quantidade": 1}
                            ],
                            "comprimento_utilizado": 1150,
                            "sobra": 1850,
                        },
                        {
                            "barra_id": 2,
                            "itens_cortados": [
                                {"item_id": "item_A", "quantidade": 1},
                                {"item_id": "item_C", "quantidade": 4},
                            ],
                            "comprimento_utilizado": 2950,
                            "sobra": 50,
                        },
                        {
                            "barra_id": 3,
                            "itens_cortados": [
                                {"item_id": "item_B", "quantidade": 2},
                                {"item_id": "item_C", "quantidade": 1},
                            ],
                            "comprimento_utilizado": 2050,
                            "sobra": 950,
                        },
                        {
                            "barra_id": 4,
                            "itens_cortados": [
                                {"item_id": "item_A", "quantidade": 1},
                                {"item_id": "item_B", "quantidade": 2},
                            ],
                            "comprimento_utilizado": 2750,
                            "sobra": 250,
                        },
                    ],
                }
            ]
        }
    )

    status_solver: str = Field(
        ...,
        description="Status retornado pelo solver (ex.: OPTIMAL, FEASIBLE, INFEASIBLE).",
        json_schema_extra={"examples": ["OPTIMAL", "FEASIBLE", "INFEASIBLE"]},
    )
    tempo_execucao_segundos: float = Field(
        ...,
        description="Tempo físico de execução do solver em segundos.",
        json_schema_extra={"examples": [0.045]},
    )
    barras_utilizadas: int = Field(
        ...,
        description="Quantidade de barras padrão efetivamente utilizadas.",
        json_schema_extra={"examples": [4]},
    )
    desperdicio_total_mm: int = Field(
        ...,
        description="Soma do desperdício (sobras) de todas as barras utilizadas (mm).",
        json_schema_extra={"examples": [120]},
    )
    plano_corte: list[BarraPlanoOutput] = Field(
        ...,
        description="Plano de corte detalhado por barra ativamente utilizada.",
    )
