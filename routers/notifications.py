from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from database import get_db
from services.notification_service import (
    generate_useless_notification,
    get_unread_notifications,
    mark_all_read,
)
import asyncio
import json

router = APIRouter(prefix="/notifications", tags=["notifications"])

_MAX_SSE_EVENTS = 100


@router.get("/")
async def list_notifications():
    db = get_db()
    return await get_unread_notifications(db)


@router.post("/generate")
async def trigger_notification():
    db = get_db()
    notif = await generate_useless_notification(db)
    return {"id": notif["_id"], "message": notif["message"], "category": notif["category"]}


@router.post("/mark-read")
async def mark_read():
    db = get_db()
    await mark_all_read(db)
    return {"message": "Todas as notificações marcadas como lidas. A Terra ainda é redonda."}


@router.get("/stream")
async def stream_notifications(request: Request):
    async def event_generator():
        db = get_db()
        count = 0
        while count < _MAX_SSE_EVENTS:
            if await request.is_disconnected():
                break
            notif = await generate_useless_notification(db)
            data = json.dumps({"message": notif["message"], "category": notif["category"]})
            yield f"data: {data}\n\n"
            count += 1
            await asyncio.sleep(30)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
