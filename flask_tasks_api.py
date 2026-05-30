from flask import Flask, request, jsonify, g
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime, timezone
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
MONGODB_DB = os.getenv("MONGODB_DB")

if not MONGODB_URL or not MONGODB_DB:
    raise RuntimeError("MONGODB_URL e MONGODB_DB devem estar definidos no .env")

app = Flask(__name__)


def get_col():
    if "client" not in g:
        g.client = MongoClient(MONGODB_URL)
    return g.client[MONGODB_DB]["flask_tasks"]


@app.teardown_appcontext
def close_client(exc):
    client = g.pop("client", None)
    if client is not None:
        client.close()


def serialize(task):
    task["id"] = str(task.pop("_id"))
    return task


# GET ALL
@app.get("/tasks")
def get_all():
    return jsonify([serialize(t) for t in get_col().find()])


# GET ONE
@app.get("/tasks/<task_id>")
def get_one(task_id):
    task = get_col().find_one({"_id": ObjectId(task_id)})
    if not task:
        return jsonify({"error": "Tarefa não encontrada"}), 404
    return jsonify(serialize(task))


# POST
@app.post("/tasks")
def create():
    body = request.get_json()
    if not body or not body.get("nome"):
        return jsonify({"error": "Campo 'nome' é obrigatório"}), 400

    task = {
        "nome": body["nome"],
        "data_termino": body.get("data_termino"),
        "concluida": False,
        "vezes_adiada": 0,
        "desistiu": False,
        "criada_em": datetime.now(timezone.utc).isoformat(),
    }
    result = get_col().insert_one(task)
    task["id"] = str(result.inserted_id)
    task.pop("_id", None)
    return jsonify(task), 201


# PUT — substitui o documento inteiro
@app.put("/tasks/<task_id>")
def put(task_id):
    body = request.get_json()
    if not body or not body.get("nome"):
        return jsonify({"error": "Campo 'nome' é obrigatório"}), 400

    updated = {
        "nome": body["nome"],
        "data_termino": body.get("data_termino"),
        "concluida": body.get("concluida", False),
        "vezes_adiada": body.get("vezes_adiada", 0),
        "desistiu": body.get("desistiu", False),
    }
    result = get_col().find_one_and_replace(
        {"_id": ObjectId(task_id)}, updated, return_document=True
    )
    if not result:
        return jsonify({"error": "Tarefa não encontrada"}), 404
    return jsonify(serialize(result))


# PATCH — atualiza campos parcialmente
@app.patch("/tasks/<task_id>")
def patch(task_id):
    body = request.get_json()
    allowed = {"nome", "data_termino", "concluida", "vezes_adiada", "desistiu"}
    updates = {k: v for k, v in body.items() if k in allowed}
    if not updates:
        return jsonify({"error": "Nenhum campo válido para atualizar"}), 400

    result = get_col().find_one_and_update(
        {"_id": ObjectId(task_id)}, {"$set": updates}, return_document=True
    )
    if not result:
        return jsonify({"error": "Tarefa não encontrada"}), 404
    return jsonify(serialize(result))


# DELETE
@app.delete("/tasks/<task_id>")
def delete(task_id):
    result = get_col().find_one_and_delete({"_id": ObjectId(task_id)})
    if not result:
        return jsonify({"error": "Tarefa não encontrada"}), 404
    return jsonify({"message": "Tarefa deletada", "id": task_id})


if __name__ == "__main__":
    app.run(port=5000, debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
