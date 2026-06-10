from bson import ObjectId
from datetime import datetime, timezone
import asyncio

from services.gemini_service import get_procrastination_excuse
from services.cat_service import recalculate_cat_sync
from services.shared import serialize_doc


def get_all(col):
    return [serialize_doc(t) for t in col.find()]


def get_one(col, task_id):
    return serialize_doc(col.find_one({"_id": ObjectId(task_id)}))


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
    updated = {
        "nome": body["nome"],
        "data_termino": body.get("data_termino"),
        "concluida": body.get("concluida", False),
        "vezes_adiada": body.get("vezes_adiada", 0),
        "desistiu": body.get("desistiu", False),
    }
    result = col.find_one_and_replace({"_id": ObjectId(task_id)}, updated, return_document=True)
    if result:
        recalculate_cat_sync(col.database)
    return serialize_doc(result) if result else None


def patch(col, task_id, updates):
    result = col.find_one_and_update(
        {"_id": ObjectId(task_id)}, {"$set": updates}, return_document=True
    )
    if result:
        recalculate_cat_sync(col.database)
    return serialize_doc(result) if result else None


def delete(col, task_id):
    result = col.find_one_and_delete({"_id": ObjectId(task_id)})
    if result:
        recalculate_cat_sync(col.database)
    return serialize_doc(result) if result else None


async def build_excuse(nome, data_termino=None):
    if isinstance(data_termino, str):
        try:
            data_termino = datetime.fromisoformat(data_termino)
        except ValueError:
            data_termino = None
    return await get_procrastination_excuse(nome, data_termino)


def get_excuse(nome, data_termino=None):
    return asyncio.run(build_excuse(nome, data_termino))
