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


def recalculate_cat_sync(db) -> dict:
    """Versão síncrona (PyMongo) — chamada pelas rotas Flask."""
    total = db.flask_tasks.count_documents({})
    done = db.flask_tasks.count_documents({"concluida": True})
    desistiu = db.flask_tasks.count_documents({"desistiu": True})
    adiadas = sum(t.get("vezes_adiada", 0) for t in db.flask_tasks.find({}, {"vezes_adiada": 1}))

    if total == 0:
        happiness = 70.0
        hunger = 30.0
    else:
        happiness = min(100.0, (done / total) * 120)
        hunger = min(100.0, ((desistiu + adiadas * 0.3) / max(total, 1)) * 100)

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

    cat = db.cat_state.find_one({"_id": "main"}) or {}
    current_level = cat.get("destruction_level", 0)
    if mood == "monster":
        if random.random() < 0.3:
            new_level = min(5, current_level + 1)
            update["destruction_level"] = new_level
            msg = random.choice(DESTRUCTION_MESSAGES)
            db.notifications.insert_one({
                "message": f"💥 DESTRUIÇÃO NÍVEL {new_level}: {msg}",
                "category": "cat_destruction",
                "is_read": False,
                "created_at": datetime.utcnow(),
            })
    elif current_level > 0:
        # Gato saiu do modo monstro: o estrago "cicatriza" aos poucos
        # (−1 por recálculo) até zerar, mantendo o gato recuperável.
        update["destruction_level"] = current_level - 1

    db.cat_state.update_one({"_id": "main"}, {"$set": update}, upsert=True)
    return db.cat_state.find_one({"_id": "main"})


async def recalculate_cat(db: AsyncIOMotorDatabase) -> dict:
    total = await db.flask_tasks.count_documents({})
    done = await db.flask_tasks.count_documents({"concluida": True})
    desistiu = await db.flask_tasks.count_documents({"desistiu": True})
    adiadas = 0
    async for t in db.flask_tasks.find({}, {"vezes_adiada": 1}):
        adiadas += t.get("vezes_adiada", 0)

    if total == 0:
        happiness = 70.0
        hunger = 30.0
    else:
        happiness = min(100.0, (done / total) * 120)
        hunger = min(100.0, ((desistiu + adiadas * 0.3) / max(total, 1)) * 100)

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

    cat = await db.cat_state.find_one({"_id": "main"}) or {}
    current_level = cat.get("destruction_level", 0)
    if mood == "monster":
        if random.random() < 0.3:
            new_level = min(5, current_level + 1)
            update["destruction_level"] = new_level
            msg = random.choice(DESTRUCTION_MESSAGES)
            await db.notifications.insert_one({
                "message": f"💥 DESTRUIÇÃO NÍVEL {new_level}: {msg}",
                "category": "cat_destruction",
                "is_read": False,
                "created_at": datetime.utcnow(),
            })
    elif current_level > 0:
        # Gato saiu do modo monstro: o estrago "cicatriza" aos poucos
        # (−1 por recálculo) até zerar, mantendo o gato recuperável.
        update["destruction_level"] = current_level - 1

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
