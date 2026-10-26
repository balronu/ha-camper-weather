import asyncio

from custom_components.camper_weather.location import LocationStore


class FakeStore:
    def __init__(self, payload=None):
        self.payload = payload

    async def async_load(self):
        return self.payload

    async def async_save(self, payload):
        self.payload = payload


def make_store(backend):
    store = object.__new__(LocationStore)
    store._store = backend
    store.current = {"mode": "tracker"}
    store.destinations = {}
    store._loaded = False
    return store


def test_location_store_persists_override_without_gps_history():
    backend = FakeStore()
    store = make_store(backend)
    asyncio.run(store.async_set_current({"mode": "destination", "name": "Bergen", "latitude": 60.39, "longitude": 5.32}))
    saved = asyncio.run(store.async_save_destination({"name": "Bergen", "latitude": 60.39, "longitude": 5.32}))
    restarted = make_store(backend)
    payload = asyncio.run(restarted.async_payload())
    assert payload["current"]["mode"] == "destination"
    assert payload["destinations"][0]["id"] == saved["id"]
    assert "history" not in backend.payload


def test_location_store_deletes_only_selected_destination():
    backend = FakeStore()
    store = make_store(backend)
    first = asyncio.run(store.async_save_destination({"name": "A", "latitude": 1, "longitude": 2}))
    second = asyncio.run(store.async_save_destination({"name": "B", "latitude": 3, "longitude": 4}))
    assert asyncio.run(store.async_delete_destination(first["id"])) is True
    assert [item["id"] for item in asyncio.run(store.async_payload())["destinations"]] == [second["id"]]
