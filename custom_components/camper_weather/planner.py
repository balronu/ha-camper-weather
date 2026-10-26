"""Persistent, forecast-backed activity planning."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .core import Hour, assess_activity_window, suggest_activity_windows


class ActivityStore:
    """Small HA Store wrapper; it stores plans, never a GPS history."""

    def __init__(self, hass: HomeAssistant) -> None:
        self._store = Store[dict[str, Any]](hass, 1, "camper_weather.activities")
        self._items: dict[str, dict[str, Any]] = {}
        self._loaded = False

    async def async_load(self) -> None:
        if self._loaded:
            return
        payload = await self._store.async_load() or {}
        self._items = {str(key): value for key, value in payload.get("items", {}).items() if isinstance(value, dict)}
        self._loaded = True

    async def async_save(self, item: dict[str, Any]) -> dict[str, Any]:
        await self.async_load()
        item = {**item, "id": item.get("id") or uuid4().hex}
        self._items[item["id"]] = item
        await self._store.async_save({"items": self._items})
        return item

    async def async_delete(self, item_id: str) -> bool:
        await self.async_load()
        removed = self._items.pop(item_id, None) is not None
        if removed:
            await self._store.async_save({"items": self._items})
        return removed

    async def async_items(self) -> list[dict[str, Any]]:
        await self.async_load()
        return list(self._items.values())


def assess_plan(plan: dict[str, Any], hours: list[Hour]) -> dict[str, Any]:
    try:
        start = datetime.fromisoformat(str(plan["start_at"]).replace("Z", "+00:00"))
        duration = int(plan["duration_minutes"])
    except (KeyError, TypeError, ValueError):
        return {"score": None, "risks": [{"name": "data", "severity": "unknown", "reason": "Ungültige Planungsdaten"}], "stale": True}
    score, risks = assess_activity_window(hours, str(plan.get("activity", "outdoor")), start, duration)
    return {"score": score, "risks": [risk.__dict__ for risk in risks], "stale": score is None}


def recommendations(hours: list[Hour], activity: str, duration_minutes: int) -> list[dict[str, Any]]:
    return suggest_activity_windows(hours, activity, duration_minutes)
