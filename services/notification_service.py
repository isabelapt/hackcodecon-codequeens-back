from motor.motor_asyncio import AsyncIOMotorDatabase
import random

from services.shared import serialize_doc, build_notification_doc

USELESS_FACTS = [
    "🌍 URGENTE: A Terra continua redonda. Situação monitorada.",
    "💧 ALERTA CRÍTICO: Água ainda é líquida em temperatura ambiente.",
    "🔵 BREAKING NEWS: O céu permanece azul durante o dia.",
    "⚽ ATUALIZAÇÃO IMPORTANTE: Bolas continuam redondas. Equipe técnica confirmou.",
    "🔥 AVISO DE SEGURANÇA: Fogo ainda queima. Evite contato.",
    "🌙 NOTÍCIA VERIFICADA: A Lua ainda existe. Vista ontem à noite.",
    "☀️ ALERTA SOLAR: O Sol nasceu hoje de manhã. Previsão: nascer amanhã também.",
    "🐟 DESCOBERTA CIENTÍFICA: Peixes ainda respiram na água.",
    "🧊 CONFIRMADO: Gelo derrete quando aquecido. Pesquisadores aliviados.",
    "📐 MATEMÁTICA: 2 + 2 continua sendo 4. Consenso mundial mantido.",
    "🌿 BOTÂNICA: Plantas ainda realizam fotossíntese. Verde confirmado.",
    "💤 SAÚDE: Humanos precisam dormir. Novidade: isso não mudou.",
    "⚡ FÍSICA: Eletricidade ainda flui em circuitos fechados.",
    "🍎 GRAVIDADE: Objetos continuam caindo quando soltos. Newton sem comentários.",
    "🖥️ DEV ALERT: JavaScript ainda tem comportamentos inesperados. Surpresa: não é surpresa.",
    "☕ CRÍTICO: Café ainda é quente. Cuidado ao tomar.",
    "🐈 FELINO: Gatos ainda aterrisam de pé. Física confirmada.",
    "📊 ESTATÍSTICA: 97% dos devs dizem que vão fazer depois. O 1% restante mentiu.",
    "🎯 MOTIVAÇÃO: 'Feito é melhor que perfeito.' Mas deixar pra depois é melhor que feito.",
]


async def generate_useless_notification(db: AsyncIOMotorDatabase) -> dict:
    msg = random.choice(USELESS_FACTS)
    doc = build_notification_doc(msg, "useless_fact")
    result = await db.notifications.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return doc


async def get_unread_notifications(db: AsyncIOMotorDatabase, limit: int = 20) -> list:
    cursor = db.notifications.find({"is_read": False}).sort("created_at", -1).limit(limit)
    docs = []
    async for doc in cursor:
        docs.append(serialize_doc(doc, ["created_at"]))
    return docs


async def mark_all_read(db: AsyncIOMotorDatabase):
    await db.notifications.update_many({"is_read": False}, {"$set": {"is_read": True}})
