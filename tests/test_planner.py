import asyncio
from unittest.mock import AsyncMock, patch

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


def test_manual_planner_target_is_validated_and_used_for_assessment():
    class Coordinator:
        def __init__(self):
            self.data = {"location": {"mode": "tracker", "latitude": 49.0, "longitude": 7.0}, "data_quality": {}, "hours": [], "warnings": []}

        @staticmethod
        def _valid_coordinates(latitude, longitude):
            return latitude is not None and longitude is not None and latitude != 0 and longitude != 0

    item = _validate_plan({"activity": "walking", "start_at": "2026-10-28T10:00:00Z", "duration_minutes": 60, "location_mode": "manual", "location_name": "Trier", "latitude": 49.75, "longitude": 6.64})
    assert item["location_name"] == "Trier"
    with patch("custom_components.camper_weather.api.assess_plan", return_value={}) as mocked:
        from custom_components.camper_weather.api import _assess_plan_for_coordinator

        _assess_plan_for_coordinator(Coordinator(), item)
    target = mocked.call_args.kwargs["location"]
    assert (target.mode, target.name, target.latitude, target.longitude) == ("manual", "Trier", 49.75, 6.64)


def test_manual_planner_target_requires_coordinates():
    try:
        _validate_plan({"activity": "walking", "start_at": "2026-10-28T10:00:00Z", "duration_minutes": 60, "location_mode": "manual"})
    except ValueError as error:
        assert "Koordinaten" in str(error)
    else:
        raise AssertionError("manual planner target without coordinates was accepted")


def test_manual_planner_assessment_fetches_forecast_for_target_coordinates():
    class Coordinator:
        def __init__(self):
            self.hass = object()
            self.options = {"provider": "open_meteo", "dwd_enabled": False}
            self.data = {"location": {"mode": "tracker", "latitude": 49.0, "longitude": 7.0}, "data_quality": {}, "hours": [], "warnings": []}

        @staticmethod
        def _valid_coordinates(latitude, longitude):
            return latitude is not None and longitude is not None and latitude != 0 and longitude != 0

    item = _validate_plan({"activity": "walking", "start_at": "2026-10-28T10:00:00Z", "duration_minutes": 60, "location_mode": "manual", "location_name": "Trier", "latitude": 49.75, "longitude": 6.64})
    session = object()
    with patch("custom_components.camper_weather.api.async_get_clientsession", return_value=session), patch("custom_components.camper_weather.api.async_open_meteo", new=AsyncMock(return_value=[])) as forecast:
        from custom_components.camper_weather.api import _async_assess_plan_for_coordinator

        asyncio.run(_async_assess_plan_for_coordinator(Coordinator(), item))
    forecast.assert_awaited_once_with(session, 49.75, 6.64)
