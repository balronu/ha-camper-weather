"""Optional Home Assistant actions backed by the shared assessment engine."""
from __future__ import annotations

from zoneinfo import ZoneInfo

import voluptuous as vol
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .const import ACTIVITIES, DOMAIN
from .engine import DataQuality, LocationContext, evaluate_window, serialise

SERVICE = "evaluate_window"
SCHEMA = vol.Schema({vol.Required("start_at"): cv.datetime, vol.Required("duration_minutes"): vol.All(vol.Coerce(int), vol.Range(min=15, max=720)), vol.Required("activity"): str, vol.Optional("entry_id"): str})


def async_setup_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, SERVICE):
        return

    async def evaluate(call: ServiceCall) -> ServiceResponse:
        entries = [entry for entry in hass.config_entries.async_entries(DOMAIN) if entry.state is ConfigEntryState.LOADED]
        entry_id = call.data.get("entry_id")
        entry = next((item for item in entries if item.entry_id == entry_id), None) if entry_id else entries[0] if len(entries) == 1 else None
        if entry is None:
            raise ServiceValidationError("entry_id ist bei mehreren Camper-Weather-Einträgen erforderlich")
        if call.data["activity"] not in {key for key, _ in ACTIVITIES}:
            raise ServiceValidationError("Unbekannte Aktivität")
        payload = hass.data[DOMAIN].get(entry.entry_id) or {}
        coordinator = payload.get("coordinator")
        if coordinator is None or not coordinator.data:
            raise ServiceValidationError("Camper-Weather-Daten sind noch nicht verfügbar")
        start = call.data["start_at"]
        if start.tzinfo is None:
            start = start.replace(tzinfo=ZoneInfo(hass.config.time_zone))
        location_data = coordinator.data.get("location") or {}
        location = LocationContext(location_data.get("mode", "unknown"), location_data.get("source"), location_data.get("source"), location_data.get("latitude"), location_data.get("longitude"), hass.config.time_zone, getattr(coordinator.data.get("current"), "elevation", None), bool(location_data.get("stale")))
        quality_data = coordinator.data.get("data_quality") or {}
        quality = DataQuality(quality_data.get("status", "unknown"), quality_data.get("reason", "Datenqualität unbekannt"), coordinator.data.get("updated_at"), quality_data.get("age_seconds"), bool(quality_data.get("forecast_complete", True)), tuple(quality_data.get("sources", [])))
        result = evaluate_window(coordinator.data.get("hours", ()), coordinator.data.get("warnings", ()), call.data["activity"], start, call.data["duration_minutes"], location=location, quality=quality)
        return serialise(result)

    hass.services.async_register(DOMAIN, SERVICE, evaluate, schema=SCHEMA, supports_response=SupportsResponse.ONLY)
