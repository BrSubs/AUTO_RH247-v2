# AutoRH247

Aplicacao Python de linha de comando para automatizar inclusao e remocao de
abonos de ponto pela API REST do RH247.

O sistema le um CSV local, valida os campos e datas, busca o colaborador por
nome ou CPF, executa a operacao solicitada e salva o status no proprio arquivo.

## Requisitos

- Python 3.11 ou superior
- `uv`
- Credenciais e URLs da API RH247

## Instalacao

Na raiz do repositorio, sincronize o ambiente:

```powershell
uv sync
```

Crie um arquivo `.env` na raiz do projeto e configure:

```env
API_LOGIN=login
API_SENHA=senha
URL_AUTH=url_auth
URL_SEARCH=url_search
URL_JUSTIFY=url_justify
URL_DELETE=url_delete
TOKEN_API=token_opcional
```

`TOKEN_API` e opcional. Quando nao existe, o programa autentica usando
`API_LOGIN` e `API_SENHA`, salva o token retornado no `.env` e reutiliza-o nas
execucoes seguintes.

## Estrutura

```text
AutoRH247/
├── agents.md
├── README.md
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

Os testes unitários ficam organizados por camada:

```text
tests/
├── unit/
│   ├── api/test_services.py
│   └── core/test_processor.py
```

## Formato do CSV

O arquivo deve usar UTF-8 e estas colunas com grafia exata:

| Coluna | Obrigatoria | Regra |
| --- | --- | --- |
| `Status` | Nao | Comanda a acao e recebe o resultado |
| `Nome Completo` | Sim | Nome ou CPF do colaborador |
| `Data Inicial` | Sim | `DD/MM/YY` ou `DD/MM/YYYY` |
| `Data Final` | Nao | Vazia: assume `Data Inicial` |
| `Descrição` | Sim | Motivo do abono |

Exemplo:

```csv
Status,Nome Completo,Data Inicial,Data Final,Descrição
,NOME DO FUNCIONARIO,02/08/2026,02/08/2026,Justificativa
DELETE,NOME DO FUNCIONARIO,03/08/2026,04/08/2026,Remover abono
```

O validador cria colunas ausentes, limpa textos, completa `Data Final`, valida
as datas e marca como `ERRO` as linhas estruturalmente invalidas. Datas validas
sao gravadas no formato `DD/MM/YYYY`.

## Uso

Todos os comandos usam o prefixo `uv run autorh247`.

### Buscar colaborador

Busca automaticamente por CPF quando o identificador possui 11 digitos; nos
demais casos, busca por nome:

```powershell
uv run autorh247 buscar "NOME DO FUNCIONARIO"
uv run autorh247 buscar "123.456.789-00"
```

### Validar CSV

Valida e exibe o resultado sem acessar a API:

```powershell
uv run autorh247 validar
uv run autorh247 validar -a data/justificativas.example.csv
```

### Processar abonos

Processa o arquivo padrao `data/justificativas.csv` ou um caminho informado:

```powershell
uv run autorh247 processar
uv run autorh247 processar -a data/justificativas.csv
```

Para uma linha sem status, o programa busca o colaborador e envia um `POST` de
inclusao. Para uma linha com status `DELETE`, remove o abono dia a dia com uma
requisicao `DELETE` para cada data do intervalo.

### Autenticacao

Verifica o token atual ou força sua renovacao:

```powershell
uv run autorh247 auth
uv run autorh247 auth --renovar
```

## Status

- vazio: inclui abono;
- `DELETE`: remove abono dia a dia;
- `OK`: inclusao concluida;
- `DELETED`: remocao concluida;
- `ERRO`: erro estrutural ou falha geral;
- `NOT FOUND`: nenhum colaborador encontrado;
- `MULTIPLE CHOICES`: mais de um colaborador encontrado;
- `TIMEOUT`: requisicao excedeu 30 segundos;
- `CONFLITO`: reservado no modelo e nao produzido atualmente.

As linhas com `OK`, `DELETED` e `ERRO` nao sao processadas novamente. Linhas com
`NOT FOUND` e `MULTIPLE CHOICES` podem ser tentadas novamente.

## Arquitetura

A aplicacao e organizada em tres camadas:

1. **Interface**: `autorh247/cli.py` registra e executa os comandos.
2. **Dominio**: `autorh247/core` valida dados, define status e processa linhas.
3. **Integracao**: `autorh247/api` gerencia autenticacao e chamadas HTTP.

O fluxo de processamento e:

```text
CLI -> AbonoProcessor -> validador CSV -> busca na API
    -> inclusao POST ou remocao DELETE -> atualiza Status -> salva CSV
```

A documentacao tecnica completa, incluindo todas as funcoes, classes, payloads,
variaveis de ambiente e limitacoes, esta em [agents.md](agents.md).

## Testes

Execute a suíte unitária sem acessar a API:

```powershell
uv run python -m unittest discover -s tests -v
```

## Seguranca e limitacoes

- Nunca versione `.env`, tokens, credenciais ou CSVs com dados pessoais.
- O CSV de entrada e sobrescrito ao final do processamento.
- Remocoes de varios dias nao possuem rollback; uma falha pode ocorrer depois
  de alguns dias ja terem sido removidos.
- O repositorio atualmente nao possui testes automatizados.
