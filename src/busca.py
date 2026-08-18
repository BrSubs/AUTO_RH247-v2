#PESQUISAR UM FUNCIONARIO PELO NOME COMPLETO USANDO URL_SEARCH DO .env E CAPTURAR SEU ID
#USAR O ID PARA COMPLEMENTAR O JSON ENVIADO ATRAVES DO POST URL_JUSTIFY DO .env

import dotenv, os, json, requests
from autenticar_sessao import autenticar_sessao
dotenv.load_dotenv()

s = autenticar_sessao()

def buscar_funcionario(nome):
    url_search = os.getenv("URL_SEARCH")

    json_interno = {"nome":[nome]}

    string_json = json.dumps(json_interno)

    url_composta = f"{url_search}descricao={string_json}"

    response = s.get(url_composta)
    response.raise_for_status()

    dados_funcionario = response.json()

    return dados_funcionario

print(buscar_funcionario("YAN BRASIL ANGELIM DE BRITO"))