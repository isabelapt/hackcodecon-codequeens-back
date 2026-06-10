from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

from services.cat_service import (
    recalculate_cat_sync,
    recalculate_cat,
    feed_cat,
    MOOD_DESCRIPTIONS,
    DESTRUCTION_MESSAGES,
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_sync_db(total=0, done=0, desistiu=0, tasks=None, cat=None):
    """Build a mock PyMongo database with flask_tasks and cat_state."""
    if tasks is None:
        tasks = [{"vezes_adiada": 0}] * total

    col = MagicMock()
    col.count_documents.side_effect = lambda q: (
        total if q == {} else done if q == {"concluida": True} else desistiu
    )
    col.find.return_value = iter(tasks)
    col.database = MagicMock()
    col.database.flask_tasks = col

    cat_doc = cat or {
        "_id": "main",
        "mood": "neutral",
        "happiness": 70.0,
        "hunger": 30.0,
        "destruction_level": 0,
    }
    col.database.cat_state = MagicMock()
    col.database.cat_state.find_one.return_value = cat_doc
    col.database.cat_state.update_one.return_value = None

    col.database.notifications = MagicMock()
    col.database.notifications.insert_one.return_value = None

    return col.database


def _make_async_db(total=0, done=0, desistiu=0, tasks=None, cat=None):
    """Build a mock Motor (async) database."""
    if tasks is None:
        tasks = [{"vezes_adiada": 0}] * total

    db = MagicMock()
    db.flask_tasks = MagicMock()
    db.flask_tasks.count_documents = AsyncMock(
        side_effect=lambda q: (
            total if q == {} else done if q == {"concluida": True} else desistiu
        )
    )

    async def _async_iter_tasks(*a, **kw):
        for t in tasks:
            yield t

    db.flask_tasks.find.return_value = _async_iter_tasks()

    cat_doc = cat or {
        "_id": "main",
        "mood": "neutral",
        "happiness": 70.0,
        "hunger": 30.0,
        "destruction_level": 0,
        "last_fed_at": datetime(2025, 1, 1),
    }
    db.cat_state = MagicMock()
    db.cat_state.find_one = AsyncMock(return_value=cat_doc)
    db.cat_state.update_one = AsyncMock()

    db.notifications = MagicMock()
    db.notifications.insert_one = AsyncMock()

    return db


# ── recalculate_cat_sync ─────────────────────────────────────────────────────

class TestRecalculateCatSync:
    def test_no_tasks_gives_neutral_mood(self):
        db = _make_sync_db(total=0)
        recalculate_cat_sync(db)
        call_args = db.cat_state.update_one.call_args
        update = call_args[0][1]["$set"]
        assert update["mood"] == "neutral"
        assert update["happiness"] == 70.0

    def test_all_done_gives_happy(self):
        db = _make_sync_db(total=4, done=4)
        recalculate_cat_sync(db)
        update = db.cat_state.update_one.call_args[0][1]["$set"]
        assert update["mood"] == "happy"
        assert update["happiness"] == 100.0  # min(100, 4/4*120)

    def test_no_done_gives_monster(self):
        db = _make_sync_db(total=4, done=0)
        recalculate_cat_sync(db)
        update = db.cat_state.update_one.call_args[0][1]["$set"]
        assert update["mood"] == "monster"
        assert update["happiness"] == 0.0

    def test_half_done_gives_neutral(self):
        db = _make_sync_db(total=4, done=2)
        recalculate_cat_sync(db)
        update = db.cat_state.update_one.call_args[0][1]["$set"]
        # happiness = min(100, 2/4 * 120) = 60 → neutral (50 <= h < 75)
        assert update["mood"] == "neutral"

    def test_hunger_increases_with_desistiu(self):
        db = _make_sync_db(total=4, done=2, desistiu=2)
        recalculate_cat_sync(db)
        update = db.cat_state.update_one.call_args[0][1]["$set"]
        assert update["hunger"] == 50.0  # (2 + 0*0.3)/4 * 100

    def test_hunger_includes_adiadas(self):
        tasks = [{"vezes_adiada": 5}]
        db = _make_sync_db(total=1, done=0, desistiu=0, tasks=tasks)
        recalculate_cat_sync(db)
        update = db.cat_state.update_one.call_args[0][1]["$set"]
        # hunger = min(100, (0 + 5*0.3)/1 * 100) = min(100, 150) = 100
        assert update["hunger"] == 100.0

    @patch("services.cat_service.random")
    def test_monster_triggers_destruction_notification(self, mock_random):
        mock_random.random.return_value = 0.1  # < 0.3 → triggers
        mock_random.choice.return_value = DESTRUCTION_MESSAGES[0]

        cat = {"_id": "main", "destruction_level": 2}
        db = _make_sync_db(total=4, done=0, cat=cat)
        recalculate_cat_sync(db)

        update = db.cat_state.update_one.call_args[0][1]["$set"]
        assert update["destruction_level"] == 3
        db.notifications.insert_one.assert_called_once()

    @patch("services.cat_service.random")
    def test_monster_no_destruction_when_random_high(self, mock_random):
        mock_random.random.return_value = 0.9  # >= 0.3 → no destruction
        db = _make_sync_db(total=4, done=0)
        recalculate_cat_sync(db)
        db.notifications.insert_one.assert_not_called()

    @patch("services.cat_service.random")
    def test_destruction_capped_at_5(self, mock_random):
        mock_random.random.return_value = 0.1
        mock_random.choice.return_value = DESTRUCTION_MESSAGES[0]
        cat = {"_id": "main", "destruction_level": 5}
        db = _make_sync_db(total=4, done=0, cat=cat)
        recalculate_cat_sync(db)
        update = db.cat_state.update_one.call_args[0][1]["$set"]
        assert update["destruction_level"] == 5


# ── recalculate_cat (async) ──────────────────────────────────────────────────

class TestRecalculateCatAsync:
    @pytest.mark.asyncio
    async def test_no_tasks_neutral(self):
        db = _make_async_db(total=0)
        result = await recalculate_cat(db)
        db.cat_state.update_one.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_all_done_happy(self):
        db = _make_async_db(total=4, done=4)
        await recalculate_cat(db)
        update = db.cat_state.update_one.await_args[0][1]["$set"]
        assert update["mood"] == "happy"

    @pytest.mark.asyncio
    async def test_none_done_monster(self):
        db = _make_async_db(total=4, done=0)
        await recalculate_cat(db)
        update = db.cat_state.update_one.await_args[0][1]["$set"]
        assert update["mood"] == "monster"


# ── feed_cat ─────────────────────────────────────────────────────────────────

class TestFeedCat:
    @pytest.mark.asyncio
    async def test_increases_happiness_and_decreases_hunger(self):
        cat_doc = {
            "_id": "main",
            "mood": "neutral",
            "happiness": 50.0,
            "hunger": 60.0,
            "destruction_level": 0,
            "last_fed_at": datetime(2025, 1, 1),
        }
        db = _make_async_db(total=0, cat=cat_doc)
        await feed_cat(db)
        update_call = db.cat_state.update_one.await_args_list[0]
        update_set = update_call[0][1]["$set"]
        assert update_set["happiness"] == 65.0  # 50 + 15
        assert update_set["hunger"] == 40.0     # 60 - 20

    @pytest.mark.asyncio
    async def test_happiness_capped_at_100(self):
        cat_doc = {
            "_id": "main",
            "happiness": 95.0,
            "hunger": 10.0,
            "destruction_level": 0,
            "last_fed_at": datetime(2025, 1, 1),
        }
        db = _make_async_db(total=0, cat=cat_doc)
        await feed_cat(db)
        update_set = db.cat_state.update_one.await_args_list[0][0][1]["$set"]
        assert update_set["happiness"] == 100.0

    @pytest.mark.asyncio
    async def test_hunger_floored_at_0(self):
        cat_doc = {
            "_id": "main",
            "happiness": 50.0,
            "hunger": 5.0,
            "destruction_level": 0,
            "last_fed_at": datetime(2025, 1, 1),
        }
        db = _make_async_db(total=0, cat=cat_doc)
        await feed_cat(db)
        update_set = db.cat_state.update_one.await_args_list[0][0][1]["$set"]
        assert update_set["hunger"] == 0.0
