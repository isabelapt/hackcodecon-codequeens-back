"""Shared utilities to eliminate duplicated patterns across the codebase."""

from datetime import datetime
from typing import Optional

from bson import ObjectId
from fastapi import HTTPException


def serialize_doc(doc: dict, datetime_fields: Optional[list[str]] = None) -> dict:
    """Convert a MongoDB document for JSON serialization.

    - Renames ``_id`` to ``id`` (stringified).
    - Converts any datetime values found in *datetime_fields* to ISO strings.
      If *datetime_fields* is ``None``, **all** datetime values are converted.
    """
    if doc is None:
        return None
    doc = dict(doc)
    if "_id" in doc:
        doc["id"] = str(doc.pop("_id"))
    for key, value in doc.items():
        if not isinstance(value, datetime):
            continue
        if datetime_fields is None or key in datetime_fields:
            doc[key] = value.isoformat()
    return doc


def validate_object_id(value: str) -> ObjectId:
    """Parse *value* as a BSON ObjectId or raise an HTTP 400."""
    try:
        return ObjectId(value)
    except Exception:
        raise HTTPException(status_code=400, detail="ID inválido")


async def get_doc_or_404(db, collection: str, doc_id: str) -> dict:
    """Validate *doc_id*, fetch the document, or raise 404."""
    oid = validate_object_id(doc_id)
    doc = await db[collection].find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    return doc


def build_notification_doc(message: str, category: str) -> dict:
    """Build a notification document ready for insertion."""
    return {
        "message": message,
        "category": category,
        "is_read": False,
        "created_at": datetime.utcnow(),
    }
