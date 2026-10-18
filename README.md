# API de Otimização — Problema de Corte Unidimensional

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688?logo=fastapi&logoColor=white)
![OR-Tools](https://img.shields.io/badge/OR--Tools-9.8+-4285F4?logo=google&logoColor=white)
![pytest](https://img.shields.io/badge/pytest-8.0+-0A9EDC?logo=pytest&logoColor=white)

**Optimization-as-a-Service (OaaS)** para o Problema de Corte de Estoque Unidimensional, desenvolvido em Python com FastAPI e Google OR-Tools.

---

## 🌐 Implantação em Produção (Optimization-as-a-Service)

| Recurso | URL |
|---------|-----|
| **API** | https://corte-unidimensional-api.onrender.com |
| **Swagger UI** | https://corte-unidimensional-api.onrender.com/docs |
| **Health check** | https://corte-unidimensional-api.onrender.com/health |

---

## ⚙️ Descrição

O **Problema de Corte Unidimensional** (CSP 1D) consiste em determinar como cortar barras padrão de comprimento $L$ para atender demandas $d_i$ de subpeças com comprimentos $l_i$, **minimizando o número de barras utilizadas** e, consequentemente, o desperdício de material.

Esta API expõe esse problema como serviço REST: o cliente envia a instância em JSON e recebe o plano de corte otimizado.

---

## 📊 Formulação Matemática (Kantorovich)

Modelo de **programação inteira mista (MIP)** resolvido pelo solver **SCIP** (Google OR-Tools).

### Conjuntos e parâmetros

| Símbolo | Descrição |
|---------|-----------|
| $i \in \{1, \dots, m\}$ | Tipos de item demandados |
| $j \in \{1, \dots, N\}$ | Barras candidatas, com $N = \sum d_i$ |
| $L$ | Comprimento útil da barra padrão (mm) |
| $l_i$ | Comprimento da subpeça $i$ (mm) |
| $d_i$ | Quantidade demandada do item $i$ |

### Variáveis de decisão

| Variável | Domínio | Descrição |
|----------|---------|-----------|
| $y_j$ | $\{0, 1\}$ | 1 se a barra $j$ é utilizada |
| $x_{ij}$ | $\mathbb{Z}_{\ge 0}$ | Quantidade do item $i$ cortada na barra $j$ |

### Modelo

**Objetivo:**

$$
\min \quad Z = \sum_{j=1}^{N} y_j
$$

**Sujeito a:**

*Atendimento mínimo da demanda* — garante que toda a demanda mínima exigida para cada item de subpeça seja plenamente suprida:

$$
\sum_{j=1}^{N} x_{ij} \ge d_i \quad \forall \, i \in \{1, \dots, m\}
$$

*Capacidade física da barra:*

$$
\sum_{i=1}^{m} l_i \, x_{ij} \leq L \, y_j \quad \forall \, j \in \{1, \dots, N\}
$$

*Domínio:* $y_j \in \{0, 1\}$, $x_{ij} \in \mathbb{Z}_{\ge 0}$

---

## 📁 Estrutura do Projeto

```
.
├── src/
│   ├── __init__.py         # Pacote da aplicação
│   ├── api.py              # Rotas FastAPI (/health, /otimizar)
│   ├── auth.py             # Validação da API Key (X-API-Key)
│   ├── config.py           # Carregamento de variáveis do .env
│   ├── schemas.py          # Contratos Pydantic de entrada e saída
│   └── solver.py           # Modelo de Kantorovich (OR-Tools / SCIP)
├── tests/
│   ├── test_api.py         # Testes de integração (8 cenários)
│   └── test_solver.py      # Testes unitários do solver (6 cenários)
├── .env.example            # Modelo de variáveis de ambiente
├── .gitignore              # Exclusões do controle de versão
├── api_requests.http       # Requisições para REST Client (VS Code)
├── investigacao.md         # Levantamento técnico do projeto
├── pytest.ini              # Configuração do pytest (pythonpath)
├── requirements.txt        # Dependências Python
└── README.md
```

| Arquivo / Pasta | Propósito |
|-----------------|-----------|
| `src/` | Código-fonte da API e do motor de otimização |
| `tests/` | Suíte automatizada com 14 cenários de teste |
| `requirements.txt` | Dependências para instalação via `pip` |
| `.env.example` | Referência das variáveis de ambiente necessárias |
| `.gitignore` | Impede versionamento de segredos, caches e `.venv` |
| `pytest.ini` | Garante resolução correta do pacote `src` nos testes |
| `api_requests.http` | Testes manuais rápidos com a extensão REST Client |

---

## 🚀 Instalação

**Pré-requisitos:** Python 3.12+, pip

```bash
git clone <url-do-repositorio>
cd corte-unidimensional-api

python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

Edite `.env` e defina sua chave:

```env
API_KEY=chave_da_api
```

---

## 🖥️ Execução Local

```bash
uvicorn src.api:app --reload
```

| Interface | URL |
|-----------|-----|
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Health check | http://localhost:8000/health |

---

## 🛡️ Endpoints

### `GET /health` — público

```json
{ "status": "healthy" }
```

### `POST /otimizar` — protegido

Requer o cabeçalho `X-API-Key`.

**Requisição (instância de referência):**

```json
{
  "comprimento_padrao": 3000,
  "itens": [
    { "id": "item_A", "comprimento": 1150, "quantidade": 3 },
    { "id": "item_B", "comprimento": 800, "quantidade": 4 },
    { "id": "item_C", "comprimento": 450, "quantidade": 5 }
  ],
  "time_limit": 60
}
```

**Resposta (`200 OK`):**

```json
{
  "status_solver": "OPTIMAL",
  "tempo_execucao_segundos": 0.17,
  "barras_utilizadas": 4,
  "desperdicio_total_mm": 3100,
  "plano_corte": [
    {
      "barra_id": 1,
      "itens_cortados": [{ "item_id": "item_A", "quantidade": 1 }],
      "comprimento_utilizado": 1150,
      "sobra": 1850
    },
    {
      "barra_id": 2,
      "itens_cortados": [
        { "item_id": "item_A", "quantidade": 1 },
        { "item_id": "item_C", "quantidade": 4 }
      ],
      "comprimento_utilizado": 2950,
      "sobra": 50
    },
    {
      "barra_id": 3,
      "itens_cortados": [
        { "item_id": "item_B", "quantidade": 2 },
        { "item_id": "item_C", "quantidade": 1 }
      ],
      "comprimento_utilizado": 2050,
      "sobra": 950
    },
    {
      "barra_id": 4,
      "itens_cortados": [
        { "item_id": "item_A", "quantidade": 1 },
        { "item_id": "item_B", "quantidade": 2 }
      ],
      "comprimento_utilizado": 2750,
      "sobra": 250
    }
  ]
}
```

| Código | Situação |
|--------|----------|
| `200` | Otimização concluída |
| `403` | API Key ausente ou inválida |
| `422` | Payload inválido |
| `500` | Erro interno no solver |

---

## 🧪 Testes

```bash
pytest -v
```

| Suíte | Arquivo | Cenários |
|-------|---------|----------|
| Integração | `tests/test_api.py` | 8 |
| Unitário | `tests/test_solver.py` | 6 |
| **Total** | | **14** |

---

## 📚 Stack

| Camada | Tecnologia |
|--------|------------|
| API | FastAPI + Uvicorn |
| Otimização | Google OR-Tools (MIP / SCIP) |
| Validação | Pydantic v2 |
| Segurança | API Key (`X-API-Key`) |
| Testes | pytest + httpx |
| Configuração | python-dotenv |

---

Desenvolvido por Isaack Nyllo para a disciplina de Laboratório de Otimização (UFC). Organização do repositório com apoio de IA.
