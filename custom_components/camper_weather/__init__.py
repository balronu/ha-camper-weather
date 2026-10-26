"""Camper Weather Home Assistant integration."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .api import async_setup_websocket
from .const import CARD_PATH, CARD_VERSION, DOMAIN, PLATFORMS
from .coordinator import CamperWeatherCoordinator
from .location import LocationStore
from .planner import ActivityStore

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
DATA_COORDINATOR = "coordinator"


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    hass.data.setdefault(DOMAIN, {})
    card_path = Path(__file__).parent / "www" / "camper-weather-card.js"
    if hasattr(hass, "http") and hasattr(hass.http, "async_register_static_paths"):
        await hass.http.async_register_static_paths([StaticPathConfig(CARD_PATH, str(card_path), cache_headers=True)])
    if hasattr(hass, "http"):
        add_extra_js_url(hass, f"{CARD_PATH}?v={CARD_VERSION}")
    await async_setup_websocket(hass)
    hass.data[DOMAIN]["card_url"] = f"{CARD_PATH}?v={CARD_VERSION}"
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # Keep command registration valid when HA reloads an entry independently.
    await async_setup_websocket(hass)
    coordinator = CamperWeatherCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    planner = ActivityStore(hass)
    await planner.async_load()
    location = LocationStore(hass, entry.entry_id)
    await location.async_load()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {DATA_COORDINATOR: coordinator, "planner": planner, "location": location}
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unloaded


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
