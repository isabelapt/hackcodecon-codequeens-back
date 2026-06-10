import logging
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId

from services.cat_service import recalculate_cat_sync
from services.gemini_service import get_procrastination_excuse

logger = logging.getLogger(__name__)


def serialize(task):
    if task is None:
        return None
    task["id"] = str(task.pop("_id"))
    return task


def get_all(col):
    return [serialize(t) for t in col.find()]


def get_one(col, task_id):
    try:
        oid = ObjectId(task_id)
    except (InvalidId, TypeError):
        return None
    return serialize(col.find_one({"_id": oid}))


def create(col, body):
    task = {
        "nome": body["nome"],
        "data_termino": body.get("data_termino"),
        "concluida": False,
        "vezes_adiada": 0,
        "desistiu": False,
        "criada_em": datetime.now(timezone.utc).isoformat(),
    }
    result = col.insert_one(task)
    task["id"] = str(result.inserted_id)
    task.pop("_id", None)
    recalculate_cat_sync(col.database)
    return task


def put(col, task_id, body):
    try:
        oid = ObjectId(task_id)
    except (InvalidId, TypeError):
        return None
    updated = {
        "nome": body["nome"],
        "data_termino": body.get("data_termino"),
        "concluida": body.get("concluida", False),
        "vezes_adiada": body.get("vezes_adiada", 0),
        "desistiu": body.get("desistiu", False),
    }
    result = col.find_one_and_replace({"_id": oid}, updated, return_document=True)
    if result:
        recalculate_cat_sync(col.database)
    return serialize(result) if result else None


def patch(col, task_id, updates):
    try:
        oid = ObjectId(task_id)
    except (InvalidId, TypeError):
        return None
    result = col.find_one_and_update(
        {"_id": oid}, {"$set": updates}, return_document=True
    )
    if result:
        recalculate_cat_sync(col.database)
    return serialize(result) if result else None


def delete(col, task_id):
    try:
        oid = ObjectId(task_id)
    except (InvalidId, TypeError):
        return None
    result = col.find_one_and_delete({"_id": oid})
    if result:
        recalculate_cat_sync(col.database)
    return serialize(result) if result else None

def get_excuse(nome, data_termino=None):
    """Generate an excuse synchronously (safe to call from Flask routes)."""
    import asyncio

    if isinstance(data_termino, str):
        try:
            data_termino = datetime.fromisoformat(data_termino)
        except ValueError:
            data_termino = None

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(
                asyncio.run,
                get_procrastination_excuse(nome, scheduled_at=data_termino),
            ).result(timeout=15)

    return asyncio.run(
        get_procrastination_excuse(nome, scheduled_at=data_termino)
    )
