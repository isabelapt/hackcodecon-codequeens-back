from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

from services.cat_mood import compute_cat_state, maybe_destruction_event
from services.shared import build_notification_doc

MOOD_DESCRIPTIONS = {
    "happy":   "Seu gato está radiante! Ele está fazendo biscoitinhos e cantando.",
    "neutral": "Seu gato está neutro. Observando você com olhos semicerrados de julgamento.",
    "grumpy":  "Seu gato está mal-humorado. Ele derrubou sua caneca de café de propósito.",
    "monster": "SEU GATO VIROU UM MONSTRO. ELE ESTÁ DESTRUINDO SEU WORKSPACE.",
}


def recalculate_cat_sync(db) -> dict:
    """Versão síncrona (PyMongo) — chamada pelas rotas Flask."""
    total = db.flask_tasks.count_documents({})
    done = db.flask_tasks.count_documents({"concluida": True})
    desistiu = db.flask_tasks.count_documents({"desistiu": True})
    adiadas = sum(t.get("vezes_adiada", 0) for t in db.flask_tasks.find({}, {"vezes_adiada": 1}))

    mood, happiness, hunger = compute_cat_state(total, done, desistiu, adiadas)

    update = {
        "mood": mood,
        "happiness": happiness,
        "hunger": hunger,
        "updated_at": datetime.utcnow(),
    }

    cat = db.cat_state.find_one({"_id": "main"}) or {}
    fired, new_level, msg = maybe_destruction_event(cat.get("destruction_level", 0), mood)
    if fired:
        update["destruction_level"] = new_level
        db.notifications.insert_one(build_notification_doc(msg, "cat_destruction"))

    db.cat_state.update_one({"_id": "main"}, {"$set": update}, upsert=True)
    return db.cat_state.find_one({"_id": "main"})


async def recalculate_cat(db: AsyncIOMotorDatabase) -> dict:
    total = await db.flask_tasks.count_documents({})
    done = await db.flask_tasks.count_documents({"concluida": True})
    desistiu = await db.flask_tasks.count_documents({"desistiu": True})
    adiadas = 0
    async for t in db.flask_tasks.find({}, {"vezes_adiada": 1}):
        adiadas += t.get("vezes_adiada", 0)

    mood, happiness, hunger = compute_cat_state(total, done, desistiu, adiadas)

    update = {
        "mood": mood,
        "happiness": happiness,
        "hunger": hunger,
        "updated_at": datetime.utcnow(),
    }

    cat = await db.cat_state.find_one({"_id": "main"})
    fired, new_level, msg = maybe_destruction_event((cat or {}).get("destruction_level", 0), mood)
    if fired:
        update["destruction_level"] = new_level
        await db.notifications.insert_one(build_notification_doc(msg, "cat_destruction"))

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
