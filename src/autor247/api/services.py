import json
import re
from typing import Any, Dict, List, Optional
from autor247.api.client import RH247Client
from autor247.config import URL_DELETE, URL_JUSTIFY, URL_SEARCH


class RH247Service:
    """Implementa as operações de negócio consumindo os endpoints da API."""

    def __init__(self, client: Optional[RH247Client] = None):
        self.client = client or RH247Client()

    def _extrair_lista(self, response) -> List[Dict[str, Any]]:
        """Extrai a lista de colaboradores da resposta paginada da API."""
        dados = response.json()
        if isinstance(dados, dict):
            return dados.get("data", {}).get("data", [])
        elif isinstance(dados, list):
            return dados
        return []

    def buscar_por_nome(self, nome: str) -> List[Dict[str, Any]]:
        """Busca colaboradores pelo nome completo."""
        if not URL_SEARCH:
            raise ValueError("URL_SEARCH não configurada no .env")

        string_json = json.dumps({"nome": [nome]})
        response = self.client.get(f"{URL_SEARCH}descricao={string_json}")
        response.raise_for_status()
        return self._extrair_lista(response)

    def buscar_por_cpf(self, cpf: str) -> List[Dict[str, Any]]:
        """Busca colaboradores pelo CPF (apenas dígitos ou formatado com pontos/traço)."""
        if not URL_SEARCH:
            raise ValueError("URL_SEARCH não configurada no .env")

        # Normaliza o CPF mantendo apenas dígitos
        cpf_limpo = re.sub(r"\D", "", cpf)
        string_json = json.dumps({"cpf": [cpf_limpo]})
        response = self.client.get(f"{URL_SEARCH}descricao={string_json}")
        response.raise_for_status()
        return self._extrair_lista(response)

    def buscar_funcionario(self, identificador: str) -> List[Dict[str, Any]]:
        """Busca colaboradores detectando automaticamente se o identificador é CPF ou nome.

        - Se o identificador contiver apenas dígitos e pontuação de CPF (11 dígitos no total),
          usa busca por CPF.
        - Caso contrário, usa busca por nome completo.
        """
        cpf_candidato = re.sub(r"\D", "", identificador)
        if len(cpf_candidato) == 11:
            return self.buscar_por_cpf(cpf_candidato)
        return self.buscar_por_nome(identificador)


    def enviar_abono(
        self,
        id_colaborador: Any,
        data_inicio: str,
        data_fim: str,
        motivo: str,
    ) -> Dict[str, Any]:
        """Envia requisição POST para registrar o abono/atestado no sistema."""
        if not URL_JUSTIFY:
            raise ValueError("URL_JUSTIFY não configurada no .env")

        payload = {
            "descricao_add_atestado_main": motivo,
            "data_inicial_add_atestado_main": data_inicio,
            "data_final_add_atestado_main": data_fim,
            "fv_alteracao_escala_main": id_colaborador,
        }

        response = self.client.post(URL_JUSTIFY, json=payload)
        response.raise_for_status()
        return response.json() if response.content else {}

    def remover_abono_dia(
        self,
        id_colaborador: Any,
        data_iso: str,
    ) -> Dict[str, Any]:
        """Envia requisição DELETE para remover observação/abono do dia especificado.

        :param id_colaborador: ID do colaborador (ex: 18434)
        :param data_iso: Data no formato YYYY-MM-DD (ex: '2026-08-01')
        """
        if not URL_DELETE:
            raise ValueError("URL_DELETE não configurada no .env")

        params = {
            "funcionario_vinculo_id": id_colaborador,
            "data": data_iso,
        }

        response = self.client.delete(URL_DELETE, params=params)
        response.raise_for_status()
        return response.json() if response.content else {}
