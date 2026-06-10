import logging
import os
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient = None


def get_client() -> AsyncIOMotorClient:
    return _client


def get_db():
    return _client[os.getenv("MONGODB_DB", "goosecat")]


async def connect_db():
    global _client
    url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    _client = AsyncIOMotorClient(url)
    try:
        await _client.admin.command("ping")
        logger.info("Connected to MongoDB at %s", url.split("@")[-1] if "@" in url else url)
    except Exception:
        logger.error("Failed to connect to MongoDB", exc_info=True)
        raise
    await _seed_cat()


async def close_db():
    if _client:
        _client.close()


async def _seed_cat():
    db = get_db()
    exists = await db.cat_state.find_one({"_id": "main"})
    if not exists:
        await db.cat_state.insert_one({
            "_id": "main",
            "mood": "neutral",
            "happiness": 70.0,
            "hunger": 30.0,
            "destruction_level": 0,
            "last_fed_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })
