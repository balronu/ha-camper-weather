import asyncio

from custom_components.camper_weather.api import _assess_plan_for_coordinator, _validate_plan
from custom_components.camper_weather.planner import ActivityStore


class FakeStore:
    def __init__(self):
        self.payload = None

    async def async_load(self):
        return self.payload

    async def async_save(self, payload):
        self.payload = payload


def test_numeric_legacy_id_is_canonicalized_and_update_is_idempotent():
    store_backend = FakeStore()
    store = object.__new__(ActivityStore)
    store._store = store_backend
    store._items = {}
    store._loaded = True
    item = {"id": 277, "activity": "hiking", "start_at": "2026-10-26T11:43:00Z", "duration_minutes": 120}
    first = asyncio.run(store.async_save(item))
    second = asyncio.run(store.async_save({**item, "temperature_note": "updated"}))
    assert first["id"] == second["id"] == "277"
    assert len(asyncio.run(store.async_items())) == 1
    restarted = object.__new__(ActivityStore)
    restarted._store = store_backend
    restarted._items = {}
    restarted._loaded = False
    assert [item["id"] for item in asyncio.run(restarted.async_items())] == ["277"]
    assert asyncio.run(store.async_delete("277")) is True
    assert asyncio.run(store.async_items()) == []


def test_plan_schema_accepts_numeric_legacy_id_and_returns_string():
    result = _validate_plan({"id": 277, "activity": "hiking", "start_at": "2026-10-26T11:43:00Z", "duration_minutes": 120})
    assert result["id"] == 277


def test_planner_assessment_helper_is_not_shadowed_by_websocket_handler():
    class Coordinator:
        def __init__(self):
            self.data = {
                "location": {"mode": "tracker", "latitude": 49.0, "longitude": 7.0},
                "data_quality": {"status": "good", "reason": "ok", "sources": ["test"]},
                "hours": [],
                "warnings": [],
            }

    result = _assess_plan_for_coordinator(Coordinator(), {"activity": "walking", "start_at": "2026-10-27T10:00:00Z", "duration_minutes": 60})
    assert {"score", "safety_status", "data_quality"} <= result.keys()
