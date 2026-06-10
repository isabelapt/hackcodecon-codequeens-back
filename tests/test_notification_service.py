from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

from services.notification_service import (
    generate_useless_notification,
    get_unread_notifications,
    mark_all_read,
    USELESS_FACTS,
)


def _make_db():
    db = MagicMock()
    db.notifications = MagicMock()
    db.notifications.insert_one = AsyncMock()
    db.notifications.update_many = AsyncMock()
    return db


# ── generate_useless_notification ────────────────────────────────────────────

class TestGenerateUselessNotification:
    @pytest.mark.asyncio
    async def test_inserts_document(self):
        db = _make_db()
        mock_result = MagicMock()
        mock_result.inserted_id = "abc123"
        db.notifications.insert_one.return_value = mock_result

        doc = await generate_useless_notification(db)

        db.notifications.insert_one.assert_awaited_once()
        assert doc["_id"] == "abc123"
        assert doc["category"] == "useless_fact"
        assert doc["is_read"] is False

    @pytest.mark.asyncio
    async def test_message_is_from_facts(self):
        db = _make_db()
        mock_result = MagicMock()
        mock_result.inserted_id = "id1"
        db.notifications.insert_one.return_value = mock_result

        doc = await generate_useless_notification(db)
        assert doc["message"] in USELESS_FACTS


# ── get_unread_notifications ─────────────────────────────────────────────────

class TestGetUnreadNotifications:
    @pytest.mark.asyncio
    async def test_returns_serialized_list(self):
        db = _make_db()

        from bson import ObjectId

        raw_docs = [
            {
                "_id": ObjectId(),
                "message": "test",
                "is_read": False,
                "created_at": datetime(2025, 6, 1),
            },
        ]

        async def _cursor_iter(*a, **kw):
            for d in raw_docs:
                yield d

        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = _cursor_iter()
        db.notifications.find.return_value = mock_cursor

        result = await get_unread_notifications(db)

        assert len(result) == 1
        assert "id" in result[0]
        assert "_id" not in result[0]
        assert result[0]["created_at"] == "2025-06-01T00:00:00"

    @pytest.mark.asyncio
    async def test_empty_when_no_notifications(self):
        db = _make_db()

        async def _empty(*a, **kw):
            return
            yield  # make it an async generator

        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = _empty()
        db.notifications.find.return_value = mock_cursor

        result = await get_unread_notifications(db)
        assert result == []


# ── mark_all_read ────────────────────────────────────────────────────────────

class TestMarkAllRead:
    @pytest.mark.asyncio
    async def test_calls_update_many(self):
        db = _make_db()
        await mark_all_read(db)
        db.notifications.update_many.assert_awaited_once_with(
            {"is_read": False}, {"$set": {"is_read": True}}
        )
