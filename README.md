# Goose Cat — Backend

API REST do Goose Cat, o gerenciador de tarefas que trabalha contra você.
Recebe tarefas, consulta o Gemini para gerar desculpas de procrastinação e gerencia um gatinho virtual que vira monstro quando você não é produtivo.

## Stack

| | |
|---|---|
| **Runtime** | Python 3.11+ |
| **Framework principal** | FastAPI |
| **Framework secundário** | Flask (montado dentro do FastAPI via `a2wsgi`) |
| **Banco** | MongoDB via Motor (async) + PyMongo (sync) |
| **IA** | Google Gemini 2.5 Flash |
| **Agendamento** | APScheduler |

## Pré-requisitos

1. **Chave da Gemini API** (grátis)
   - Gere em [aistudio.google.com/apikey](https://aistudio.google.com/apikey)

2. **MongoDB** — escolha uma opção:
   - **MongoDB Atlas** (recomendado para produção/apresentação) — cloud grátis
   - **MongoDB local** — para desenvolvimento

## Opção 1: MongoDB Atlas + Docker (mais prático)

Sobe o backend com MongoDB Atlas:

```bash
# 1. Clone o repositório
git clone https://github.com/isabelapt/hackcodecon-codequeens-back.git
cd hackcodecon-codequeens-back

# 2. Crie o .env
cp backend/.env.example backend/.env

# 3. Configure no backend/.env:
#    - GEMINI_API_KEY (gerada acima)
#    - MONGODB_URL (do cluster Atlas)
#    - MONGODB_DB (nome do banco)

# 4. Suba com Docker
docker compose up --build
```

Acesse `http://localhost:8000/docs` para a documentação interativa.

> **Gerando a connection string do Atlas:**
> 1. Crie conta em [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
> 2. Deploy FREE cluster
> 3. Clique **Connect** → **Drivers** → Python
> 4. Copia a string e coloca em `MONGODB_URL` do `.env`

## Opção 2: Desenvolvimento Local (sem Docker)

Para trabalhar sem Docker, use MongoDB local:

```bash
# 1. Instale MongoDB Community:
#    https://www.mongodb.com/try/download/community
#    Inicie mongod (roda na porta 27017 por padrão)

# 2. Setup do backend
py -3.11 -m venv venv
source venv/bin/activate   # Linux / Mac
venv\Scripts\activate      # Windows
py -3.11 -m pip install -r requirements.txt

# 3. Configure .env
cp .env.example .env
# Preencha MONGODB_URL, MONGODB_DB e GEMINI_API_KEY

# 4. Inicie o servidor
py -3.11 -m uvicorn main:app --reload --port 8000
```

> **Atenção:** Use Python 3.11. Versões mais novas (3.13+) podem ter incompatibilidades com `pydantic-core`.
> Se tiver problemas de SSL ao instalar dependências, use:
> ```bash
> py -3.11 -m pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org
> ```

## Variáveis de ambiente

| Variável | Obrigatória | Descrição |
|---|---|---|
| `GEMINI_API_KEY` | Sim | Chave da API do Google AI Studio |
| `MONGODB_URL` | Sim | Connection string do MongoDB |
| `MONGODB_DB` | Sim | Nome do banco de dados |
| `FLASK_DEBUG` | Não | Ativa modo debug do Flask (`true`/`false`, padrão `false`) |

Nunca commite o arquivo `.env`. O `.gitignore` já o exclui.

## Endpoints

### Tarefas (FastAPI)

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/tasks/` | Lista todas as tarefas |
| `POST` | `/api/tasks/` | Cria tarefa e retorna desculpa do Gemini |
| `POST` | `/api/tasks/{id}/decide` | Aceitar procrastinação ou manter data |
| `PATCH` | `/api/tasks/{id}/complete` | Marcar como concluída |
| `DELETE` | `/api/tasks/{id}` | Deletar tarefa |
| `GET` | `/api/tasks/stats` | Métricas de improdutividade |

### Gato

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/cat/` | Estado atual do gato (humor, felicidade, destruição) |
| `POST` | `/api/cat/feed` | Alimentar o gato |

### Notificações

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/notifications/` | Lista notificações não lidas |
| `POST` | `/api/notifications/generate` | Gera uma notificação inútil |
| `POST` | `/api/notifications/mark-read` | Marca todas como lidas |
| `GET` | `/api/notifications/stream` | SSE — stream de notificações a cada 30s |

### Gerenciamento de Tarefas (Flask)

Montado em `/flask` dentro do mesmo servidor FastAPI (porta `8000`).

Campos da tarefa:

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | string | ObjectId do MongoDB |
| `nome` | string | Nome da tarefa |
| `data_termino` | string (ISO 8601) | Data de término |
| `concluida` | boolean | Se a tarefa foi concluída |
| `vezes_adiada` | integer | Número de vezes que foi adiada |
| `desistiu` | boolean | Se o usuário desistiu da tarefa |

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/flask/tasks/` | Lista todas as tarefas |
| `GET` | `/flask/tasks/{id}` | Busca uma tarefa |
| `POST` | `/flask/tasks/` | Cria uma tarefa |
| `PUT` | `/flask/tasks/{id}` | Substitui a tarefa inteira |
| `PATCH` | `/flask/tasks/{id}` | Atualiza campos parcialmente |
| `DELETE` | `/flask/tasks/{id}` | Deleta uma tarefa |

**Exemplos de uso com os botões do frontend:**

```js
// Adiar 1 dia
PATCH /flask/tasks/{id}
{ "data_termino": "2025-12-02T10:00:00", "vezes_adiada": 2 }

// Desistir
PATCH /flask/tasks/{id}
{ "desistiu": true }

// Concluir
PATCH /flask/tasks/{id}
{ "concluida": true }
```

## Exemplo de uso

**Criar tarefa:**
```bash
curl -X POST http://localhost:8000/api/tasks/ \
  -H "Content-Type: application/json" \
  -d '{"title": "Refatorar código legado", "scheduled_at": "2026-06-01T10:00:00"}'
```

**Resposta:**
```json
{
  "task": { "id": 1, "title": "Refatorar código legado", "status": "pending" },
  "excuse": "Mercúrio retrógrado está causando instabilidade nos commits.",
  "suggested_postpone_hours": 48,
  "suggested_new_date": "2026-06-03T10:00:00",
  "confidence": 94
}
```

**Aceitar procrastinação:**
```bash
curl -X POST http://localhost:8000/api/tasks/1/decide \
  -H "Content-Type: application/json" \
  -d '{"accept_postponement": true, "new_date": "2026-06-03T10:00:00"}'
```

**Criar tarefa (Flask):**
```bash
curl -X POST http://localhost:8000/flask/tasks/ \
  -H "Content-Type: application/json" \
  -d '{"nome": "Estudar Python", "data_termino": "2025-12-01T10:00:00"}'
```

## Estrutura

```
├── main.py                        # App FastAPI + Flask montado via WSGIMiddleware
├── models.py                      # Modelos: Task, CatState, Notification
├── database.py                    # Conexão Motor (async) com MongoDB
├── routers/
│   ├── tasks.py                   # CRUD de tarefas + lógica de decisão (FastAPI)
│   ├── cat.py                     # Estado e alimentação do gato
│   ├── notifications.py           # Notificações + SSE stream
│   └── flask_tasks.py             # Endpoints Flask de gerenciamento de tarefas
├── services/
│   ├── gemini_service.py          # Integração Gemini 2.5 Flash com fallbacks
│   ├── cat_service.py             # Cálculo de humor/destruição do gato
│   ├── notification_service.py    # Pool de fatos inúteis
│   └── flask_tasks_service.py     # Lógica de negócio das tarefas Flask
├── requirements.txt
├── .env.example
└── .gitignore
```

## Lógica do gato

O estado do gato é recalculado a cada operação de tarefa:

| Humor | Felicidade | Comportamento |
|---|---|---|
| 😸 Happy | 75–100% | Normal, faz biscoitinhos |
| 🐱 Neutral | 50–75% | Observa com julgamento moderado |
| 😾 Grumpy | 25–50% | Derruba sua caneca de propósito |
| 👹 Monster | 0–25% | Destrói seu workspace (mensagens aleatórias) |

O campo `destruction_level` (0–5) acumula ações destrutivas quando o gato está no estado monster.
