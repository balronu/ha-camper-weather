"""Persistent daily location selection for the Lovelace card.

This stores the selected source and explicitly saved destinations only. It
does not record a GPS history.
"""
from __future__ import annotations

from typing import Any
from uuid import uuid4

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store


class LocationStore:
    """Store one active override and a small user-managed destination list."""

    def __init__(self, hass: HomeAssistant, entry_id: str, default_mode: str = "config") -> None:
        self._store = Store[dict[str, Any]](hass, 1, f"camper_weather.location.{entry_id}")
        self.current: dict[str, Any] = {"mode": default_mode}
        self.destinations: dict[str, dict[str, Any]] = {}
        self.revision = 0
        self._loaded = False

    async def async_load(self) -> None:
        if self._loaded:
            return
        payload = await self._store.async_load() or {}
        current = payload.get("current")
        if isinstance(current, dict):
            self.current = {**self.current, **current}
        self.revision = int(payload.get("revision", 0))
        for key, value in (payload.get("destinations") or {}).items():
            if isinstance(value, dict):
                self.destinations[str(key)] = {**value, "id": str(value.get("id", key))}
        self._loaded = True

    async def _save(self) -> None:
        await self._store.async_save({"current": self.current, "destinations": self.destinations, "revision": self.revision})

    async def async_set_current(self, value: dict[str, Any]) -> dict[str, Any]:
        await self.async_load()
        self.current = dict(value)
        self.revision += 1
        await self._save()
        return self.current

    async def async_save_destination(self, value: dict[str, Any]) -> dict[str, Any]:
        await self.async_load()
        item = {**value, "id": str(value.get("id") or uuid4().hex)}
        self.destinations[item["id"]] = item
        await self._save()
        return item

    async def async_delete_destination(self, item_id: str) -> bool:
        await self.async_load()
        removed = self.destinations.pop(str(item_id), None) is not None
        if removed:
            await self._save()
        return removed

    async def async_payload(self) -> dict[str, Any]:
        await self.async_load()
        return {"current": self.current, "destinations": list(self.destinations.values()), "revision": self.revision}
