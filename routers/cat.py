from fastapi import APIRouter
from database import get_db
from services.cat_service import recalculate_cat, feed_cat, MOOD_DESCRIPTIONS

router = APIRouter(prefix="/cat", tags=["cat"])


@router.get("/")
async def get_cat():
    db = get_db()
    cat = await recalculate_cat(db)
    return {
        "mood": cat["mood"],
        "happiness": cat["happiness"],
        "hunger": cat["hunger"],
        "destruction_level": cat.get("destruction_level", 0),
        "description": MOOD_DESCRIPTIONS.get(cat["mood"], ""),
        "last_fed_at": cat["last_fed_at"].isoformat() if cat.get("last_fed_at") else None,
    }


@router.post("/feed")
async def feed():
    db = get_db()
    cat = await feed_cat(db)
    return {
        "mood": cat["mood"],
        "happiness": cat["happiness"],
        "hunger": cat["hunger"],
        "message": "Você alimentou o gato com uma tarefa concluída imaginária. Ele ficou 15% mais feliz.",
    }
