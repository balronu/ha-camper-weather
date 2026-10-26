"""Authenticated read-only websocket API for the Lovelace card."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from .const import ACTIVITIES, DOMAIN, VERSION
from .planner import assess_plan

WS_CARD_DATA = "camper_weather/card_data"
WS_LIST_ENTRIES = "camper_weather/list_entries"
WS_PLANNER_LIST = "camper_weather/planner/list"
WS_PLANNER_SAVE = "camper_weather/planner/save"
WS_PLANNER_DELETE = "camper_weather/planner/delete"
WS_PLANNER_ASSESS = "camper_weather/planner/assess"


async def async_setup_websocket(hass: HomeAssistant) -> None:
    if hass.data.get(DOMAIN, {}).get("websocket_registered"):
        return
    for handler in (_card_data, _list_entries, _planner_list, _planner_save, _planner_delete, _planner_assess):
        websocket_api.async_register_command(hass, handler)
    hass.data.setdefault(DOMAIN, {})["websocket_registered"] = True


@websocket_api.websocket_command({vol.Required("type"): WS_CARD_DATA, vol.Optional("entry_id"): str})
@websocket_api.async_response
async def _card_data(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    entries = [entry for entry in hass.config_entries.async_entries(DOMAIN) if entry.state is ConfigEntryState.LOADED]
    entry_id = msg.get("entry_id")
    if entry_id is None:
        if len(entries) != 1:
            connection.send_error(msg["id"], "entry_required", "Genau ein geladener Camper-Weather-Eintrag ist erforderlich")
            return
        entry_id = entries[0].entry_id
    payload = hass.data.get(DOMAIN, {}).get(entry_id)
    if not payload:
        connection.send_error(msg["id"], "not_found", "Camper-Weather-Eintrag nicht geladen")
        return
    data = payload["coordinator"].data or {}
    current = data.get("current")
    connection.send_result(msg["id"], {
        "version": VERSION,
        "entry_id": entry_id,
        "name": next((entry.title for entry in entries if entry.entry_id == entry_id), "Camper Weather"),
        "location": data.get("location"), "camping_score": data.get("camping_score"),
        "current": {key: (getattr(current, key).isoformat() if key == "time" and getattr(current, key) else getattr(current, key)) for key in ("time", "temperature", "apparent_temperature", "precipitation", "wind", "gusts", "uv")} if current else None,
        "risks": [risk.__dict__ for risk in data.get("risks", [])], "warnings": data.get("warnings", [])[:20],
        "forecast": data.get("forecast", [])[:168], "radar": data.get("radar", {}),
        "recommendations": data.get("recommendations", {}),
        "provider_status": data.get("provider_status", {}),
        "dwd_status": data.get("dwd_status", "unknown"),
        "sources": data.get("sources", []), "errors": data.get("errors", []),
        "updated_at": data.get("updated_at").isoformat() if data.get("updated_at") else None,
    })


def _entry_payload(hass: HomeAssistant, entry_id: str | None) -> tuple[dict[str, Any] | None, ConfigEntryState | None]:
    entries = [entry for entry in hass.config_entries.async_entries(DOMAIN) if entry.state is ConfigEntryState.LOADED]
    if entry_id is None and len(entries) == 1:
        entry_id = entries[0].entry_id
    if entry_id is None:
        return None, None
    payload = hass.data.get(DOMAIN, {}).get(entry_id)
    return payload, next((entry.state for entry in entries if entry.entry_id == entry_id), None)


@websocket_api.websocket_command({vol.Required("type"): WS_LIST_ENTRIES})
@websocket_api.async_response
async def _list_entries(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    entries = hass.config_entries.async_entries(DOMAIN)
    connection.send_result(msg["id"], [{"entry_id": entry.entry_id, "name": entry.title, "loaded": entry.state is ConfigEntryState.LOADED} for entry in entries])


def _planner_data(hass: HomeAssistant, entry_id: str) -> tuple[Any, Any] | None:
    payload = hass.data.get(DOMAIN, {}).get(entry_id)
    if not payload or "planner" not in payload:
        return None
    return payload["planner"], payload["coordinator"]


@websocket_api.websocket_command({vol.Required("type"): WS_PLANNER_LIST, vol.Required("entry_id"): str})
@websocket_api.async_response
async def _planner_list(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    result = _planner_data(hass, msg["entry_id"])
    if result is None:
        connection.send_error(msg["id"], "not_found", "Camper-Weather-Eintrag nicht geladen")
        return
    store, coordinator = result
    hours = list((coordinator.data or {}).get("hours", ()))
    connection.send_result(msg["id"], [{**item, "assessment": assess_plan(item, hours)} for item in await store.async_items()])


def _validate_plan(msg: dict[str, Any]) -> dict[str, Any]:
    activity = msg.get("activity")
    if activity not in {key for key, _ in ACTIVITIES}:
        raise ValueError("Unbekannte Aktivität")
    duration = int(msg.get("duration_minutes", 0))
    if not 15 <= duration <= 720:
        raise ValueError("Die Dauer muss zwischen 15 und 720 Minuten liegen")
    start_at = str(msg.get("start_at", ""))
    if not start_at:
        raise ValueError("Startzeit fehlt")
    # Parsing also rejects malformed user input; the stored value remains ISO text.
    from datetime import datetime
    datetime.fromisoformat(start_at)
    return {"id": msg.get("id"), "activity": activity, "start_at": start_at, "duration_minutes": duration, "location_mode": msg.get("location_mode", "current"), "latitude": msg.get("latitude"), "longitude": msg.get("longitude")}


@websocket_api.websocket_command({vol.Required("type"): WS_PLANNER_SAVE, vol.Required("entry_id"): str, vol.Required("activity"): str, vol.Required("start_at"): str, vol.Required("duration_minutes"): vol.Coerce(int), vol.Optional("id"): vol.Coerce(str), vol.Optional("location_mode"): str, vol.Optional("latitude"): vol.Coerce(float), vol.Optional("longitude"): vol.Coerce(float)})
@websocket_api.async_response
async def _planner_save(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    result = _planner_data(hass, msg["entry_id"])
    if result is None:
        connection.send_error(msg["id"], "not_found", "Camper-Weather-Eintrag nicht geladen")
        return
    try:
        item = _validate_plan(msg)
    except (TypeError, ValueError) as err:
        connection.send_error(msg["id"], "invalid_plan", str(err))
        return
    store, coordinator = result
    item = await store.async_save(item)
    connection.send_result(msg["id"], {**item, "assessment": assess_plan(item, list((coordinator.data or {}).get("hours", ())))})


@websocket_api.websocket_command({vol.Required("type"): WS_PLANNER_DELETE, vol.Required("entry_id"): str, vol.Required("plan_id"): vol.Coerce(str)})
@websocket_api.async_response
async def _planner_delete(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    result = _planner_data(hass, msg["entry_id"])
    if result is None:
        connection.send_error(msg["id"], "not_found", "Camper-Weather-Eintrag nicht geladen")
        return
    connection.send_result(msg["id"], {"deleted": await result[0].async_delete(msg["plan_id"])})


@websocket_api.websocket_command({vol.Required("type"): WS_PLANNER_ASSESS, vol.Required("entry_id"): str, vol.Required("activity"): str, vol.Required("start_at"): str, vol.Required("duration_minutes"): vol.Coerce(int), vol.Optional("location_mode"): str, vol.Optional("latitude"): vol.Coerce(float), vol.Optional("longitude"): vol.Coerce(float)})
@websocket_api.async_response
async def _planner_assess(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    result = _planner_data(hass, msg["entry_id"])
    if result is None:
        connection.send_error(msg["id"], "not_found", "Camper-Weather-Eintrag nicht geladen")
        return
    try:
        item = _validate_plan(msg)
    except (TypeError, ValueError) as err:
        connection.send_error(msg["id"], "invalid_plan", str(err))
        return
    connection.send_result(msg["id"], assess_plan(item, list((result[1].data or {}).get("hours", ()))))
