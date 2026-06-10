from fastapi import APIRouter
from datetime import datetime

from database import get_db
from models import TaskCreate, ProcrastinateDecision
from services.gemini_service import get_procrastination_excuse
from services.cat_service import recalculate_cat
from services.shared import serialize_doc, get_doc_or_404

router = APIRouter(prefix="/tasks", tags=["tasks"])

TASK_DATE_FIELDS = ["scheduled_at", "postponed_to", "created_at", "completed_at"]


async def _mark_overdue():
    db = get_db()
    now = datetime.utcnow()
    await db.tasks.update_many(
        {"status": "pending", "scheduled_at": {"$lt": now}},
        {"$set": {"status": "overdue"}},
    )


@router.get("/stats")
async def get_stats():
    db = get_db()
    await _mark_overdue()
    total = await db.tasks.count_documents({})
    done = await db.tasks.count_documents({"status": "done"})
    procrastinated = await db.tasks.count_documents({"status": "procrastinated"})
    overdue = await db.tasks.count_documents({"status": "overdue"})
    pending = await db.tasks.count_documents({"status": "pending"})
    return {
        "total": total,
        "done": done,
        "procrastinated": procrastinated,
        "overdue": overdue,
        "pending": pending,
        "procrastination_rate": round(procrastinated / total * 100 if total else 0, 1),
        "completion_rate": round(done / total * 100 if total else 0, 1),
        "not_done": total - done,
    }


@router.get("/")
async def list_tasks():
    db = get_db()
    await _mark_overdue()
    cursor = db.tasks.find().sort("created_at", -1)
    return [serialize_doc(t, TASK_DATE_FIELDS) async for t in cursor]


@router.post("/", status_code=201)
async def create_task(payload: TaskCreate):
    db = get_db()
    doc = {
        "title": payload.title,
        "description": payload.description or "",
        "scheduled_at": payload.scheduled_at,
        "postponed_to": None,
        "status": "pending",
        "excuse": None,
        "procrastination_count": 0,
        "created_at": datetime.utcnow(),
        "completed_at": None,
    }
    result = await db.tasks.insert_one(doc)
    task_id = result.inserted_id

    excuse_data = await get_procrastination_excuse(
        payload.title, payload.description or "", payload.scheduled_at
    )
    await db.tasks.update_one({"_id": task_id}, {"$set": {"excuse": excuse_data["excuse"]}})
    task = await db.tasks.find_one({"_id": task_id})

    return {
        "task": serialize_doc(task, TASK_DATE_FIELDS),
        "excuse": excuse_data["excuse"],
        "suggested_postpone_hours": excuse_data["suggested_postpone_hours"],
        "suggested_new_date": excuse_data["suggested_new_date"],
        "confidence": excuse_data["confidence"],
    }


@router.post("/{task_id}/decide")
async def decide_procrastination(task_id: str, decision: ProcrastinateDecision):
    db = get_db()
    task = await get_doc_or_404(db, "tasks", task_id)

    if decision.accept_postponement:
        update = {
            "status": "procrastinated",
            "procrastination_count": task.get("procrastination_count", 0) + 1,
        }
        if decision.new_date:
            update["postponed_to"] = decision.new_date
        count = update["procrastination_count"]
        message = f"Excelente decisão! Sua tarefa foi adiada {count}x. O gato aprova... por enquanto."
    else:
        update = {"status": "pending"}
        message = "Corajoso. O gato está impressionado e ligeiramente decepcionado."

    await db.tasks.update_one({"_id": task["_id"]}, {"$set": update})
    await recalculate_cat(db)
    task = await db.tasks.find_one({"_id": task["_id"]})
    return {"task": serialize_doc(task, TASK_DATE_FIELDS), "message": message}


@router.patch("/{task_id}/complete")
async def complete_task(task_id: str):
    db = get_db()
    task = await get_doc_or_404(db, "tasks", task_id)

    await db.tasks.update_one(
        {"_id": task["_id"]},
        {"$set": {"status": "done", "completed_at": datetime.utcnow()}},
    )
    await recalculate_cat(db)
    task = await db.tasks.find_one({"_id": task["_id"]})
    return {"task": serialize_doc(task, TASK_DATE_FIELDS), "message": "Tarefa concluída! O gato ficou 15% mais feliz."}


@router.delete("/{task_id}")
async def delete_task(task_id: str):
    db = get_db()
    task = await get_doc_or_404(db, "tasks", task_id)

    await db.tasks.delete_one({"_id": task["_id"]})
    await recalculate_cat(db)
    return {"message": "Tarefa deletada. Uma forma válida de concluir."}
