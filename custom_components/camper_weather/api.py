"""Authenticated read-only websocket API for the Lovelace card."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from aiohttp import ClientError
from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import UpdateFailed

from .const import ACTIVITIES, DOMAIN, GEOCODING_URL, VERSION
from .planner import assess_plan

WS_CARD_DATA = "camper_weather/card_data"
WS_LIST_ENTRIES = "camper_weather/list_entries"
WS_PLANNER_LIST = "camper_weather/planner/list"
WS_PLANNER_SAVE = "camper_weather/planner/save"
WS_PLANNER_DELETE = "camper_weather/planner/delete"
WS_PLANNER_ASSESS = "camper_weather/planner/assess"
WS_LOCATION_GET = "camper_weather/location/get"
WS_LOCATION_SET = "camper_weather/location/set"
WS_LOCATION_GEOCODE = "camper_weather/location/geocode"
WS_LOCATION_SAVE = "camper_weather/location/save_destination"
WS_LOCATION_DELETE = "camper_weather/location/delete_destination"


async def async_setup_websocket(hass: HomeAssistant) -> None:
    if hass.data.get(DOMAIN, {}).get("websocket_registered"):
        return
    for handler in (_card_data, _list_entries, _planner_list, _planner_save, _planner_delete, _planner_assess, _location_get, _location_set, _location_geocode, _location_save, _location_delete):
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
        "location_revision": data.get("location_revision", 0),
        "current": {key: (getattr(current, key).isoformat() if key == "time" and getattr(current, key) else getattr(current, key)) for key in ("time", "temperature", "apparent_temperature", "precipitation", "wind", "gusts", "uv", "weather_code", "is_day")} if current else None,
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


def _location_data(hass: HomeAssistant, entry_id: str) -> tuple[Any, Any] | None:
    payload = hass.data.get(DOMAIN, {}).get(entry_id)
    if not payload or "location" not in payload:
        return None
    return payload["location"], payload["coordinator"]


@websocket_api.websocket_command({vol.Required("type"): WS_LOCATION_GET, vol.Required("entry_id"): str})
@websocket_api.async_response
async def _location_get(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    result = _location_data(hass, msg["entry_id"])
    if result is None:
        connection.send_error(msg["id"], "not_found", "Camper-Weather-Eintrag nicht geladen")
        return
    store, coordinator = result
    connection.send_result(msg["id"], {**await store.async_payload(), "active": (coordinator.data or {}).get("location"), "active_revision": (coordinator.data or {}).get("location_revision", 0)})


@websocket_api.websocket_command({
    vol.Required("type"): WS_LOCATION_SET, vol.Required("entry_id"): str,
    vol.Required("mode"): vol.In({"tracker", "home_zone", "manual", "destination"}),
    vol.Optional("name"): str, vol.Optional("destination_id"): str,
    vol.Optional("latitude"): vol.Coerce(float), vol.Optional("longitude"): vol.Coerce(float),
})
@websocket_api.async_response
async def _location_set(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    result = _location_data(hass, msg["entry_id"])
    if result is None:
        connection.send_error(msg["id"], "not_found", "Camper-Weather-Eintrag nicht geladen")
        return
    store, coordinator = result
    current = {key: value for key, value in msg.items() if key in {"mode", "name", "destination_id", "latitude", "longitude"}}
    if current["mode"] in {"manual", "destination"} and not coordinator._valid_coordinates(current.get("latitude"), current.get("longitude")):
        connection.send_error(msg["id"], "invalid_location", "Für diesen Standortmodus sind gültige Koordinaten erforderlich")
        return
    await store.async_load()
    previous = dict(store.current)
    saved = await store.async_set_current(current)
    try:
        await coordinator.async_refresh()
    except (ClientError, OSError, TimeoutError, ValueError, UpdateFailed) as err:
        await store.async_set_current(previous)
        try:
            await coordinator.async_refresh()
        except (ClientError, OSError, TimeoutError, ValueError, UpdateFailed):
            connection.send_error(msg["id"], "location_refresh_failed", "Standort und vorherige Wetterdaten konnten nicht geladen werden")
            return
        connection.send_error(msg["id"], "location_refresh_failed", f"Standort konnte nicht geladen werden ({type(err).__name__})")
        return
    payload = await store.async_payload()
    connection.send_result(msg["id"], {**saved, **payload, "active": (coordinator.data or {}).get("location"), "active_revision": (coordinator.data or {}).get("location_revision", 0)})


@websocket_api.websocket_command({vol.Required("type"): WS_LOCATION_GEOCODE, vol.Required("entry_id"): str, vol.Required("query"): str})
@websocket_api.async_response
async def _location_geocode(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    if _location_data(hass, msg["entry_id"]) is None:
        connection.send_error(msg["id"], "not_found", "Camper-Weather-Eintrag nicht geladen")
        return
    query = msg["query"].strip()
    if len(query) < 2 or len(query) > 120:
        connection.send_error(msg["id"], "invalid_query", "Bitte einen Ortsnamen eingeben")
        return
    session = async_get_clientsession(hass)
    headers = {"User-Agent": "CamperWeather/0.1 (+https://www.smartcamper765.de)"}
    try:
        async with session.get(GEOCODING_URL, params={"q": query, "format": "jsonv2", "limit": 5, "accept-language": "de"}, headers=headers, timeout=8) as response:
            response.raise_for_status()
            payload = await response.json()
        results = [{"name": item.get("display_name", query), "latitude": float(item["lat"]), "longitude": float(item["lon"])} for item in payload if item.get("lat") and item.get("lon")]
    except (ClientError, OSError, TimeoutError, ValueError) as err:
        connection.send_error(msg["id"], "geocode_failed", f"Ortssuche nicht verfügbar ({type(err).__name__})")
        return
    connection.send_result(msg["id"], results)


@websocket_api.websocket_command({vol.Required("type"): WS_LOCATION_SAVE, vol.Required("entry_id"): str, vol.Required("name"): str, vol.Required("latitude"): vol.Coerce(float), vol.Required("longitude"): vol.Coerce(float), vol.Optional("id"): str})
@websocket_api.async_response
async def _location_save(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    result = _location_data(hass, msg["entry_id"])
    if result is None:
        connection.send_error(msg["id"], "not_found", "Camper-Weather-Eintrag nicht geladen")
        return
    store, coordinator = result
    if not coordinator._valid_coordinates(msg["latitude"], msg["longitude"]):
        connection.send_error(msg["id"], "invalid_location", "Ungültige Koordinaten")
        return
    connection.send_result(msg["id"], await store.async_save_destination({key: msg[key] for key in ("id", "name", "latitude", "longitude") if key in msg}))


@websocket_api.websocket_command({vol.Required("type"): WS_LOCATION_DELETE, vol.Required("entry_id"): str, vol.Required("destination_id"): str})
@websocket_api.async_response
async def _location_delete(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    result = _location_data(hass, msg["entry_id"])
    if result is None:
        connection.send_error(msg["id"], "not_found", "Camper-Weather-Eintrag nicht geladen")
        return
    connection.send_result(msg["id"], {"deleted": await result[0].async_delete_destination(msg["destination_id"])})


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
    return {"id": msg.get("id"), "activity": activity, "start_at": start_at, "duration_minutes": duration, "location_mode": msg.get("location_mode", "current"), "latitude": msg.get("latitude"), "longitude": msg.get("longitude"), "location_revision": msg.get("location_revision")}


@websocket_api.websocket_command({vol.Required("type"): WS_PLANNER_SAVE, vol.Required("entry_id"): str, vol.Required("activity"): str, vol.Required("start_at"): str, vol.Required("duration_minutes"): vol.Coerce(int), vol.Optional("id"): vol.Coerce(str), vol.Optional("location_mode"): str, vol.Optional("latitude"): vol.Coerce(float), vol.Optional("longitude"): vol.Coerce(float), vol.Optional("location_revision"): vol.Coerce(int)})
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
    runtime_location = hass.data.get(DOMAIN, {}).get(msg["entry_id"], {}).get("location")
    if msg.get("location_mode", "current") == "current" and msg.get("location_revision") is not None and msg["location_revision"] != getattr(runtime_location, "revision", 0):
        connection.send_error(msg["id"], "stale_location", "Der Standort hat sich geändert. Bitte die Aktivität neu bewerten.")
        return
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


@websocket_api.websocket_command({vol.Required("type"): WS_PLANNER_ASSESS, vol.Required("entry_id"): str, vol.Required("activity"): str, vol.Required("start_at"): str, vol.Required("duration_minutes"): vol.Coerce(int), vol.Optional("location_mode"): str, vol.Optional("latitude"): vol.Coerce(float), vol.Optional("longitude"): vol.Coerce(float), vol.Optional("location_revision"): vol.Coerce(int)})
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
