from bson import ObjectId
from datetime import datetime, timezone


def serialize(task):
    task["id"] = str(task.pop("_id"))
    return task


def get_all(col):
    return [serialize(t) for t in col.find()]


def get_one(col, task_id):
    return serialize(col.find_one({"_id": ObjectId(task_id)}))


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
    return serialize(result) if result else None


def patch(col, task_id, updates):
    result = col.find_one_and_update(
        {"_id": ObjectId(task_id)}, {"$set": updates}, return_document=True
    )
    return serialize(result) if result else None


def delete(col, task_id):
    result = col.find_one_and_delete({"_id": ObjectId(task_id)})
    return serialize(result) if result else None
