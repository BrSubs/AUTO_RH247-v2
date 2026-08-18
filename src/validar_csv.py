import pandas as pd

caminho_arquivo = "justificativas.csv"

def validar_csv(caminho_arquivo):

    df = pd.read_csv(caminho_arquivo, encoding="utf-8")

    colunas = [
        "Status",
        "Nome Completo",
        "Data Inicial",
        "Data Final",
        "Descrição",
    ]

    df["Status"] = df["Status"].fillna("")

    df["Nome Completo"] = df["Nome Completo"].str.strip().replace({"": pd.NA})
    df["Descrição"] = df["Descrição"].str.strip().replace({"": pd.NA})

    df["Data Final"] = df["Data Final"].fillna( df["Data Inicial"] )

    df['Data Inicial'] = pd.to_datetime(df['Data Inicial'], errors='coerce', format='%d/%m/%y')
    df['Data Final'] = pd.to_datetime(df['Data Final'], errors='coerce', format='%d/%m/%y')

    erros = df['Data Inicial'].isna() | df['Data Final'].isna() | (df['Descrição'].isna()) | (df['Nome Completo'].isna()) | (df['Data Inicial'] > df['Data Final'])

    df.loc[erros,"Status"] = "ERRO"

    df['Data Inicial'] = df['Data Inicial'].dt.strftime('%d/%m/%Y')
    df['Data Final'] = df['Data Final'].dt.strftime('%d/%m/%Y')

    return df

print(validar_csv(caminho_arquivo))