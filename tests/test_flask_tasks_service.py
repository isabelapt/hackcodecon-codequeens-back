from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, AsyncMock

import pytest
from bson import ObjectId

from services.flask_tasks_service import (
    serialize,
    get_all,
    get_one,
    create,
    put,
    patch as svc_patch,
    delete,
    build_excuse,
)


# ── serialize ────────────────────────────────────────────────────────────────

class TestSerialize:
    def test_converts_id(self):
        oid = ObjectId()
        result = serialize({"_id": oid, "nome": "x"})
        assert result["id"] == str(oid)
        assert "_id" not in result


# ── get_all ──────────────────────────────────────────────────────────────────

class TestGetAll:
    def test_returns_serialized_list(self):
        col = MagicMock()
        col.find.return_value = [
            {"_id": ObjectId(), "nome": "a"},
            {"_id": ObjectId(), "nome": "b"},
        ]
        result = get_all(col)
        assert len(result) == 2
        assert all("id" in r for r in result)

    def test_empty_collection(self):
        col = MagicMock()
        col.find.return_value = []
        assert get_all(col) == []


# ── get_one ──────────────────────────────────────────────────────────────────

class TestGetOne:
    def test_returns_task(self):
        oid = ObjectId()
        col = MagicMock()
        col.find_one.return_value = {"_id": oid, "nome": "task1"}
        result = get_one(col, str(oid))
        assert result["id"] == str(oid)


# ── create ───────────────────────────────────────────────────────────────────

class TestCreate:
    @patch("services.flask_tasks_service.recalculate_cat_sync")
    def test_inserts_and_returns_task(self, mock_recat):
        col = MagicMock()
        oid = ObjectId()
        mock_result = MagicMock()
        mock_result.inserted_id = oid
        col.insert_one.return_value = mock_result
        col.database = MagicMock()

        body = {"nome": "Test task", "data_termino": "2025-07-01"}
        result = create(col, body)

        col.insert_one.assert_called_once()
        assert result["id"] == str(oid)
        assert result["concluida"] is False
        assert result["vezes_adiada"] == 0
        assert result["desistiu"] is False
        mock_recat.assert_called_once_with(col.database)

    @patch("services.flask_tasks_service.recalculate_cat_sync")
    def test_create_without_data_termino(self, mock_recat):
        col = MagicMock()
        oid = ObjectId()
        mock_result = MagicMock()
        mock_result.inserted_id = oid
        col.insert_one.return_value = mock_result
        col.database = MagicMock()

        result = create(col, {"nome": "No deadline"})
        inserted = col.insert_one.call_args[0][0]
        assert inserted["data_termino"] is None


# ── put ──────────────────────────────────────────────────────────────────────

class TestPut:
    @patch("services.flask_tasks_service.recalculate_cat_sync")
    def test_replaces_task(self, mock_recat):
        oid = ObjectId()
        col = MagicMock()
        col.find_one_and_replace.return_value = {"_id": oid, "nome": "updated"}
        col.database = MagicMock()

        result = put(col, str(oid), {"nome": "updated", "concluida": True})
        assert result["id"] == str(oid)
        mock_recat.assert_called_once()

    @patch("services.flask_tasks_service.recalculate_cat_sync")
    def test_returns_none_when_not_found(self, mock_recat):
        col = MagicMock()
        col.find_one_and_replace.return_value = None
        result = put(col, str(ObjectId()), {"nome": "x"})
        assert result is None
        mock_recat.assert_not_called()


# ── patch ────────────────────────────────────────────────────────────────────

class TestPatch:
    @patch("services.flask_tasks_service.recalculate_cat_sync")
    def test_updates_task(self, mock_recat):
        oid = ObjectId()
        col = MagicMock()
        col.find_one_and_update.return_value = {"_id": oid, "nome": "patched"}
        col.database = MagicMock()

        result = svc_patch(col, str(oid), {"nome": "patched"})
        assert result["id"] == str(oid)
        mock_recat.assert_called_once()

    @patch("services.flask_tasks_service.recalculate_cat_sync")
    def test_returns_none_when_not_found(self, mock_recat):
        col = MagicMock()
        col.find_one_and_update.return_value = None
        result = svc_patch(col, str(ObjectId()), {"nome": "x"})
        assert result is None
        mock_recat.assert_not_called()


# ── delete ───────────────────────────────────────────────────────────────────

class TestDelete:
    @patch("services.flask_tasks_service.recalculate_cat_sync")
    def test_deletes_and_returns_task(self, mock_recat):
        oid = ObjectId()
        col = MagicMock()
        col.find_one_and_delete.return_value = {"_id": oid, "nome": "gone"}
        col.database = MagicMock()

        result = delete(col, str(oid))
        assert result["id"] == str(oid)
        mock_recat.assert_called_once()

    @patch("services.flask_tasks_service.recalculate_cat_sync")
    def test_returns_none_when_not_found(self, mock_recat):
        col = MagicMock()
        col.find_one_and_delete.return_value = None
        result = delete(col, str(ObjectId()))
        assert result is None
        mock_recat.assert_not_called()


# ── build_excuse ─────────────────────────────────────────────────────────────

class TestBuildExcuse:
    @pytest.mark.asyncio
    @patch("services.flask_tasks_service.get_procrastination_excuse", new_callable=AsyncMock)
    async def test_parses_iso_string_date(self, mock_excuse):
        mock_excuse.return_value = {"excuse": "ok"}
        await build_excuse("task", "2025-07-01T10:00:00")
        call_dt = mock_excuse.call_args[0][1]
        assert isinstance(call_dt, datetime)

    @pytest.mark.asyncio
    @patch("services.flask_tasks_service.get_procrastination_excuse", new_callable=AsyncMock)
    async def test_handles_invalid_date_string(self, mock_excuse):
        mock_excuse.return_value = {"excuse": "ok"}
        await build_excuse("task", "not-a-date")
        call_dt = mock_excuse.call_args[0][1]
        assert call_dt is None

    @pytest.mark.asyncio
    @patch("services.flask_tasks_service.get_procrastination_excuse", new_callable=AsyncMock)
    async def test_passes_none_when_no_date(self, mock_excuse):
        mock_excuse.return_value = {"excuse": "ok"}
        await build_excuse("task")
        call_dt = mock_excuse.call_args[0][1]
        assert call_dt is None
