from flask import Blueprint, request, jsonify, g
from bson import ObjectId
from bson.errors import InvalidId
from services import flask_tasks_service as svc
from datetime import datetime

bp = Blueprint("tasks", __name__, url_prefix="/tasks")

_MAX_NOME_LEN = 500
_MAX_DATA_TERMINO_LEN = 100


def col():
    return g.db["flask_tasks"]


def _validate_object_id(task_id: str):
    try:
        ObjectId(task_id)
    except (InvalidId, TypeError):
        return False
    return True


@bp.get("/")
def get_all():
    return jsonify(svc.get_all(col()))


@bp.get("/<task_id>")
def get_one(task_id):
    if not _validate_object_id(task_id):
        return jsonify({"error": "ID inválido"}), 400
    task = svc.get_one(col(), task_id)
    if not task:
        return jsonify({"error": "Tarefa não encontrada"}), 404
    return jsonify(task)


@bp.post("/")
def create():
    body = request.get_json(silent=True)
    if not body or not body.get("nome"):
        return jsonify({"error": "Campo 'nome' é obrigatório"}), 400

    nome = body["nome"]
    if not isinstance(nome, str) or len(nome) > _MAX_NOME_LEN:
        return jsonify({"error": f"'nome' deve ter no máximo {_MAX_NOME_LEN} caracteres"}), 400

    data_termino = body.get("data_termino")
    if data_termino and (not isinstance(data_termino, str) or len(data_termino) > _MAX_DATA_TERMINO_LEN):
        return jsonify({"error": "Campo 'data_termino' inválido"}), 400

    doc = {
        "nome": nome,
        "data_termino": data_termino,
        "concluida": False,
        "vezes_adiada": 0,
        "desistiu": False,
        "desculpa": None,
        "created_at": datetime.utcnow(),
        "completed_at": None,
    }

    created = svc.create(col(), doc)
    excuse_data = svc.get_excuse(
        nome,
        data_termino,
    )

    svc.patch(col(), created["id"], {
        "desculpa": excuse_data["excuse"]
    })

    created["desculpa"] = excuse_data["excuse"]

    return jsonify({
        "task": created,
        "excuse": excuse_data["excuse"],
        "suggested_postpone_hours": excuse_data["suggested_postpone_hours"],
        "suggested_new_date": excuse_data["suggested_new_date"],
        "confidence": excuse_data["confidence"],
    }), 201


@bp.put("/<task_id>")
def put(task_id):
    if not _validate_object_id(task_id):
        return jsonify({"error": "ID inválido"}), 400
    body = request.get_json(silent=True)
    if not body or not body.get("nome"):
        return jsonify({"error": "Campo 'nome' é obrigatório"}), 400
    nome = body["nome"]
    if not isinstance(nome, str) or len(nome) > _MAX_NOME_LEN:
        return jsonify({"error": f"'nome' deve ter no máximo {_MAX_NOME_LEN} caracteres"}), 400
    result = svc.put(col(), task_id, body)
    if not result:
        return jsonify({"error": "Tarefa não encontrada"}), 404
    return jsonify(result)


@bp.patch("/<task_id>")
def patch(task_id):
    if not _validate_object_id(task_id):
        return jsonify({"error": "ID inválido"}), 400
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "Corpo da requisição inválido"}), 400
    allowed = {"nome", "data_termino", "concluida", "vezes_adiada", "desistiu"}
    updates = {k: v for k, v in body.items() if k in allowed}
    if not updates:
        return jsonify({"error": "Nenhum campo válido para atualizar"}), 400
    if "nome" in updates:
        if not isinstance(updates["nome"], str) or len(updates["nome"]) > _MAX_NOME_LEN:
            return jsonify({"error": f"'nome' deve ter no máximo {_MAX_NOME_LEN} caracteres"}), 400
    result = svc.patch(col(), task_id, updates)
    if not result:
        return jsonify({"error": "Tarefa não encontrada"}), 404
    return jsonify(result)


@bp.delete("/<task_id>")
def delete(task_id):
    if not _validate_object_id(task_id):
        return jsonify({"error": "ID inválido"}), 400
    result = svc.delete(col(), task_id)
    if not result:
        return jsonify({"error": "Tarefa não encontrada"}), 404
    return jsonify({"message": "Tarefa deletada", "id": task_id})
