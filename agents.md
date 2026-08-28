# AutoRH247 - Documentacao Tecnica do Projeto

Este documento descreve a arquitetura, a estrutura, as ferramentas, as funcoes,
o contrato de dados e o fluxo de execucao do AutoRH247.

O AutoRH247 e uma aplicacao Python de linha de comando. Ela le um CSV de
justificativas, valida e normaliza os dados, consulta colaboradores na API do
RH247, inclui ou remove abonos e grava o resultado no proprio CSV.

## 1. Tecnologias e ferramentas

- Python 3.11 ou superior.
- `uv`: gerencia o ambiente, dependencias e a entrada da CLI.
- `pandas`: le, transforma, valida e grava CSVs.
- `requests`: executa requisicoes HTTP e mantem uma `Session` autenticada.
- `python-dotenv`: carrega o `.env` e persiste o token renovado.
- `argparse`: implementa subcomandos e argumentos da CLI.
- `pathlib.Path`: manipula caminhos de arquivos.
- `json` e `re`: montam filtros da API e normalizam CPFs.
- `enum.Enum`: concentra os status do dominio.
- `typing`: fornece anotacoes de tipos.

Instalacao e sincronizacao:

```powershell
uv sync
```

Execucao:

```powershell
uv run autorh247 <comando> [opcoes]
```

O ponto de entrada esta definido em `pyproject.toml`:

```text
autorh247 = autorh247.cli:main
```

## 2. Estrutura do repositorio

```text
AUTO_RH247-v2/
├── agents.md
├── README.md
├── autoRH247.bat
├── pyproject.toml
├── data/
│   ├── justificativas.csv
│   └── justificativas.example.csv
└── src/
    └── autorh247/
        ├── __init__.py
        ├── cli.py
        ├── config.py
        ├── api/
        │   ├── __init__.py
        │   ├── client.py
        │   └── services.py
        └── core/
            ├── __init__.py
            ├── models.py
            ├── processor.py
            └── validator.py
```

O arquivo `autoRH247.bat` na raiz e um atalho clicavel que oferece um menu
textual com busca, validacao, processamento e acesso a interface grafica.

Testes unitarios:

```text
tests/
├── unit/
│   ├── api/test_services.py
│   └── core/test_processor.py
```

### Responsabilidade dos modulos

- `cli.py`: interpreta comandos, valida caminhos e apresenta resultados.
- `config.py`: define caminhos e carrega configuracoes do ambiente.
- `api/client.py`: encapsula sessao HTTP e autenticacao.
- `api/services.py`: implementa operacoes especificas da API RH247.
- `core/models.py`: define os status do dominio.
- `core/validator.py`: transforma o CSV em um `DataFrame` consistente.
- `core/processor.py`: coordena validacao, busca, inclusao/remocao e persistencia.

## 3. Arquitetura e fluxo

O projeto possui tres camadas:

1. **Interface**: `cli.py` recebe a intencao do usuario.
2. **Dominio**: `validator.py`, `models.py` e `processor.py` aplicam regras.
3. **Integracao**: `client.py` e `services.py` comunicam-se com a API.

Fluxo do processamento:

```text
CLI processar
  -> AbonoProcessor.processar_arquivo
  -> carregar_e_validar_csv
  -> RH247Service.buscar_funcionario
  -> [0 resultados: NOT FOUND]
  -> [mais de 1: MULTIPLE CHOICES]
  -> [1 resultado: extrai ID]
  -> DELETE por dia ou POST de abono
  -> atualiza Status
  -> salva o CSV
```

`AbonoProcessor` aceita um `RH247Service` opcional, permitindo injetar um mock
em testes.

## 4. Configuracao e autenticacao

`config.py` calcula a raiz do projeto a partir de `src/autorh247`, define `data/`
como diretorio de dados e carrega `.env` na raiz.

Variaveis de ambiente:

| Variavel | Uso |
| --- | --- |
| `API_LOGIN` | Login da API |
| `API_SENHA` | Senha da API |
| `TOKEN_API` | Token reutilizado entre execucoes |
| `URL_AUTH` | Endpoint de autenticacao |
| `URL_SEARCH` | URL base da busca de colaboradores |
| `URL_ID` | Reservada; atualmente nao utilizada |
| `URL_JUSTIFY` | Endpoint de inclusao de abono |
| `URL_DELETE` | Endpoint de remocao diaria |

O `RH247Client` reutiliza `TOKEN_API`. Sem token, faz login em `URL_AUTH`,
extrai `token`, salva o valor no `.env` e atualiza o ambiente em memoria. O
token e instalado no header `Authorization` da sessao.

## 5. Contrato do CSV

O codigo espera estas colunas, com grafia exata:

| Coluna | Obrigatoria para processar | Regra |
| --- | --- | --- |
| `Status` | Nao | Controla a acao e recebe o resultado |
| `Nome Completo` | Sim | Nome ou identificador consultado |
| `Data Inicial` | Sim | `DD/MM/YY` ou `DD/MM/YYYY` |
| `Data Final` | Nao | Vazia: recebe `Data Inicial` |
| `Descrição` | Sim | Motivo do abono |

O nome da coluna inclui o acento e precisa ser mantido exatamente assim.
Colunas ausentes sao criadas vazias e tendem a produzir `ERRO` nas linhas.

Status:

- vazio: inclui um abono;
- `DELETE`: remove o abono dia a dia no intervalo;
- `OK`: inclusao concluida; nao processa novamente;
- `DELETED`: remocao concluida; nao processa novamente;
- `ERRO`: erro estrutural ou falha geral; nao processa novamente;
- `NOT FOUND`: nenhum colaborador encontrado;
- `MULTIPLE CHOICES`: mais de um colaborador encontrado;
- `TIMEOUT`: requisicao excedeu o limite;
- `CONFLITO`: definido no modelo, mas nao produzido atualmente pelo fluxo.

Linhas `NOT FOUND` e `MULTIPLE CHOICES` podem ser tentadas novamente, pois o
processador ignora somente `OK`, `DELETED` e `ERRO`.

## 6. Funcoes, classes e ferramentas por modulo

### `autorh247.cli`

- `comando_processar(args)`: resolve o CSV, verifica existencia, cria
  `AbonoProcessor` e inicia `processar_arquivo`.
- `comando_validar(args)`: chama `carregar_e_validar_csv`, exibe dados e conta
  linhas com `ERRO` sem acessar a API.
- `comando_auth(args)`: cria `RH247Client`, reutiliza o token ou chama
  `obter_novo_token` quando `--renovar`.
- `comando_buscar(args)`: detecta CPF ou nome, consulta o servico e imprime os
  dados dos colaboradores retornados.
- `main()`: configura `argparse`, registra subcomandos e despacha a funcao.

Comandos:

```powershell
uv run autorh247 buscar "NOME DO FUNCIONARIO"
uv run autorh247 validar
uv run autorh247 validar -a data/justificativas.example.csv
uv run autorh247 processar
uv run autorh247 processar -a data/justificativas.csv
uv run autorh247 auth
uv run autorh247 auth --renovar
```

### `autorh247.gui`

- `AutoRH247App(root)`: cria a janela, os controles e a area de resultados.
- `_criar_widgets()`: monta campos de busca, selecao de planilha, botoes e
  saida de resultados.
- `_escrever(texto)`: atualiza a area de resultados com seguranca.
- `_executar_em_background(nome, funcao)`: executa operacoes potencialmente
  demoradas em uma thread e mantém a interface responsiva.
- `_finalizar(nome, resultado)`: exibe resultado de uma operacao concluida.
- `_finalizar_erro(nome, erro)`: exibe erro e reativa os controles.
- `_habilitar_botoes()`: reativa os botoes da janela.
- `selecionar_arquivo()`: abre o seletor de arquivos CSV.
- `buscar()`: consulta funcionario por nome ou CPF.
- `validar()`: valida a planilha sem acessar a API.
- `processar()`: confirma e executa o processamento da planilha.
- `main()`: cria a janela Tkinter e inicia o loop grafico.

### `autorh247.config`

Nao possui funcoes publicas. Na importacao, inicializa `BASE_DIR`, `DATA_DIR`,
`ENV_PATH`, credenciais, URLs e `DEFAULT_CSV_PATH`.

### `autorh247.api.client`

Classe `RH247Client`:

- `__init__()`: cria `requests.Session`, carrega token e inicia autenticacao.
- `_inicializar_autenticacao()`: obtem token quando necessario e configura o
  header `Authorization`.
- `obter_novo_token()`: valida configuracao, faz `POST` em `URL_AUTH`, exige
  sucesso, extrai `token` e atualiza `.env`.
- `get(url, **kwargs)`: wrapper de `Session.get` com timeout padrao de 30s.
- `post(url, **kwargs)`: wrapper de `Session.post` com timeout padrao de 30s.
- `delete(url, **kwargs)`: wrapper de `Session.delete` com timeout padrao de 30s.

### `autorh247.api.services`

Classe `RH247Service`:

- `__init__(client=None)`: usa o cliente fornecido ou cria `RH247Client`.
- `_extrair_lista(response)`: extrai colaboradores de uma lista direta ou do
  formato paginado `data.data`.
- `buscar_por_nome(nome)`: faz `GET` em `URL_SEARCH` com filtro JSON por nome.
- `buscar_por_cpf(cpf)`: remove pontuacao e faz `GET` com filtro por CPF.
- `buscar_funcionario(identificador)`: usa CPF quando ha 11 digitos; caso
  contrario, usa busca por nome.
- `enviar_abono(id_colaborador, data_inicio, data_fim, motivo)`: envia `POST`
  para `URL_JUSTIFY` e retorna o JSON da resposta.
- `remover_abono_dia(id_colaborador, data_iso)`: envia `DELETE` para `URL_DELETE`
  com o ID e a data no formato `YYYY-MM-DD`.

Payload de inclusao:

```json
{
  "descricao_add_atestado_main": "motivo",
  "data_inicial_add_atestado_main": "DD/MM/YYYY",
  "data_final_add_atestado_main": "DD/MM/YYYY",
  "fv_alteracao_escala_main": "id do colaborador"
}
```

### `autorh247.core.models`

`StatusAbono` e um `Enum` baseado em `str`, com os valores `OK`, `ERRO`,
`NOT FOUND`, `MULTIPLE CHOICES`, `CONFLITO`, `TIMEOUT`, `DELETE`, `DELETED` e
`PENDENTE` (string vazia).

### `autorh247.core.validator`

- `carregar_e_validar_csv(caminho_arquivo)`: le o CSV UTF-8; cria colunas
  esperadas ausentes; limpa textos; completa `Data Final`; interpreta datas;
  identifica campos vazios e intervalos invertidos; marca `ERRO`; formata datas
  validas como `DD/MM/YYYY`; retorna um `pandas.DataFrame`.

Datas invalidas tornam-se `NaT`. Nome, descricao, data inicial e data final
invalidos tornam a linha estruturalmente invalida.

### `autorh247.core.processor`

Classe `AbonoProcessor`:

- `__init__(service=None)`: injeta ou cria o servico da API.
- `processar_arquivo(caminho_csv)`: valida o arquivo, percorre linhas, ignora
  status finais, busca o colaborador, extrai
  `fv_alteracao_escala_main` ou `id`, inclui ou remove o abono, atualiza status,
  salva no mesmo caminho e retorna o `DataFrame`.

Na remocao, `pandas.date_range` expande o intervalo e cada dia gera uma
requisicao `DELETE`. Excecoes `Timeout` recebem `TIMEOUT`; falhas HTTP e outras
excecoes recebem `ERRO`.

## 7. Seguranca, persistencia e limites

- `.env` contem credenciais e token e nao deve ser versionado.
- CSVs reais podem conter dados pessoais e nao devem ser compartilhados.
- O arquivo de entrada e sobrescrito ao final do processamento.
- Nao existe rollback: uma falha no meio de uma remocao de varios dias pode
  deixar dias anteriores ja removidos e a linha marcada como `ERRO`.
- Nao ha suite de testes automatizados no repositorio atualmente.
- Alteracoes em colunas, status ou endpoints devem atualizar este documento e o
  `README.md`.
- Os testes podem ser executados com `uv run python -m unittest discover -s tests -v`.
