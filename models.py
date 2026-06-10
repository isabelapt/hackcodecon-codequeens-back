from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime


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
