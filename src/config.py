"""Configuração da aplicação via variáveis de ambiente."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

API_KEY: str = os.environ["API_KEY"]
