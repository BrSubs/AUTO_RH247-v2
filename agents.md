# AGENTS.md - Documentação do Projeto: Automação de Abono de Faltas via API (RH)

Este documento especifica a arquitetura, o fluxo de execução, as regras de negócio e a lógica da aplicação em Python para automação de abono de pontos.

---

## 1. Visão Geral da Arquitetura
A aplicação processa um arquivo `.csv` local, valida e trata os dados estruturalmente, consome uma API REST do RH para resolver identificadores de funcionários, envia requisições `POST` para abonar as ausências e atualiza o arquivo CSV com os status de retorno de cada operação.

---

## 2. Tecnologias e Dependências
* **Linguagem:** Python
* **Manipulação de Dados:** Pandas
* **Configurações e Segurança:** Arquivo `.env` (credenciais, token de acesso e URLs base)
* **Comunicação HTTP:** Requisições para API REST

---

## 3. Contrato de Dados (Arquivo CSV)
O arquivo CSV deve conter estritamente as seguintes colunas:

| Coluna | Obrigatória | Regra de Negócio / Comportamento |
| :--- | :--- | :--- |
| `status` | Não (Gerenciado pelo script) | Armazena o estado/resultado do processamento da linha (`OK`, `ERRO`, `NOT FOUND`, `MULTIPLE CHOICES`, `CONFLITO`, `TIMEOUT`, `VAZIO`, etc.). |
| `nome_completo` | Sim | Nome do funcionário. Utilizado para buscar o ID correspondente na API. |
| `data_inicio` | Sim | Data inicial do abono (Formato: `DD/MM/YYYY` ou `DD/MM/YY`). |
| `data_fim` | Não | Data final do abono. Se estiver vazia, assume automaticamente o mesmo valor de `data_inicio`. |
| `motivo` | Sim | Justificativa/motivo do abono. |

---

## 4. Gerenciamento de Autenticação (`.env`)
* **Token Caching:** O token de acesso é fixo e reutilizável mesmo após o encerramento da sessão. O script deve verificar se o token já está salvo no `.env`.
* **Fluxo de Login:** Caso o token não esteja presente no `.env`:
  * **Endpoint:** `POST https://api.rh247.com.br/230540701/ponto/authenticate/create`
  * **Payload:** `{"login": "...", "senha": "..."}`
  * **Retorno:** Extrai-se o campo `token` da resposta JSON e salva-se/atualiza-se no arquivo `.env`.

---

## 5. Fluxo de Execução da Aplicação (Passo a Passo)

### Fase 1: Validação e Preparação Inicial do CSV
1. Carregar o arquivo `.csv` utilizando Pandas.
2. Validar a existência de todas as colunas obrigatórias.
3. Aplicar a regra do `data_fim`: se o campo estiver em branco, preenchê-lo com o valor de `data_inicio`.
4. Validar os campos obrigatórios em cada linha (`nome_completo` e `motivo`):
   * Se houver falhas estruturais, preencher imediatamente o campo `status` com a mensagem de erro correspondente.
   * Linhas com erros estruturais detectados nesta fase são isoladas e não seguem para o envio na API.

### Fase 2: Execução Linha por Linha (Abono)
Para cada linha que passou na validação estrutural da Fase 1:
1. **Busca de Identificação (GET):** Realizar uma requisição de busca utilizando o `nome_completo` para obter o ID do funcionário (`fv_alteracao_escala_main`).
2. **Tratamento de Ambiguidade / Retorno da Busca:**
   * Se retornar **0 resultados**: Definir o `status` da linha como `NOT FOUND`.
   * Se retornar **múltiplos resultados**: Definir o `status` da linha como `MULTIPLE CHOICES`.
   * Se retornar **exatamente 1 resultado**: Extrair o ID correspondente (`fv_alteracao_escala_main`).
3. **Envio da Requisição de Abono (POST):**
   * **Endpoint:** `POST https://api.rh247.com.br/230540701/ponto/atestados/add-atestado-by-calendario`
   * **Payload JSON:**
     ```json
     {
       "descricao_add_atestado_main": "motivo",
       "data_inicial_add_atestado_main": "data_inicio",
       "data_final_add_atestado_main": "data_fim",
       "fv_alteracao_escala_main": id_obtido
     }
     ```
4. **Atualização de Status Pós-Execução:**
   * Imediatamente após a tentativa de abono de cada linha, atualizar o campo `status` com o resultado correspondente (ex: `OK`, `ERRO`, `CONFLITO`, `TIMEOUT`, `VAZIO`, etc.).

### Fase 3: Persistência
1. Após a conclusão do loop de todas as linhas, salvar/sobrescrever o arquivo `.csv` em disco contendo todos os status atualizados.