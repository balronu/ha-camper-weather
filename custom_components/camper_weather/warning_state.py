"""Persistent warning state transitions without false endings on outages."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from homeassistant.helpers.storage import Store

from .engine import WarningIdentity, WarningState


class WarningStateTracker:
    """Deduplicate warning transitions per config entry."""

    def __init__(self, hass: Any, entry_id: str) -> None:
        self._store = Store[dict[str, Any]](hass, 1, f"camper_weather.warning_state.{entry_id}")
        self._active: dict[str, WarningState] = {}
        self._loaded = False

    async def async_load(self) -> None:
        if self._loaded:
            return
        payload = await self._store.async_load() or {}
        for key, item in (payload.get("active") or {}).items():
            try:
                identity = WarningIdentity(**item["identity"])
                self._active[key] = WarningState(identity, "active", int(item["level"]), str(item["event"]), str(item["source"]), datetime.fromisoformat(item["observed_at"]), str(item.get("quality", "known")))
            except (KeyError, TypeError, ValueError):
                continue
        self._loaded = True

    def _save(self) -> None:
        self._store.async_delay_save(lambda: {"active": {key: {"identity": state.identity.__dict__, "phase": state.phase, "level": state.level, "event": state.event, "source": state.source, "observed_at": state.observed_at.isoformat(), "quality": state.quality} for key, state in self._active.items()}}, 5)

    def update(self, warnings: list[dict[str, Any]], *, available: bool, source: str = "dwd", now: datetime | None = None) -> list[WarningState]:
        now = now or datetime.now(UTC)
        if not available:
            return []
        current: dict[str, WarningState] = {}
        events: list[WarningState] = []
        for warning in warnings:
            identity = WarningIdentity.from_warning(warning)
            key = identity.key()
            event = str(warning.get("summary") or warning.get("event") or "Amtliche Wetterwarnung")
            quality = "uncertain" if warning.get("location_uncertain") or warning.get("altitude_uncertain") else "known"
            previous = self._active.get(key)
            if previous is None:
                state = WarningState(identity, "started", identity.level, event, source, now, quality)
                events.append(state)
            elif previous.level != identity.level or previous.event != event or previous.quality != quality:
                state = WarningState(identity, "changed", identity.level, event, source, now, quality)
                events.append(state)
            else:
                state = WarningState(identity, "active", identity.level, event, source, now, quality)
            current[key] = state
        for key, previous in self._active.items():
            if key not in current:
                events.append(WarningState(previous.identity, "ended", previous.level, previous.event, previous.source, now, previous.quality))
        self._active = {key: WarningState(state.identity, "active", state.level, state.event, state.source, state.observed_at, state.quality) for key, state in current.items()}
        if events:
            self._save()
        return events
