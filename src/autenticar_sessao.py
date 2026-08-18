import os
from pathlib import Path
import requests
from dotenv import load_dotenv, set_key

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

s = requests.Session()

#função para verificar se existe um token salvo no .env
def autenticar_sessao():
    token = os.getenv("TOKEN_API")

    if not token:
        token = obter_token()

    s.headers.update({"Authorization": token})
    return s

#função para obter token
def obter_token():
    login_usuario = os.getenv("API_LOGIN")
    senha_usuario = os.getenv("API_SENHA")
    url_auth = os.getenv("URL_AUTH")

    payload = {"login": login_usuario, "senha": senha_usuario}

    response = s.post(url_auth, json=payload)
    response.raise_for_status()

    dados_resposta = response.json()
    novo_token = dados_resposta.get("token")

    if novo_token:
        set_key(env_path, "TOKEN_API", novo_token)
        os.environ["TOKEN_API"] = novo_token
    
    return novo_token

autenticar_sessao()