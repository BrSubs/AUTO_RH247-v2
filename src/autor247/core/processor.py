"""Orquestrador do processamento de abonos linha a linha."""

from pathlib import Path
from typing import Optional, Union
import pandas as pd
from requests.exceptions import RequestException, Timeout
from autor247.api.services import RH247Service
from autor247.core.models import StatusAbono
from autor247.core.validator import carregar_e_validar_csv


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
            if status_atual in (StatusAbono.OK.value, StatusAbono.DELETED.value, StatusAbono.ERRO.value):
                continue

            eh_remocao = status_atual == StatusAbono.DELETE.value
            acao_str = "Removendo abono" if eh_remocao else "Processando abono"

            nome = row["Nome Completo"]
            data_ini = row["Data Inicial"]
            data_fim = row["Data Final"]
            motivo = row["Descrição"]

            print(f"[{index + 1}/{total_linhas}] {acao_str}: {nome} ({data_ini} ate {data_fim})...")

            try:
                # 1. Busca funcionário na API
                colaboradores = self.service.buscar_funcionario(nome)

                if len(colaboradores) == 0:
                    df.at[index, "Status"] = StatusAbono.NOT_FOUND.value
                    print(f"    -> Status: {StatusAbono.NOT_FOUND.value}")
                    continue

                if len(colaboradores) > 1:
                    df.at[index, "Status"] = StatusAbono.MULTIPLE_CHOICES.value
                    print(f"    -> Status: {StatusAbono.MULTIPLE_CHOICES.value}")
                    continue

                # Extrai o ID do colaborador retornado pela API
                colaborador = colaboradores[0]
                id_colaborador = colaborador.get("fv_alteracao_escala_main") or colaborador.get("id")

                if not id_colaborador:
                    df.at[index, "Status"] = StatusAbono.ERRO.value
                    print("    -> Erro: ID do colaborador não encontrado no retorno da API")
                    continue

                # 2. Executa a Ação (Exclusão ou Inserção)
                if eh_remocao:
                    # Gera a lista de dias entre data_ini e data_fim para remover dia a dia
                    intervalo_datas = pd.date_range(
                        start=pd.to_datetime(data_ini, format="%d/%m/%Y"),
                        end=pd.to_datetime(data_fim, format="%d/%m/%Y"),
                    )
                    for data_dt in intervalo_datas:
                        data_iso = data_dt.strftime("%Y-%m-%d")
                        self.service.remover_abono_dia(
                            id_colaborador=id_colaborador,
                            data_iso=data_iso,
                        )
                    df.at[index, "Status"] = StatusAbono.DELETED.value
                    print(f"    -> Status: {StatusAbono.DELETED.value}")
                else:
                    self.service.enviar_abono(
                        id_colaborador=id_colaborador,
                        data_inicio=data_ini,
                        data_fim=data_fim,
                        motivo=motivo,
                    )
                    df.at[index, "Status"] = StatusAbono.OK.value
                    print(f"    -> Status: {StatusAbono.OK.value}")

            except Timeout:
                df.at[index, "Status"] = StatusAbono.TIMEOUT.value
                print(f"    -> Status: {StatusAbono.TIMEOUT.value}")
            except RequestException as e:
                df.at[index, "Status"] = StatusAbono.ERRO.value
                print(f"    -> Erro na requisição: {e}")
            except Exception as e:
                df.at[index, "Status"] = StatusAbono.ERRO.value
                print(f"    -> Erro inesperado: {e}")

        # 3. Salva o CSV atualizado em disco
        df.to_csv(caminho_csv, index=False, encoding="utf-8")
        print(f"[OK] Arquivo {caminho_csv.name} atualizado com sucesso!")
        return df
