from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


# ── Helpers ──────────────────────────────────────────────────────────────────

def serialize_doc(doc: dict) -> dict:
    """Converte _id do MongoDB e datetimes para serialização JSON."""
    if doc is None:
        return None
    doc = dict(doc)
    if "_id" in doc:
        doc["id"] = str(doc.pop("_id"))
    for k, v in doc.items():
        if isinstance(v, datetime):
            doc[k] = v.isoformat()
    return doc


# ── Task ─────────────────────────────────────────────────────────────────────

TaskStatus = Literal["pending", "procrastinated", "done", "overdue"]


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    scheduled_at: datetime


class ProcrastinateDecision(BaseModel):
    accept_postponement: bool
    new_date: Optional[datetime] = None


# ── Cat ──────────────────────────────────────────────────────────────────────

CatMood = Literal["happy", "neutral", "grumpy", "monster"]
