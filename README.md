# 🐱 Chewie The Cat — Backend

> **Um projeto criado para o Hackathon CodeCon Universe** 🚀

## O que é isso? 🤔

Bem-vindo ao **Goose Cat**, o gerenciador de tarefas que sabe exatamente como te desmotivar! 

Se você é aquele tipo de pessoa que procrastina olhando para um gatinho fofo, então este projeto é **perfeito** para você. Aqui, temos um gatinho virtual que não só observa suas tarefas como também **se transforma em monstro** quando você não é produtivo. Além disso, toda vez que você não consegue fazer uma tarefa, o **Gemini (nossa IA favorita) gera desculpas criativas** para justificar sua preguiça. 

Sim, é como ter um amigo que o julga passivamente enquanto oferece motivação de forma cáustica. 😹

---

## ⚙️ Tech Stack

| Componente | Tecnologia |
|---|---|
| **Runtime** | Python 3.11+ |
| **Framework API** | FastAPI |
| **Framework Secundário** | Flask (integrado via `a2wsgi`) |
| **Banco de Dados** | MongoDB (Motor para async + PyMongo para sync) |
| **Gerador de Desculpas** | Google Gemini 2.5 Flash |
| **Agendador de Tarefas** | APScheduler |

---

## 📋 Pré-requisitos

Antes de começar, você vai precisar de:

1. **Chave da Gemini API** (sim, é de graça!)
   - Gere em [aistudio.google.com/apikey](https://aistudio.google.com/apikey)

2. **MongoDB** — escolha seu poison:
   - **MongoDB Atlas** ☁️ (recomendado para produção/apresentação) — cloud grátis
   - **MongoDB local** 💻 (para desenvolvimento local)

3. **Docker** (opcional, mas facilita a vida)

---

## 🚀 Setup: Opção 1 — MongoDB Atlas + Docker (O caminho fácil)

Se você quer que tudo "just work", use Docker com MongoDB Atlas:

```bash
# 1. Clone o repositório
git clone https://github.com/isabelapt/hackcodecon-codequeens-back.git
cd hackcodecon-codequeens-back

# 2. Crie seu arquivo .env (copie o exemplo)
cp .env.example .env

# 3. Configure no .env:
#    - GEMINI_API_KEY (da chave que você gerou)
#    - MONGODB_URL (connection string do Atlas)
#    - MONGODB_DB (nome do seu banco)

# 4. Levante o servidor com Docker
docker compose up --build
```

Pronto! Acesse `http://localhost:8000/docs` para a **documentação interativa** da API. 📚

### 📌 Gerando a connection string do MongoDB Atlas

1. Crie uma conta em [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
2. Deploy um cluster FREE
3. Clique em **Connect** → **Drivers** → **Python**
4. Copie a connection string e jogue em `MONGODB_URL` do `.env`

---

## 🛠️ Setup: Opção 2 — Desenvolvimento Local (Sem Docker)

Quer brincar sem Docker? Sem problema!

```bash
# 1. Instale MongoDB Community (se ainda não tem):
#    https://www.mongodb.com/try/download/community
#    Abra um terminal separado e execute: mongod

# 2. Setup do projeto Python
py -3.11 -m venv venv

# Ative o ambiente virtual:
source venv/bin/activate   # Linux / macOS
venv\Scripts\activate      # Windows

# 3. Instale as dependências
py -3.11 -m pip install -r requirements.txt

# 4. Configure o .env
cp .env.example .env
# Preencha MONGODB_URL, MONGODB_DB e GEMINI_API_KEY

# 5. Inicie o servidor
py -3.11 -m uvicorn main:app --reload --port 8000
```

Acesse `http://localhost:8000/docs` e aproveite! 🎉

### ⚠️ Troubleshooting Python

- **Use Python 3.11!** Versões mais novas (3.13+) têm problemas com `pydantic-core`.
- Se tiver erros de SSL ao instalar dependências:
  ```bash
  py -3.11 -m pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org
  ```

---

## 🔑 Variáveis de Ambiente

| Variável | Obrigatória | O que é |
|---|---|---|
| `GEMINI_API_KEY` | ✅ | Sua chave de acesso à API do Google Gemini |
| `MONGODB_URL` | ✅ | A connection string do seu MongoDB (Atlas ou local) |
| `MONGODB_DB` | ✅ | Nome do banco de dados (ex: `goosecat`) |
| `FLASK_DEBUG` | ❌ | Ativa modo debug do Flask (`true`/`false`, padrão: `false`) |

**Dica:** Nunca commite o `.env`! O `.gitignore` já cuida disso. 🔒

---

## 🔌 Endpoints da API

### 🐱 Tarefas (FastAPI)

> **Nota:** As rotas `/api/tasks/` são mantidas para compatibilidade com o Gemini (geração de desculpas). O gerenciamento principal de tarefas é feito via Flask em `/flask/tasks/`.

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

O estado do gato é recalculado automaticamente após cada operação nas tarefas Flask (`POST`, `PUT`, `PATCH`, `DELETE`), lendo da coleção `flask_tasks`:

| Ação na tarefa | Efeito no gato |
|---|---|
| `concluida: true` | ↑ felicidade |
| `desistiu: true` | ↑ irritação |
| `vezes_adiada` aumenta | ↑ irritação (peso menor que desistir) |

| Humor | Felicidade | Comportamento |
|---|---|---|
| 😸 Happy | 75–100% | Normal, faz biscoitinhos |
| 🐱 Neutral | 50–75% | Observa com julgamento moderado |
| 😾 Grumpy | 25–50% | Derruba sua caneca de propósito |
| 👹 Monster | 0–25% | Destrói seu workspace (mensagens aleatórias) |

O campo `destruction_level` (0–5) acumula ações destrutivas quando o gato está no estado monster.

---

## 🔧 Instalação com MongoDB Atlas

Se você quer uma documentação mais detalhada sobre como configurar o MongoDB Atlas, veja [MONGODB_ATLAS_SETUP.md](./MONGODB_ATLAS_SETUP.md).

---

## 📝 Licença

Este projeto está licenciado sob a [MIT License](LICENSE).

---

## 👑 Agradecimentos Especiais

Este projeto foi desenvolvido com ❤️ pela equipe **Code Queens** durante o **Hackathon CodeCon Universe**.

Um agradecimento especial aos membros da equipe que tornaram isso possível:

- **Erica** — Nossa PM e Designer UX/UI ✨ (visão do projeto + interface linda)
- **Isabela** — Dev Back-end 💻 (arquitetura robusta do servidor)
- **Maria Eduarda** — Dev Full-Stack 🚀 (conectando front e back com maestria)
- **Marina** — Dev Front-end 🎨 (tornando o gato irresistível)
- **Tissiany** — Dev Front-end 💅 (polimento final da interface)

Sem essa equipe incrível, o Goose Cat seria apenas... um gato comum. 😹

---

**Desenvolvido com café, sem paciência e muito humor! ☕😄**
