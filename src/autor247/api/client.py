"""Cliente HTTP para autenticação e gerenciamento de sessão na API RH247."""

import os
import requests
from dotenv import set_key
from autor247.config import (
    API_LOGIN,
    API_SENHA,
    ENV_PATH,
    TOKEN_API,
    URL_AUTH,
)


class RH247Client:
    """Gerencia a sessão autenticada com a API do RH247."""

    def __init__(self):
        self.session = requests.Session()
        self.token = TOKEN_API
        self._inicializar_autenticacao()

    def _inicializar_autenticacao(self):
        """Garante que a sessão tenha um token válido configurado no Header."""
        if not self.token:
            self.token = self.obter_novo_token()
        self.session.headers.update({"Authorization": self.token})

    def obter_novo_token(self) -> str:
        """Autentica na API com login/senha e atualiza o .env com o novo token."""
        if not API_LOGIN or not API_SENHA or not URL_AUTH:
            raise ValueError(
                "As variáveis API_LOGIN, API_SENHA e URL_AUTH devem estar configuradas no .env"
            )

        payload = {"login": API_LOGIN, "senha": API_SENHA}
        response = self.session.post(URL_AUTH, json=payload, timeout=30)
        response.raise_for_status()

        dados = response.json()
        novo_token = dados.get("token")

        if not novo_token:
            raise ValueError("A resposta de autenticação não retornou um campo 'token'.")

        # Atualiza o arquivo .env e o ambiente em memória
        set_key(str(ENV_PATH), "TOKEN_API", novo_token)
        os.environ["TOKEN_API"] = novo_token
        self.token = novo_token
        return novo_token

    def get(self, url: str, **kwargs):
        """Wrapper para requisições GET com a sessão configurada."""
        kwargs.setdefault("timeout", 30)
        return self.session.get(url, **kwargs)

    def post(self, url: str, **kwargs):
        """Wrapper para requisições POST com a sessão configurada."""
        kwargs.setdefault("timeout", 30)
        return self.session.post(url, **kwargs)

    def delete(self, url: str, **kwargs):
        """Wrapper para requisições DELETE com a sessão configurada."""
        kwargs.setdefault("timeout", 30)
        return self.session.delete(url, **kwargs)
