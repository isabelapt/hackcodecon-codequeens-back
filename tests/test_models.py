from datetime import datetime

from bson import ObjectId

from models import serialize_doc, TaskCreate, ProcrastinateDecision


# ── serialize_doc ────────────────────────────────────────────────────────────

class TestSerializeDoc:
    def test_returns_none_for_none(self):
        assert serialize_doc(None) is None

    def test_converts_objectid_to_str_id(self):
        oid = ObjectId()
        result = serialize_doc({"_id": oid, "title": "test"})
        assert result["id"] == str(oid)
        assert "_id" not in result

    def test_converts_datetime_fields_to_isoformat(self):
        now = datetime(2025, 1, 15, 12, 0, 0)
        result = serialize_doc({"_id": ObjectId(), "created_at": now})
        assert result["created_at"] == "2025-01-15T12:00:00"

    def test_leaves_non_datetime_values_unchanged(self):
        result = serialize_doc({"_id": ObjectId(), "count": 42, "name": "x"})
        assert result["count"] == 42
        assert result["name"] == "x"

    def test_empty_doc_only_converts_id(self):
        oid = ObjectId()
        result = serialize_doc({"_id": oid})
        assert result == {"id": str(oid)}

    def test_does_not_mutate_original(self):
        oid = ObjectId()
        original = {"_id": oid, "val": 1}
        serialize_doc(original)
        assert "_id" in original  # original should still have _id


# ── Pydantic models ─────────────────────────────────────────────────────────

class TestTaskCreate:
    def test_defaults(self):
        t = TaskCreate(title="Buy milk", scheduled_at=datetime(2025, 6, 1))
        assert t.description == ""

    def test_with_description(self):
        t = TaskCreate(
            title="Deploy",
            description="Push v2",
            scheduled_at=datetime(2025, 6, 1),
        )
        assert t.description == "Push v2"


class TestProcrastinateDecision:
    def test_accept_without_new_date(self):
        d = ProcrastinateDecision(accept_postponement=True)
        assert d.new_date is None

    def test_accept_with_new_date(self):
        dt = datetime(2025, 7, 1)
        d = ProcrastinateDecision(accept_postponement=True, new_date=dt)
        assert d.new_date == dt
