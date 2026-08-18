"""Validador e sanitizador dos dados do arquivo CSV."""

from pathlib import Path
from typing import Union
import pandas as pd
from autor247.core.models import StatusAbono

COLUNAS_ESPERADAS = [
    "Status",
    "Nome Completo",
    "Data Inicial",
    "Data Final",
    "Descrição",
]


def carregar_e_validar_csv(caminho_arquivo: Union[str, Path]) -> pd.DataFrame:
    """Lê o arquivo CSV, sanitiza os dados e identifica erros estruturais."""
    df = pd.read_csv(caminho_arquivo, encoding="utf-8")

    # Garante a existência de todas as colunas esperadas
    for col in COLUNAS_ESPERADAS:
        if col not in df.columns:
            df[col] = ""

    df["Status"] = df["Status"].fillna("").astype(str).str.strip()
    df["Nome Completo"] = df["Nome Completo"].astype(str).str.strip().replace({"": pd.NA, "nan": pd.NA})
    df["Descrição"] = df["Descrição"].astype(str).str.strip().replace({"": pd.NA, "nan": pd.NA})

    # Regra: se Data Final estiver vazia, assume Data Inicial
    df["Data Final"] = df["Data Final"].fillna(df["Data Inicial"]).replace({"": pd.NA, "nan": pd.NA})
    df["Data Final"] = df["Data Final"].fillna(df["Data Inicial"])

    # Conversão de datas aceitando tanto DD/MM/YY quanto DD/MM/YYYY
    dt_inicial = pd.to_datetime(df["Data Inicial"], errors="coerce", format="%d/%m/%y")
    dt_inicial = dt_inicial.fillna(pd.to_datetime(df["Data Inicial"], errors="coerce", format="%d/%m/%Y"))

    dt_final = pd.to_datetime(df["Data Final"], errors="coerce", format="%d/%m/%y")
    dt_final = dt_final.fillna(pd.to_datetime(df["Data Final"], errors="coerce", format="%d/%m/%Y"))

    # Identifica erros estruturais
    erros_estruturais = (
        dt_inicial.isna()
        | dt_final.isna()
        | df["Descrição"].isna()
        | df["Nome Completo"].isna()
        | (dt_inicial > dt_final)
    )

    # Marca status de erro apenas para linhas pendentes/não finalizadas
    status_finalizados = (StatusAbono.OK.value, StatusAbono.DELETED.value)
    linhas_com_erro = erros_estruturais & (~df["Status"].isin(status_finalizados))
    df.loc[linhas_com_erro, "Status"] = StatusAbono.ERRO.value

    # Formata as datas válidas de volta para string no formato DD/MM/YYYY
    datas_validas_ini = dt_inicial.notna()
    datas_validas_fim = dt_final.notna()

    df.loc[datas_validas_ini, "Data Inicial"] = dt_inicial[datas_validas_ini].dt.strftime("%d/%m/%Y")
    df.loc[datas_validas_fim, "Data Final"] = dt_final[datas_validas_fim].dt.strftime("%d/%m/%Y")

    return df
