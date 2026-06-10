"""Tests for the FastAPI routers (tasks, cat, notifications) and the health endpoint."""
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from bson import ObjectId


# We need to stub database and external deps before importing `main`.

@pytest.fixture(autouse=True)
def _stub_env(monkeypatch):
    monkeypatch.setenv("MONGODB_URL", "mongodb://localhost:27017")
    monkeypatch.setenv("MONGODB_DB", "testdb")
    monkeypatch.setenv("GEMINI_API_KEY", "fake")


@pytest.fixture()
def app():
    """Create a fresh FastAPI app with lifespan events patched out."""
    # Patch connect_db / close_db so no real Mongo connection is attempted.
    with (
        patch("main.connect_db", new_callable=AsyncMock),
        patch("main.close_db", new_callable=AsyncMock),
        patch("main.scheduler") as mock_sched,
    ):
        mock_sched.add_job = MagicMock()
        mock_sched.start = MagicMock()
        mock_sched.shutdown = MagicMock()

        # Re-import to get a fresh app with patched lifespan.
        import importlib
        import main as main_mod
        importlib.reload(main_mod)
        yield main_mod.app


@pytest.fixture()
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ── Health ───────────────────────────────────────────────────────────────────

class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health_returns_alive(self, client):
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "alive"


# ── Cat router ───────────────────────────────────────────────────────────────

class TestCatRouter:
    @pytest.mark.asyncio
    @patch("routers.cat.get_db")
    @patch("routers.cat.recalculate_cat", new_callable=AsyncMock)
    async def test_get_cat(self, mock_recat, mock_get_db, client):
        mock_recat.return_value = {
            "mood": "happy",
            "happiness": 90.0,
            "hunger": 10.0,
            "destruction_level": 0,
            "last_fed_at": datetime(2025, 6, 1),
        }
        resp = await client.get("/api/cat/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["mood"] == "happy"
        assert data["happiness"] == 90.0
        assert data["description"] != ""

    @pytest.mark.asyncio
    @patch("routers.cat.get_db")
    @patch("routers.cat.feed_cat", new_callable=AsyncMock)
    async def test_feed_cat(self, mock_feed, mock_get_db, client):
        mock_feed.return_value = {
            "mood": "happy",
            "happiness": 85.0,
            "hunger": 20.0,
        }
        resp = await client.post("/api/cat/feed")
        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data


# ── Notifications router ────────────────────────────────────────────────────

class TestNotificationsRouter:
    @pytest.mark.asyncio
    @patch("routers.notifications.get_db")
    @patch("routers.notifications.get_unread_notifications", new_callable=AsyncMock)
    async def test_list_notifications(self, mock_unread, mock_get_db, client):
        mock_unread.return_value = [{"id": "1", "message": "hi"}]
        resp = await client.get("/api/notifications/")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    @pytest.mark.asyncio
    @patch("routers.notifications.get_db")
    @patch("routers.notifications.generate_useless_notification", new_callable=AsyncMock)
    async def test_generate_notification(self, mock_gen, mock_get_db, client):
        mock_gen.return_value = {
            "_id": "abc",
            "message": "Testing",
            "category": "useless_fact",
        }
        resp = await client.post("/api/notifications/generate")
        assert resp.status_code == 200
        assert resp.json()["id"] == "abc"

    @pytest.mark.asyncio
    @patch("routers.notifications.get_db")
    @patch("routers.notifications.mark_all_read", new_callable=AsyncMock)
    async def test_mark_read(self, mock_mark, mock_get_db, client):
        resp = await client.post("/api/notifications/mark-read")
        assert resp.status_code == 200
        mock_mark.assert_awaited_once()


# ── Tasks router ─────────────────────────────────────────────────────────────

def _task_doc(oid=None, **overrides):
    doc = {
        "_id": oid or ObjectId(),
        "title": "Test",
        "description": "",
        "scheduled_at": datetime(2025, 7, 1),
        "postponed_to": None,
        "status": "pending",
        "excuse": None,
        "procrastination_count": 0,
        "created_at": datetime(2025, 6, 1),
        "completed_at": None,
    }
    doc.update(overrides)
    return doc


class TestTasksRouter:
    @pytest.mark.asyncio
    @patch("routers.tasks.get_db")
    async def test_get_stats_empty(self, mock_get_db, client):
        db = MagicMock()
        db.tasks = MagicMock()
        db.tasks.update_many = AsyncMock()
        db.tasks.count_documents = AsyncMock(return_value=0)
        mock_get_db.return_value = db

        resp = await client.get("/api/tasks/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["procrastination_rate"] == 0

    @pytest.mark.asyncio
    @patch("routers.tasks.get_db")
    async def test_list_tasks(self, mock_get_db, client):
        db = MagicMock()
        db.tasks = MagicMock()
        db.tasks.update_many = AsyncMock()

        async def _iter():
            yield _task_doc()

        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = _iter()
        db.tasks.find.return_value = mock_cursor
        mock_get_db.return_value = db

        resp = await client.get("/api/tasks/")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    @pytest.mark.asyncio
    @patch("routers.tasks.recalculate_cat", new_callable=AsyncMock)
    @patch("routers.tasks.get_db")
    async def test_complete_task(self, mock_get_db, mock_recat, client):
        oid = ObjectId()
        db = MagicMock()
        db.tasks = MagicMock()
        db.tasks.find_one = AsyncMock(return_value=_task_doc(oid=oid))
        db.tasks.update_one = AsyncMock()
        mock_get_db.return_value = db

        resp = await client.patch(f"/api/tasks/{oid}/complete")
        assert resp.status_code == 200
        assert "message" in resp.json()

    @pytest.mark.asyncio
    @patch("routers.tasks.recalculate_cat", new_callable=AsyncMock)
    @patch("routers.tasks.get_db")
    async def test_complete_invalid_id(self, mock_get_db, mock_recat, client):
        resp = await client.patch("/api/tasks/invalid-id/complete")
        assert resp.status_code == 400

    @pytest.mark.asyncio
    @patch("routers.tasks.recalculate_cat", new_callable=AsyncMock)
    @patch("routers.tasks.get_db")
    async def test_complete_not_found(self, mock_get_db, mock_recat, client):
        oid = ObjectId()
        db = MagicMock()
        db.tasks = MagicMock()
        db.tasks.find_one = AsyncMock(return_value=None)
        mock_get_db.return_value = db

        resp = await client.patch(f"/api/tasks/{oid}/complete")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    @patch("routers.tasks.recalculate_cat", new_callable=AsyncMock)
    @patch("routers.tasks.get_db")
    async def test_delete_task(self, mock_get_db, mock_recat, client):
        oid = ObjectId()
        db = MagicMock()
        db.tasks = MagicMock()
        mock_del = MagicMock()
        mock_del.deleted_count = 1
        db.tasks.delete_one = AsyncMock(return_value=mock_del)
        mock_get_db.return_value = db

        resp = await client.delete(f"/api/tasks/{oid}")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    @patch("routers.tasks.recalculate_cat", new_callable=AsyncMock)
    @patch("routers.tasks.get_db")
    async def test_delete_not_found(self, mock_get_db, mock_recat, client):
        oid = ObjectId()
        db = MagicMock()
        db.tasks = MagicMock()
        mock_del = MagicMock()
        mock_del.deleted_count = 0
        db.tasks.delete_one = AsyncMock(return_value=mock_del)
        mock_get_db.return_value = db

        resp = await client.delete(f"/api/tasks/{oid}")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    @patch("routers.tasks.recalculate_cat", new_callable=AsyncMock)
    @patch("routers.tasks.get_db")
    async def test_decide_accept(self, mock_get_db, mock_recat, client):
        oid = ObjectId()
        db = MagicMock()
        db.tasks = MagicMock()
        db.tasks.find_one = AsyncMock(return_value=_task_doc(oid=oid))
        db.tasks.update_one = AsyncMock()
        mock_get_db.return_value = db

        resp = await client.post(
            f"/api/tasks/{oid}/decide",
            json={"accept_postponement": True},
        )
        assert resp.status_code == 200
        assert "adiada" in resp.json()["message"].lower() or "adiada" in resp.json()["message"]

    @pytest.mark.asyncio
    @patch("routers.tasks.recalculate_cat", new_callable=AsyncMock)
    @patch("routers.tasks.get_db")
    async def test_decide_reject(self, mock_get_db, mock_recat, client):
        oid = ObjectId()
        db = MagicMock()
        db.tasks = MagicMock()
        db.tasks.find_one = AsyncMock(return_value=_task_doc(oid=oid))
        db.tasks.update_one = AsyncMock()
        mock_get_db.return_value = db

        resp = await client.post(
            f"/api/tasks/{oid}/decide",
            json={"accept_postponement": False},
        )
        assert resp.status_code == 200
        assert "Corajoso" in resp.json()["message"]
