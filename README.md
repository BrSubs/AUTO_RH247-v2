# AutoR247 - Automação de Abono de Ponto via API RH247

Aplicação em Python (CLI) para automação de abono de faltas e justificativas de ponto eletrônico consumindo a API REST do **RH247**.

O sistema lê um arquivo CSV local, valida os dados e consistência de datas, resolve os identificadores dos colaboradores na API, envia os pedidos de abono e atualiza o arquivo CSV com o status de cada operação.

---

## 🛠️ Tecnologias e Ferramentas

- **Linguagem:** Python 3.11+
- **Gerenciador de Pacotes e Ambiente:** [uv](https://docs.astral.sh/uv/)
- **Manipulação de Dados:** Pandas
- **Comunicação HTTP:** Requests
- **Configurações:** Python-dotenv

---

## 📁 Estrutura do Projeto

```text
AutoR247/
├── .env.example                     # Modelo de variáveis de ambiente
├── .gitignore                       # Ignora credenciais (.env) e dados reais (*.csv)
├── pyproject.toml                   # Dependências e configuração da CLI
├── README.md                        # Documentação da aplicação
├── agents.md                        # Especificações técnicas e contratos de API
├── data/                            # Diretório de dados e planilhas
│   ├── justificativas.example.csv   # Planilha de exemplo (versionada)
│   └── justificativas.csv           # Planilha real de trabalho (ignorada no git)
└── src/
    └── autor247/                    # Pacote principal
        ├── __init__.py
        ├── config.py                # Configurações, paths e variáveis do .env
        ├── cli.py                   # Interface de linha de comando (CLI)
        ├── api/                     # Camada de comunicação HTTP
        │   ├── client.py            # Sessão HTTP e autenticação / cache de token
        │   └── services.py          # Endpoints: busca de funcionários e envio de abono
        └── core/                    # Camada de regras de negócio
            ├── models.py            # Enums e modelos de status
            ├── validator.py         # Leitura, sanitização e validação do CSV
            └── processor.py         # Orquestração do processamento linha a linha
```

---

## ⚙️ Configuração Inicial

### 1. Clonar o Repositório e Instalar Dependências
Certifique-se de ter o `uv` instalado. As dependências são instaladas e gerenciadas automaticamente:
```powershell
uv sync
```

### 2. Configurar o Arquivo `.env`
Crie um arquivo `.env` na raiz do projeto a partir do modelo `.env.example`:
```powershell
cp .env.example .env
```

Abra o arquivo `.env` com qualquer editor de texto e preencha os campos:
```env
API_LOGIN='login'
API_SENHA='senha'
URL_AUTH='url_auth'
URL_SEARCH='url_search'
URL_JUSTIFY='url_justify'
TOKEN_API='token_api'
```

---

## 📋 Formato do Arquivo CSV (`data/justificativas.csv`)

Crie (ou edite) o arquivo `data/justificativas.csv` com as colunas abaixo.
Um modelo já está disponível em `data/justificativas.example.csv`.

| Coluna | Obrigatória | Descrição / Regra |
| :--- | :--- | :--- |
| `Status` | Não | Preenchido automaticamente ou usado como comando.<br>• Deixe em branco (ou status diferente de OK/DELETED) para **inserir abono**.<br>• Defina como `DELETE` para **remover o abono** do intervalo informado.<br>• Resultados gravados: `OK`, `DELETED`, `ERRO`, `NOT FOUND`, `MULTIPLE CHOICES`, `TIMEOUT`. |
| `Nome Completo` | Sim | Nome do colaborador para busca na API. |
| `Data Inicial` | Sim | Data inicial do abono (`DD/MM/YYYY` ou `DD/MM/YY`). |
| `Data Final` | Não | Data final do abono. Se vazia, assume a `Data Inicial`. |
| `Descrição` | Sim | Motivo / justificativa do abono. |

---

## 🚀 Como Usar (Comandos da CLI)

Você pode executar os comandos da CLI usando o prefixo `uv run autor247`:

### 1. Pesquisar Colaborador na API
Pesquisa funcionários pelo nome para inspecionar ID, matrícula, cargo e CPF:
```powershell
uv run autor247 buscar "NOME DO FUNCIONARIO"
```

### 2. Validar Estrutura do CSV
Verifica se existem datas inválidas, campos obrigatórios vazios ou inconsistências sem fazer alterações na API:
```powershell
uv run autor247 validar
# ou especificando outro arquivo:
uv run autor247 validar -a data/justificativas.example.csv
```

### 3. Processar e Enviar Abonos
Valida, busca os IDs dos colaboradores, envia os abonos na API e salva os status no CSV:
```powershell
uv run autor247 processar
# ou especificando outro arquivo:
uv run autor247 processar -a data/justificativas.csv
```

### 4. Testar ou Renovar Autenticação
Verifica o token salvo ou força a obtenção de um novo token:
```powershell
uv run autor247 auth
# para forçar renovação:
uv run autor247 auth --renovar
```

---

## 🔒 Segurança e Dados Sensíveis
- Arquivos `.env` e planilhas reais com nomes de funcionários (`data/*.csv`) são automaticamente ignorados pelo `.gitignore`.
- Nunca commite senhas, tokens ou dados pessoais de colaboradores no repositório.