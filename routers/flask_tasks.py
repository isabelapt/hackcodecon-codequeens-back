from flask import Blueprint, request, jsonify, g
from services import flask_tasks_service as svc

bp = Blueprint("tasks", __name__, url_prefix="/tasks")


def col():
    return g.db["flask_tasks"]


@bp.get("/")
def get_all():
    return jsonify(svc.get_all(col()))


@bp.get("/<task_id>")
def get_one(task_id):
    task = svc.get_one(col(), task_id)
    if not task:
        return jsonify({"error": "Tarefa não encontrada"}), 404
    return jsonify(task)


@bp.post("/")
def create():
    body = request.get_json()
    if not body or not body.get("nome"):
        return jsonify({"error": "Campo 'nome' é obrigatório"}), 400
    return jsonify(svc.create(col(), body)), 201


@bp.put("/<task_id>")
def put(task_id):
    body = request.get_json()
    if not body or not body.get("nome"):
        return jsonify({"error": "Campo 'nome' é obrigatório"}), 400
    result = svc.put(col(), task_id, body)
    if not result:
        return jsonify({"error": "Tarefa não encontrada"}), 404
    return jsonify(result)


@bp.patch("/<task_id>")
def patch(task_id):
    body = request.get_json()
    allowed = {"nome", "data_termino", "concluida", "vezes_adiada", "desistiu"}
    updates = {k: v for k, v in body.items() if k in allowed}
    if not updates:
        return jsonify({"error": "Nenhum campo válido para atualizar"}), 400
    result = svc.patch(col(), task_id, updates)
    if not result:
        return jsonify({"error": "Tarefa não encontrada"}), 404
    return jsonify(result)


@bp.delete("/<task_id>")
def delete(task_id):
    result = svc.delete(col(), task_id)
    if not result:
        return jsonify({"error": "Tarefa não encontrada"}), 404
    return jsonify({"message": "Tarefa deletada", "id": task_id})
