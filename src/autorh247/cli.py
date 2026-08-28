"""Interface de linha de comando (CLI) da aplicação AutoRH247."""

import argparse
import sys
from pathlib import Path
from autorh247.api.client import RH247Client
from autorh247.config import DEFAULT_CSV_PATH
from autorh247.core.processor import AbonoProcessor
from autorh247.core.validator import carregar_e_validar_csv


def comando_processar(args):
    """Executa o fluxo completo de abonos."""
    caminho = Path(args.arquivo) if args.arquivo else DEFAULT_CSV_PATH
    if not caminho.exists():
        print(f"[ERRO] Arquivo não encontrado: {caminho}")
        sys.exit(1)

    processador = AbonoProcessor()
    processador.processar_arquivo(caminho)


def comando_validar(args):
    """Apenas valida a estrutura do arquivo CSV sem enviar para a API."""
    caminho = Path(args.arquivo) if args.arquivo else DEFAULT_CSV_PATH
    if not caminho.exists():
        print(f"[ERRO] Arquivo não encontrado: {caminho}")
        sys.exit(1)

    print(f"[*] Validando arquivo: {caminho}")
    df = carregar_e_validar_csv(caminho)
    print("\n--- Resultado da Validação ---")
    print(df[["Nome Completo", "Data Inicial", "Data Final", "Status"]])
    total_erros = (df["Status"] == "ERRO").sum()
    print(f"\nTotal de linhas com erros estruturais: {total_erros}")


def comando_auth(args):
    """Testa ou força a renovação do token de acesso da API."""
    print("[*] Testando autenticação com a API RH247...")
    try:
        cliente = RH247Client()
        if args.renovar:
            print("[*] Forçando obtenção de novo token...")
            token = cliente.obter_novo_token()
        else:
            token = cliente.token
        print(f"[OK] Autenticacao realizada com sucesso! Token ativo: {token[:15]}...")
    except Exception as e:
        print(f"[ERRO] Falha ao autenticar: {e}")
        sys.exit(1)


def comando_buscar(args):
    """Pesquisa um funcionário por CPF ou nome e exibe os detalhes retornados pela API."""
    import re
    from autorh247.api.services import RH247Service

    identificador = args.identificador
    cpf_candidato = re.sub(r"\D", "", identificador)
    modo = "CPF" if len(cpf_candidato) == 11 else "Nome"

    print(f"[*] Pesquisando por {modo}: '{identificador}'...")
    try:
        service = RH247Service()
        resultados = service.buscar_funcionario(identificador)
        total = len(resultados)
        print(f"\n[OK] Total encontrado: {total} registro(s)\n")

        for idx, colab in enumerate(resultados, start=1):
            print(f"--- Colaborador #{idx} ---")
            print(f"  ID: {colab.get('id')}")
            print(f"  Nome: {colab.get('nome')}")
            print(f"  CPF: {colab.get('cpf_f') or colab.get('numero_cpf')}")
            print(f"  Matrícula: {colab.get('matricula')}")
            print(f"  Cargo: {colab.get('cargo_descricao')}")
            print(f"  Orgao / Empresa: {colab.get('orgao_descricao')}")
            print(f"  Status Ativo: {colab.get('ativo')}")
            print()
    except Exception as e:
        print(f"[ERRO] Falha ao pesquisar: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        prog="autorh247",
        description="AutoRH247 - Automação de Abono de Faltas via API do RH247",
    )
    subparsers = parser.add_subparsers(dest="comando", help="Comandos disponíveis")

    # Subcomando: buscar
    parser_buscar = subparsers.add_parser(
        "buscar", help="Pesquisa um funcionario por CPF ou nome e exibe dados da API"
    )
    parser_buscar.add_argument(
        "identificador",
        help="CPF (11 digitos, com ou sem formatacao) ou Nome completo do funcionario"
    )
    parser_buscar.set_defaults(func=comando_buscar)

    # Subcomando: processar
    parser_processar = subparsers.add_parser(
        "processar", help="Valida e executa o envio de abonos na API"
    )
    parser_processar.add_argument(
        "-a",
        "--arquivo",
        help="Caminho personalizado do arquivo CSV (padrão: data/justificativas.csv)",
        default=None,
    )
    parser_processar.set_defaults(func=comando_processar)

    # Subcomando: validar
    parser_validar = subparsers.add_parser(
        "validar", help="Apenas valida a estrutura do CSV sem disparar a API"
    )
    parser_validar.add_argument(
        "-a",
        "--arquivo",
        help="Caminho personalizado do arquivo CSV",
        default=None,
    )
    parser_validar.set_defaults(func=comando_validar)

    # Subcomando: auth
    parser_auth = subparsers.add_parser("auth", help="Verifica ou renova o token de acesso")
    parser_auth.add_argument(
        "--renovar",
        action="store_true",
        help="Força uma nova autenticação ignorando o token atual em cache",
    )
    parser_auth.set_defaults(func=comando_auth)

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
