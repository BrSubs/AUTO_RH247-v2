"""Orquestrador do processamento de abonos linha a linha."""

from pathlib import Path
from typing import Optional, Union
import unicodedata
import pandas as pd
from requests.exceptions import RequestException, Timeout
from autorh247.api.services import RH247Service
from autorh247.core.models import StatusAbono
from autorh247.core.validator import carregar_e_validar_csv


class AbonoProcessor:
    """Executa o ciclo completo de abono de faltas."""

    def __init__(self, service: Optional[RH247Service] = None):
        self.service = service or RH247Service()

    def processar_arquivo(self, caminho_csv: Union[str, Path]) -> pd.DataFrame:
        """Executa a validação, consulta a API e persiste o resultado no arquivo CSV."""
        caminho_csv = Path(caminho_csv)
        print(f"[*] Carregando e validando: {caminho_csv.name}")
        df = carregar_e_validar_csv(caminho_csv)

        total_linhas = len(df)
        print(f"[*] Total de registros: {total_linhas}")

        for index, row in df.iterrows():
            status_atual = str(row["Status"]).strip()

            # Pula registros já concluídos com sucesso ou que falharam na validação inicial
            if status_atual in (
                StatusAbono.OK.value,
                StatusAbono.DELETED.value,
                StatusAbono.CONFLITO.value,
                StatusAbono.ERRO.value,
            ):
                continue

            self._processar_linha(df, index, row, total_linhas)

        # 3. Salva o CSV atualizado em disco
        df.to_csv(caminho_csv, index=False, encoding="utf-8")
        print(f"[OK] Arquivo {caminho_csv.name} atualizado com sucesso!")
        return df

    def _processar_linha(
        self,
        df: pd.DataFrame,
        index: int,
        row: pd.Series,
        total_linhas: int,
    ) -> None:
        """Processa uma linha e atualiza seu status no DataFrame."""
        eh_remocao = str(row["Status"]).strip() == StatusAbono.DELETE.value
        acao_str = "Removendo abono" if eh_remocao else "Processando abono"
        nome = row["Nome Completo"]
        data_ini = row["Data Inicial"]
        data_fim = row["Data Final"]
        motivo = row["Descrição"]

        print(f"[{index + 1}/{total_linhas}] {acao_str}: {nome} ({data_ini} ate {data_fim})...")

        try:
            id_colaborador, status_busca = self._buscar_id_colaborador(nome)
            if status_busca:
                df.at[index, "Status"] = status_busca
                print(f"    -> Status: {status_busca}")
                return

            if eh_remocao:
                self._remover_intervalo(id_colaborador, data_ini, data_fim)
                novo_status = StatusAbono.DELETED.value
            else:
                self.service.enviar_abono(id_colaborador, data_ini, data_fim, motivo)
                novo_status = StatusAbono.OK.value

            df.at[index, "Status"] = novo_status
            print(f"    -> Status: {novo_status}")
        except Timeout:
            df.at[index, "Status"] = StatusAbono.TIMEOUT.value
            print(f"    -> Status: {StatusAbono.TIMEOUT.value}")
        except RequestException as e:
            if self._resposta_indica_conflito(e):
                df.at[index, "Status"] = StatusAbono.CONFLITO.value
                print(f"    -> Status: {StatusAbono.CONFLITO.value}")
            else:
                df.at[index, "Status"] = StatusAbono.ERRO.value
                print(f"    -> Erro na requisição: {e}")
        except Exception as e:
            df.at[index, "Status"] = StatusAbono.ERRO.value
            print(f"    -> Erro inesperado: {e}")

    @staticmethod
    def _resposta_indica_conflito(erro: RequestException) -> bool:
        """Identifica o conflito de período informado pela API como HTTP 400."""
        resposta = getattr(erro, "response", None)
        if getattr(resposta, "status_code", None) != 400:
            return False

        try:
            payload = resposta.json()
        except (AttributeError, ValueError):
            return False

        if not isinstance(payload, dict):
            return False

        mensagens = [payload.get(campo, "") for campo in ("msg", "message", "msg_err", "message_erro")]
        texto = " ".join(valor for valor in mensagens if isinstance(valor, str))
        texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()
        return "periodo conflitante" in texto

    def _buscar_id_colaborador(self, identificador: str):
        """Retorna o ID e um status quando a busca nao pode continuar."""
        colaboradores = self.service.buscar_funcionario(identificador)
        if not colaboradores:
            return None, StatusAbono.NOT_FOUND.value
        if len(colaboradores) > 1:
            return None, StatusAbono.MULTIPLE_CHOICES.value

        colaborador = colaboradores[0]
        id_colaborador = colaborador.get("fv_alteracao_escala_main") or colaborador.get("id")
        if not id_colaborador:
            raise ValueError("ID do colaborador não encontrado no retorno da API")
        return id_colaborador, None

    def _remover_intervalo(self, id_colaborador, data_ini: str, data_fim: str) -> None:
        """Remove o abono de cada dia do intervalo informado."""
        intervalo_datas = pd.date_range(
            start=pd.to_datetime(data_ini, format="%d/%m/%Y"),
            end=pd.to_datetime(data_fim, format="%d/%m/%Y"),
        )
        for data_dt in intervalo_datas:
            self.service.remover_abono_dia(
                id_colaborador=id_colaborador,
                data_iso=data_dt.strftime("%Y-%m-%d"),
            )
