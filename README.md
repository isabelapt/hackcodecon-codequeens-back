# Goose Cat — Backend

API REST do Goose Cat, o gerenciador de tarefas que trabalha contra você.
Recebe tarefas, consulta o Gemini para gerar desculpas de procrastinação e gerencia um gatinho virtual que vira monstro quando você não é produtivo.

## Stack

| | |
|---|---|
| **Runtime** | Python 3.11+ |
| **Framework** | FastAPI |
| **Banco** | MongoDB via Motor (async) |
| **IA** | Google Gemini 2.5 Flash |
| **Agendamento** | APScheduler |

## Pré-requisitos

- Chave da Gemini API — grátis em [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
- Docker + Docker Compose **ou** Python 3.11+ com MongoDB local

## Rodando com Docker (recomendado)

Sobe o backend e o MongoDB com um único comando:

```bash
# Na raiz do repositório (onde está o docker-compose.yml)
cp backend/.env.example backend/.env
# Edite backend/.env e preencha GEMINI_API_KEY

docker compose up --build
```

Acesse `http://localhost:8000/docs` para a documentação interativa.

> Os dados do MongoDB ficam no volume `mongo_data` — persistem entre reinicializações.

## Rodando localmente (sem Docker)

```bash
# 1. Instale as dependências
python -m venv venv
source venv/bin/activate   # Linux / Mac
venv\Scripts\activate      # Windows
pip install -r requirements.txt

# 2. Configure as variáveis de ambiente
cp .env.example .env
# Edite .env: GEMINI_API_KEY, MONGODB_URL, MONGODB_DB

# 3. Certifique-se que o MongoDB está rodando em localhost:27017

# 4. Inicie o servidor
uvicorn main:app --reload --port 8000
```

## Variáveis de ambiente

| Variável | Obrigatória | Descrição |
|---|---|---|
| `GEMINI_API_KEY` | Sim | Chave da API do Google AI Studio |

Nunca commite o arquivo `.env`. O `.gitignore` já o exclui.

## Endpoints

### Tarefas

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

## Estrutura

```
backend/
├── main.py                  # App FastAPI, CORS, scheduler, lifespan
├── models.py                # Modelos SQLAlchemy: Task, CatState, Notification
├── database.py              # Engine SQLite, sessão, init_db
├── routers/
│   ├── tasks.py             # CRUD de tarefas + lógica de decisão
│   ├── cat.py               # Estado e alimentação do gato
│   └── notifications.py    # Notificações + SSE stream
├── services/
│   ├── gemini_service.py   # Integração Gemini 2.5 Flash com fallbacks
│   ├── cat_service.py      # Cálculo de humor/destruição do gato
│   └── notification_service.py  # Pool de fatos inúteis
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
