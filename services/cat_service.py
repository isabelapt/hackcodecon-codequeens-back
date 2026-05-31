from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
import random

MOOD_DESCRIPTIONS = {
    "happy":   "Seu gato está radiante! Ele está fazendo biscoitinhos e cantando.",
    "neutral": "Seu gato está neutro. Observando você com olhos semicerrados de julgamento.",
    "grumpy":  "Seu gato está mal-humorado. Ele derrubou sua caneca de café de propósito.",
    "monster": "SEU GATO VIROU UM MONSTRO. ELE ESTÁ DESTRUINDO SEU WORKSPACE.",
}

DESTRUCTION_MESSAGES = [
    "O gatinho deletou um comentário do seu código.",
    "O gatinho trocou todos os seus 'true' por 'false'.",
    "O gatinho adicionou um `time.sleep(5)` em produção.",
    "O gatinho renomeou sua variável principal para 'coisaNome2'.",
    "O gatinho commitou com a mensagem 'asdfghjkl'.",
    "O gatinho abriu 47 abas do Stack Overflow e não fechou nenhuma.",
]


def _compute_mood_metrics(ativas, pendentes, desistidas, adiadas):
    """Calcula (happiness, hunger) a partir das pendências atuais.

    Modelo de pressão (tetos baixos no histórico para o gato ser RECUPERÁVEL:
    ao zerar as pendências ele volta a ficar feliz, independente do histórico):
      - tarefas pendentes  → −15 cada (teto 75)   ← lever principal, muda a cada ação
      - adiamentos         → −2  cada (teto 8)
      - desistências       → −3  cada (teto 10)
    Penalidade fixa máx. de histórico = 18 → lista limpa (0 pendentes) ⇒ ~82 (happy).
    Lista sem tarefas = estado neutro inicial (70).
    """
    if ativas == 0 and desistidas == 0:
        return 70.0, 30.0

    pen_pendentes = min(75, pendentes * 15)
    pen_adiadas = min(8, adiadas * 2)
    pen_desist = min(10, desistidas * 3)
    happiness = max(0.0, 100.0 - pen_pendentes - pen_adiadas - pen_desist)

    hunger = min(100.0, pendentes * 15 + min(20, adiadas * 2) + min(20, desistidas * 3))
    return happiness, hunger


def recalculate_cat_sync(db) -> dict:
    """Versão síncrona (PyMongo) — chamada pelas rotas Flask."""
    # Humor por "pressão de tarefas em aberto": cada tarefa pendente, adiada ou
    # abandonada deixa o gato mais triste. Como depende da quantidade ATUAL de
    # pendências (e não da razão sobre todo o histórico), cada ação do usuário
    # — concluir, criar, adiar, desistir — move o humor de forma perceptível.
    ativas = db.flask_tasks.count_documents({"desistiu": {"$ne": True}})
    pendentes = db.flask_tasks.count_documents({"desistiu": {"$ne": True}, "concluida": {"$ne": True}})
    desistidas = db.flask_tasks.count_documents({"desistiu": True})
    adiadas = sum(t.get("vezes_adiada", 0) for t in db.flask_tasks.find({"desistiu": {"$ne": True}}, {"vezes_adiada": 1}))

    happiness, hunger = _compute_mood_metrics(ativas, pendentes, desistidas, adiadas)

    if happiness >= 75:
        mood = "happy"
    elif happiness >= 50:
        mood = "neutral"
    elif happiness >= 25:
        mood = "grumpy"
    else:
        mood = "monster"

    update = {
        "mood": mood,
        "happiness": round(happiness, 1),
        "hunger": round(hunger, 1),
        "updated_at": datetime.utcnow(),
    }

    if mood == "monster" and random.random() < 0.3:
        cat = db.cat_state.find_one({"_id": "main"}) or {}
        new_level = min(5, cat.get("destruction_level", 0) + 1)
        update["destruction_level"] = new_level
        msg = random.choice(DESTRUCTION_MESSAGES)
        db.notifications.insert_one({
            "message": f"💥 DESTRUIÇÃO NÍVEL {new_level}: {msg}",
            "category": "cat_destruction",
            "is_read": False,
            "created_at": datetime.utcnow(),
        })

    db.cat_state.update_one({"_id": "main"}, {"$set": update}, upsert=True)
    return db.cat_state.find_one({"_id": "main"})


async def recalculate_cat(db: AsyncIOMotorDatabase) -> dict:
    # mesma lógica de "pressão de tarefas em aberto" da versão síncrona
    ativas = await db.flask_tasks.count_documents({"desistiu": {"$ne": True}})
    pendentes = await db.flask_tasks.count_documents({"desistiu": {"$ne": True}, "concluida": {"$ne": True}})
    desistidas = await db.flask_tasks.count_documents({"desistiu": True})
    adiadas = 0
    async for t in db.flask_tasks.find({"desistiu": {"$ne": True}}, {"vezes_adiada": 1}):
        adiadas += t.get("vezes_adiada", 0)

    happiness, hunger = _compute_mood_metrics(ativas, pendentes, desistidas, adiadas)

    if happiness >= 75:
        mood = "happy"
    elif happiness >= 50:
        mood = "neutral"
    elif happiness >= 25:
        mood = "grumpy"
    else:
        mood = "monster"

    update = {
        "mood": mood,
        "happiness": round(happiness, 1),
        "hunger": round(hunger, 1),
        "updated_at": datetime.utcnow(),
    }

    if mood == "monster" and random.random() < 0.3:
        cat = await db.cat_state.find_one({"_id": "main"})
        new_level = min(5, (cat or {}).get("destruction_level", 0) + 1)
        update["destruction_level"] = new_level
        msg = random.choice(DESTRUCTION_MESSAGES)
        await db.notifications.insert_one({
            "message": f"💥 DESTRUIÇÃO NÍVEL {new_level}: {msg}",
            "category": "cat_destruction",
            "is_read": False,
            "created_at": datetime.utcnow(),
        })

    await db.cat_state.update_one({"_id": "main"}, {"$set": update})
    return await db.cat_state.find_one({"_id": "main"})


async def feed_cat(db: AsyncIOMotorDatabase) -> dict:
    cat = await db.cat_state.find_one({"_id": "main"})
    new_happiness = min(100.0, cat.get("happiness", 50) + 15)
    new_hunger = max(0.0, cat.get("hunger", 50) - 20)
    await db.cat_state.update_one(
        {"_id": "main"},
        {"$set": {
            "happiness": new_happiness,
            "hunger": new_hunger,
            "last_fed_at": datetime.utcnow(),
        }},
    )
    return await recalculate_cat(db)
