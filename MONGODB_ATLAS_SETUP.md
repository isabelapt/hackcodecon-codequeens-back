# MongoDB Atlas — Guia Rápido

Instruções passo-a-passo para configurar MongoDB Atlas (cloud grátis) para a aplicação Goose Cat.

## Por que Atlas?

- ✅ Grátis (até 1GB dados)
- ✅ Sem instalação local necessária
- ✅ Funciona do notebook, desktop, servidor
- ✅ Ideal para demonstrações e hackathons

## Setup (5 minutos)

### 1. Criar conta no Atlas

- Acesse [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
- **Sign Up** (Google, GitHub ou email)
- Verifique seu email

### 2. Deploy um cluster FREE

- Clique em **Create a Deployment**
- Selecione **FREE** (M0 Sandbox)
- Cloud Provider: **AWS**
- Region: escolha a mais próxima (ex: `sa-east-1` para Brasil, `us-east-1` para EUA)
- Cluster Name: `goosecat` (ou nome que quiser)
- Clique **Create Deployment**

Aguarde ~10 segundos até ficar **Available** (verde).

### 3. Obter Connection String

- Clique em **Connect**
- Escolha **Drivers**
- Language: **Python**
- Driver: **PyMongo**

Você verá uma string assim:
```
mongodb+srv://seu_usuario:sua_senha@goosecat.xxxxx.mongodb.net/?retryWrites=true&w=majority
```

**Copie essa string** — é o `MONGODB_URL`.

### 4. Configurar no projeto

No arquivo `backend/.env`, coloque:

```env
GEMINI_API_KEY=sua_chave_aqui
MONGODB_URL=mongodb+srv://seu_usuario:sua_senha@goosecat.xxxxx.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB=goosecat
```

### 5. Rodar a aplicação

```bash
# Opção 1: Com Docker
docker compose up --build

# Opção 2: Sem Docker
cd backend
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Acesse: `http://localhost:8000/docs`

## Troubleshooting

**"Couldn't resolve host"**
- Certifique-se que a connection string é de Atlas (começa com `mongodb+srv://`)
- Verifique username/password

**"Authentication failed"**
- Copie a string de novo (teve erro no copy/paste)
- Teste no **Atlas → Connect** se a conexão funciona

**Dados sumindo?**
- Atlas grátis apaga clusters inativos por 60 dias
- Volte ao painel e clique em **Resume** se necessário

## Monitorar no Atlas

Depois de rodar a aplicação:
- Vá em **Browse Collections** para ver as tarefas criadas
- **Metrics** para ver tráfego e latência
- **Activity** para ver operações do banco

---

**Pronto!** Seu backend está rodando com MongoDB Atlas. 🚀
