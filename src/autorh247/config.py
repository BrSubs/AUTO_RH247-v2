"""Centralização de configurações, diretórios e variáveis de ambiente."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Diretórios principais do projeto
if getattr(sys, "frozen", False):
	BASE_DIR = Path(sys.executable).resolve().parent
else:
	BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
ENV_PATH = BASE_DIR / ".env"

# Carrega o .env a partir da raiz do projeto
load_dotenv(dotenv_path=ENV_PATH)

# Credenciais e URLs da API RH247
API_LOGIN = os.getenv("API_LOGIN")
API_SENHA = os.getenv("API_SENHA")
TOKEN_API = os.getenv("TOKEN_API")

URL_AUTH = os.getenv("URL_AUTH")
URL_SEARCH = os.getenv("URL_SEARCH")
URL_ID = os.getenv("URL_ID")
URL_JUSTIFY = os.getenv("URL_JUSTIFY")
URL_DELETE = os.getenv("URL_DELETE")

# Caminho padrão dos dados
DEFAULT_CSV_PATH = DATA_DIR / "justificativas.csv"
