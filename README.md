# AutoRH247

Automacao de abonos de ponto integrada a API REST do RH247.

O projeto recebe uma planilha CSV, valida e normaliza seus dados, resolve o
colaborador por nome ou CPF, inclui ou remove abonos e persiste o resultado na
mesma planilha. A aplicacao oferece uma CLI, uma interface Tkinter e um menu
clicavel para Windows.

## Visao tecnica

O sistema e dividido em tres camadas:

```text
Interface
  cli.py / gui.py / autoRH247.bat
      |
Dominio
  validator.py / models.py / processor.py
      |
Integracao
  client.py / services.py
      |
API REST RH247
```

Fluxo de inclusao:

```text
CSV -> validacao -> busca do colaborador -> POST de abono -> Status=OK -> CSV
```

Fluxo de remocao:

```text
CSV com Status=DELETE -> validacao -> busca -> DELETE por dia
  -> Status=DELETED -> CSV
```

## Requisitos

- Windows 10 ou superior para os atalhos `.bat`.
- Python 3.11 ou superior.
- `uv` instalado no `PATH`.
- Acesso a API RH247 e credenciais validas.
- PowerShell para instalacao e comandos de desenvolvimento.

## Instalacao no Windows

### 1. Instalar o Python

Pelo PowerShell, usando o Windows Package Manager:

```powershell
winget install --id Python.Python.3.11 -e --source winget
```

Feche e reabra o PowerShell e confirme:

```powershell
python --version
py --version
```

O resultado deve ser Python 3.11 ou superior.

### 2. Instalar o uv pelo pip

```powershell
py -m pip install --upgrade pip
py -m pip install --upgrade uv
uv --version
```

Se `uv` nao for encontrado, reabra o PowerShell. Como alternativa, use
`py -m uv` quando aplicavel.

### 3. Obter o codigo

```powershell
git clone URL_DO_REPOSITORIO
Set-Location .\AUTO_RH247-v2
```

Para um clone existente:

```powershell
Set-Location "C:\caminho\para\AUTO_RH247-v2"
```

A raiz correta contem `pyproject.toml`:

```powershell
Get-ChildItem pyproject.toml
```

### 4. Criar o ambiente e instalar dependencias

```powershell
uv sync
```

O comando cria ou atualiza `.venv`, instala a versao de Python necessaria
quando disponivel e instala as dependencias declaradas em `pyproject.toml`:

- `pandas`: leitura, validacao, transformacao e persistencia do CSV.
- `requests`: comunicacao HTTP com a API.
- `python-dotenv`: leitura e persistencia do `.env`.

O lockfile utilizado e `uv.lock`; alteracoes de dependencias devem ser feitas
no `pyproject.toml` e sincronizadas com `uv lock` ou `uv sync`.

## Configuracao

Crie o arquivo local a partir do modelo:

```powershell
Copy-Item .env.example .env
notepad .env
```

Configure as variaveis necessarias:

```env
API_LOGIN=seu_login
API_SENHA=sua_senha
TOKEN_API=
URL_AUTH=https://seu-endpoint-de-autenticacao
URL_SEARCH=https://seu-endpoint-de-busca
URL_ID=
URL_JUSTIFY=https://seu-endpoint-de-inclusao
URL_DELETE=https://seu-endpoint-de-remocao
```

`TOKEN_API` pode ficar vazio na primeira execucao. O cliente obtem um token
novo, salva-o no `.env` e o reutiliza nas execucoes seguintes.

Nunca versione `.env`. O `.env.example` deve conter somente placeholders e
pode ser enviado ao GitHub.

## Estrutura do repositorio

```text
AUTO_RH247-v2/
├── .env.example                 # Modelo seguro de configuracao
├── .gitignore                   # Protecao de segredos e artefatos locais
├── README.md                    # Documentacao para desenvolvedores
├── agents.md                    # Referencia tecnica detalhada
├── autoRH247.bat                # Menu clicavel para Windows
├── pyproject.toml               # Metadados, dependencias e entry point
├── uv.lock                      # Dependencias fixadas pelo uv
├── data/
│   └── justificativas.example.csv
├── src/
│   └── autorh247/
│       ├── __init__.py
│       ├── cli.py               # Interface argparse
│       ├── gui.py               # Interface Tkinter
│       ├── config.py            # Caminhos e ambiente
│       ├── api/
│       │   ├── __init__.py
│       │   ├── client.py        # Sessao, autenticacao e wrappers HTTP
│       │   └── services.py      # Operacoes especificas da API
│       └── core/
│           ├── __init__.py
│           ├── models.py         # Enum StatusAbono
│           ├── processor.py      # Orquestracao do processamento
│           └── validator.py      # Leitura e validacao do CSV
└── tests/
    ├── __init__.py
    └── unit/
        ├── __init__.py
        ├── api/test_services.py
        └── core/test_processor.py
```

Arquivos locais como `.env`, `data/justificativas.csv`, `.venv`, caches,
logs, chaves, bancos e builds sao protegidos pelo `.gitignore`.

## Contratos principais

### CSV

O arquivo deve ser UTF-8 e usar exatamente estas colunas:

| Coluna | Obrigatoria | Comportamento |
| --- | --- | --- |
| `Status` | Nao | Vazio inclui; `DELETE` remove |
| `Nome Completo` | Sim | Nome ou CPF consultado |
| `Data Inicial` | Sim | `DD/MM/YY` ou `DD/MM/YYYY` |
| `Data Final` | Nao | Vazia recebe `Data Inicial` |
| `Descrição` | Sim | Motivo do abono |

O validador cria colunas ausentes, limpa textos, converte datas, completa a
data final e marca linhas invalidas como `ERRO`. Datas validas sao persistidas
como `DD/MM/YYYY`.

### Status

- vazio: inclusao pendente;
- `DELETE`: remocao diaria no intervalo;
- `OK`: inclusao concluida;
- `DELETED`: remocao concluida;
- `ERRO`: falha estrutural, HTTP ou inesperada;
- `NOT FOUND`: nenhum colaborador encontrado;
- `MULTIPLE CHOICES`: mais de um colaborador encontrado;
- `TIMEOUT`: requisicao excedeu 30 segundos;
- `CONFLITO`: reservado no modelo e nao produzido atualmente.

O processador ignora `OK`, `DELETED` e `ERRO`. Os demais status podem ser
processados novamente.

### API

`RH247Client` mantem uma `requests.Session`, instala o header `Authorization` e
usa timeout padrao de 30 segundos nos metodos `GET`, `POST` e `DELETE`.

`RH247Service` implementa:

- busca por nome ou CPF em `URL_SEARCH`, usando `params` HTTP;
- inclusao via `POST` em `URL_JUSTIFY`;
- remocao diaria via `DELETE` em `URL_DELETE`.

Payload de inclusao:

```json
{
  "descricao_add_atestado_main": "motivo",
  "data_inicial_add_atestado_main": "DD/MM/YYYY",
  "data_final_add_atestado_main": "DD/MM/YYYY",
  "fv_alteracao_escala_main": 18434
}
```

## Comandos de desenvolvimento

Todos os comandos abaixo devem ser executados na raiz do projeto.

Ver ajuda:

```powershell
uv run autorh247 --help
```

Buscar colaborador:

```powershell
uv run autorh247 buscar "NOME DO FUNCIONARIO"
uv run autorh247 buscar "123.456.789-00"
```

Validar sem acessar a API:

```powershell
uv run autorh247 validar -a data\justificativas.example.csv
uv run autorh247 validar -a data\justificativas.csv
```

Processar a planilha padrao ou um caminho especifico:

```powershell
uv run autorh247 processar
uv run autorh247 processar -a data\justificativas.csv
```

Testar autenticacao:

```powershell
uv run autorh247 auth
uv run autorh247 auth --renovar
```

Executar testes unitarios:

```powershell
uv run python -m unittest discover -s tests -v
```

## Interfaces para Windows

### Menu clicavel

Abra `autoRH247.bat` com duplo clique. O menu oferece:

1. Busca por nome ou CPF.
2. Validacao de planilha.
3. Processamento de planilha.
4. Abertura da interface grafica.
5. Encerramento.

O menu requer `uv` instalado e deve ser executado a partir do projeto clonado.

### Interface grafica

A opcao 4 do menu inicia a interface Tkinter. Tambem e possivel iniciar
manualmente:

```powershell
uv run python -m autorh247.gui
```

A GUI permite selecionar CSV, buscar funcionario, validar dados e processar a
planilha. O processamento executa em segundo plano e solicita confirmacao antes
de alterar a planilha ou chamar a API.

## Empacotamento opcional

Para gerar uma distribuicao Windows, instale o PyInstaller como dependencia de
desenvolvimento:

```powershell
uv add --dev pyinstaller
uv run pyinstaller --name autorh247 --onedir --windowed --paths src src/autorh247/gui.py
```

O resultado fica em `dist/autorh247/`. Mantenha `.env` e `data/` fora do
executavel, ao lado da distribuicao. O `config.py` usa a pasta do executavel
quando o programa esta empacotado.

## Testes e limites conhecidos

A suíte atual usa `unittest` e mocks; nao faz chamadas reais a API. Ainda devem
ser cobertos, idealmente:

- validacao completa do CSV;
- autenticacao e renovacao de token;
- respostas paginadas e respostas invalidas da API;
- falhas parciais durante remocao de varios dias;
- testes de integracao controlados.

O CSV de entrada e sobrescrito ao final do processamento. Remocoes de varios
dias nao possuem rollback: uma falha pode ocorrer depois de dias anteriores ja
terem sido removidos.

Para detalhes de todas as funcoes e responsabilidades, consulte
[agents.md](agents.md).
