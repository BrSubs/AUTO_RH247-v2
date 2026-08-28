<div align="center">

# AutoRH247

**Automação de abonos de ponto integrada à API REST do RH247**

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Windows](https://img.shields.io/badge/Platform-Windows-lightgrey)
![License](https://img.shields.io/badge/status-uso%20interno-orange)

</div>

---

## Sobre o projeto

O **AutoRH247** automatiza o processo manual de inclusão e remoção de abonos
(atestados/justificativas) no sistema RH247. A partir de uma planilha CSV, o
sistema:

1. Valida e normaliza os dados (colaborador, período, motivo);
2. Resolve o colaborador por nome ou CPF diretamente na API do RH247;
3. Inclui ou remove o abono via requisições HTTP;
4. Grava o resultado de volta na mesma planilha, linha a linha.

Está disponível como **CLI**, **interface gráfica (Tkinter)** e um **menu
clicável** para Windows (`autoRH247.bat`), cobrindo tanto uso técnico quanto
uso por pessoas não técnicas da equipe de RH.

## Índice

- [Arquitetura](#arquitetura)
- [Fluxo de processamento](#fluxo-de-processamento)
- [Requisitos](#requisitos)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Uso](#uso)
  - [CLI](#cli)
  - [Menu clicável (Windows)](#menu-clicável-windows)
  - [Interface gráfica](#interface-gráfica)
- [Contrato de dados (CSV)](#contrato-de-dados-csv)
- [Status do processamento](#status-do-processamento)
- [Estrutura do repositório](#estrutura-do-repositório)
- [Testes](#testes)
- [Empacotamento (opcional)](#empacotamento-opcional)
- [Segurança](#segurança)
- [Limitações conhecidas](#limitações-conhecidas)
- [Documentação técnica adicional](#documentação-técnica-adicional)

## Arquitetura

O projeto segue uma separação clara em três camadas:

```
┌─────────────────────────────────────────┐
│                Interface                 │
│     cli.py · gui.py · autoRH247.bat      │
└───────────────────┬───────────────────────┘
                    │
┌───────────────────▼───────────────────────┐
│                 Domínio                  │
│  validator.py · models.py · processor.py │
└───────────────────┬───────────────────────┘
                    │
┌───────────────────▼───────────────────────┐
│               Integração                 │
│      client.py · services.py             │
└───────────────────┬───────────────────────┘
                    │
              API REST RH247
```

| Camada | Responsabilidade |
| --- | --- |
| Interface | Recebe a intenção do usuário (linha de comando, GUI ou menu) |
| Domínio | Valida dados, aplica regras de negócio e orquestra o processamento |
| Integração | Autentica e comunica-se com a API RH247 via HTTP |

## Fluxo de processamento

**Inclusão de abono**

```
CSV → validação → busca do colaborador → POST de abono → Status=OK → CSV
```

**Remoção de abono**

```
CSV com Status=DELETE → validação → busca do colaborador
   → DELETE por dia do intervalo → Status=DELETED → CSV
```

## Requisitos

- Windows 10 ou superior (para os atalhos `.bat`);
- Python 3.11 ou superior;
- [`uv`](https://docs.astral.sh/uv/) instalado no `PATH`;
- Acesso à API RH247 e credenciais válidas;
- PowerShell para instalação e comandos de desenvolvimento.

## Instalação

### 1. Instalar o Python

```powershell
winget install --id Python.Python.3.11 -e --source winget
```

Feche e reabra o PowerShell e confirme a instalação:

```powershell
python --version
py --version
```

### 2. Instalar o `uv`

```powershell
py -m pip install --upgrade pip
py -m pip install --upgrade uv
uv --version
```

Se o comando `uv` não for reconhecido, reabra o PowerShell ou utilize
`py -m uv` como alternativa.

### 3. Obter o código

```powershell
git clone URL_DO_REPOSITORIO
Set-Location .\AUTO_RH247-v2
```

Confirme que está na raiz correta:

```powershell
Get-ChildItem pyproject.toml
```

### 4. Instalar as dependências

```powershell
uv sync
```

Esse comando cria/atualiza o `.venv`, instala a versão de Python necessária
(quando disponível) e resolve as dependências declaradas em `pyproject.toml`:

| Pacote | Uso |
| --- | --- |
| `pandas` | Leitura, validação, transformação e persistência do CSV |
| `requests` | Comunicação HTTP com a API RH247 |
| `python-dotenv` | Leitura e persistência das variáveis do `.env` |

O lockfile é o `uv.lock`. Alterações de dependências devem ser feitas no
`pyproject.toml` e sincronizadas com `uv lock` ou `uv sync`.

## Configuração

Crie o arquivo de ambiente local a partir do modelo:

```powershell
Copy-Item .env.example .env
notepad .env
```

Preencha as variáveis necessárias:

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

> **Nota:** `TOKEN_API` pode ficar vazio na primeira execução. O cliente
> obtém um novo token automaticamente, salva-o no `.env` e o reutiliza nas
> execuções seguintes.

> ⚠️ **Nunca versione o `.env`.** Apenas `.env.example`, com valores fictícios,
> deve ser enviado ao repositório.

## Uso

Todos os comandos abaixo devem ser executados na raiz do projeto.

### CLI

Ajuda geral:

```powershell
uv run autorh247 --help
```

Buscar colaborador por nome ou CPF:

```powershell
uv run autorh247 buscar "NOME DO FUNCIONARIO"
uv run autorh247 buscar "123.456.789-00"
```

Validar a planilha sem acessar a API:

```powershell
uv run autorh247 validar -a data\justificativas.example.csv
uv run autorh247 validar -a data\justificativas.csv
```

Processar a planilha padrão ou um caminho específico:

```powershell
uv run autorh247 processar
uv run autorh247 processar -a data\justificativas.csv
```

Testar ou renovar a autenticação:

```powershell
uv run autorh247 auth
uv run autorh247 auth --renovar
```

Cada subcomando aceita `-h`/`--help` para detalhes de argumentos.

### Menu clicável (Windows)

Dê duplo clique em `autoRH247.bat`. O menu oferece:

1. Busca por nome ou CPF;
2. Validação de planilha;
3. Processamento de planilha;
4. Abertura da interface gráfica;
5. Encerramento.

O menu requer `uv` instalado e deve ser executado a partir do projeto
clonado.

### Interface gráfica

A opção 4 do menu inicia a interface Tkinter. Também é possível iniciá-la
manualmente:

```powershell
uv run python -m autorh247.gui
```

A GUI permite selecionar o CSV, buscar um funcionário, validar os dados e
processar a planilha. O processamento roda em segundo plano e solicita
confirmação antes de alterar a planilha ou chamar a API.

## Contrato de dados (CSV)

O arquivo deve ser **UTF-8** e conter exatamente estas colunas:

| Coluna | Obrigatória | Comportamento |
| --- | --- | --- |
| `Status` | Não | Vazio inclui abono; `DELETE` remove |
| `Nome Completo` | Sim | Nome ou CPF consultado na API |
| `Data Inicial` | Sim | Aceita `DD/MM/YY` ou `DD/MM/YYYY` |
| `Data Final` | Não | Se vazia, recebe o valor de `Data Inicial` |
| `Descrição` | Sim | Motivo do abono |

O validador cria colunas ausentes, limpa textos, converte datas, completa a
data final quando vazia e marca linhas estruturalmente inválidas como `ERRO`.
Datas válidas são persistidas no formato `DD/MM/YYYY`.

## Status do processamento

| Status | Significado |
| --- | --- |
| *(vazio)* | Inclusão pendente |
| `DELETE` | Remoção diária no intervalo informado |
| `OK` | Inclusão concluída |
| `DELETED` | Remoção concluída |
| `ERRO` | Falha estrutural, HTTP ou inesperada |
| `NOT FOUND` | Nenhum colaborador encontrado |
| `MULTIPLE CHOICES` | Mais de um colaborador encontrado |
| `TIMEOUT` | Requisição excedeu 30 segundos |
| `CONFLITO` | Reservado no modelo; não produzido atualmente |

O processador ignora linhas com `OK`, `DELETED` e `ERRO`. Os demais status
podem ser reprocessados.

### Comunicação com a API

`RH247Client` mantém uma `requests.Session`, injeta o header `Authorization`
e aplica timeout padrão de 30 segundos em `GET`, `POST` e `DELETE`.

`RH247Service` implementa:

- busca por nome ou CPF em `URL_SEARCH`, via parâmetros HTTP;
- inclusão de abono via `POST` em `URL_JUSTIFY`;
- remoção diária via `DELETE` em `URL_DELETE`.

Payload de inclusão:

```json
{
  "descricao_add_atestado_main": "motivo",
  "data_inicial_add_atestado_main": "DD/MM/YYYY",
  "data_final_add_atestado_main": "DD/MM/YYYY",
  "fv_alteracao_escala_main": 18434
}
```

## Estrutura do repositório

```
AUTO_RH247-v2/
├── .env.example                 # Modelo seguro de configuração
├── .gitignore                   # Proteção de segredos e artefatos locais
├── README.md                    # Este documento
├── agents.md                    # Referência técnica detalhada
├── autoRH247.bat                # Menu clicável para Windows
├── pyproject.toml               # Metadados, dependências e entry point
├── uv.lock                      # Dependências fixadas pelo uv
├── data/
│   └── justificativas.example.csv
├── src/
│   └── autorh247/
│       ├── __init__.py
│       ├── cli.py               # Interface argparse
│       ├── gui.py               # Interface Tkinter
│       ├── config.py            # Caminhos e variáveis de ambiente
│       ├── api/
│       │   ├── __init__.py
│       │   ├── client.py        # Sessão, autenticação e wrappers HTTP
│       │   └── services.py      # Operações específicas da API
│       └── core/
│           ├── __init__.py
│           ├── models.py        # Enum StatusAbono
│           ├── processor.py     # Orquestração do processamento
│           └── validator.py     # Leitura e validação do CSV
└── tests/
    ├── __init__.py
    └── unit/
        ├── __init__.py
        ├── api/test_services.py
        └── core/test_processor.py
```

Arquivos locais como `.env`, `data/justificativas.csv`, `.venv/`, caches,
logs, chaves e bancos de dados são protegidos pelo `.gitignore`.

## Testes

A suíte atual usa `unittest` com mocks e **não realiza chamadas reais à
API**.

```powershell
uv run python -m unittest discover -s tests -v
```

Itens que ainda devem ser cobertos:

- validação completa do CSV;
- autenticação e renovação de token;
- respostas paginadas e respostas inválidas da API;
- falhas parciais durante a remoção de múltiplos dias;
- testes de integração controlados.

## Empacotamento (opcional)

Para gerar uma distribuição Windows standalone, instale o PyInstaller como
dependência de desenvolvimento:

```powershell
uv add --dev pyinstaller
uv run pyinstaller --name autorh247 --onedir --windowed --paths src src/autorh247/gui.py
```

O resultado fica em `dist/autorh247/`. Mantenha `.env` e `data/` fora do
executável, ao lado da distribuição — `config.py` já resolve os caminhos
corretamente quando o programa está empacotado.

## Segurança

- Nunca versione `.env`; apenas `.env.example` com placeholders deve ir para
  o repositório.
- Planilhas com dados reais de colaboradores contêm informação pessoal e não
  devem ser compartilhadas fora dos canais autorizados.
- O CSV de entrada é **sobrescrito** ao final do processamento — mantenha
  backups quando necessário.

## Limitações conhecidas

- Remoções de múltiplos dias não possuem rollback: uma falha pode ocorrer
  depois que dias anteriores do intervalo já foram removidos, deixando a
  linha marcada como `ERRO` mesmo com remoções parciais aplicadas.
- Não há testes de integração automatizados contra a API real.

## Documentação técnica adicional

Para detalhes de todas as funções, classes e responsabilidades de cada
módulo, consulte [`agents.md`](agents.md).
