"""Authenticated read-only websocket API for the Lovelace card."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from .const import DOMAIN

WS_CARD_DATA = "camper_weather/card_data"


async def async_setup_websocket(hass: HomeAssistant) -> None:
    if hass.data.get(DOMAIN, {}).get("websocket_registered"):
        return
    websocket_api.async_register_command(hass, _card_data)
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
        "entry_id": entry_id,
        "name": next((entry.title for entry in entries if entry.entry_id == entry_id), "Camper Weather"),
        "location": data.get("location"), "camping_score": data.get("camping_score"),
        "current": {key: (getattr(current, key).isoformat() if key == "time" and getattr(current, key) else getattr(current, key)) for key in ("time", "temperature", "apparent_temperature", "precipitation", "wind", "gusts", "uv")} if current else None,
        "risks": [risk.__dict__ for risk in data.get("risks", [])], "warnings": data.get("warnings", [])[:20],
        "forecast": data.get("forecast", [])[:48], "radar": data.get("radar", {}),
        "sources": data.get("sources", []), "errors": data.get("errors", []),
        "updated_at": data.get("updated_at").isoformat() if data.get("updated_at") else None,
    })
