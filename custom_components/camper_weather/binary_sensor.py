"""Camping warning binary sensors."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CamperWeatherCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    c = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([RiskSensor(c, entry, "awning", "Markisenwarnung"), RiskSensor(c, entry, "frost", "Frostwarnung"), RiskSensor(c, entry, "storm", "Sturmwarnung")])


class RiskSensor(CoordinatorEntity[CamperWeatherCoordinator], BinarySensorEntity):
    _attr_has_entity_name = True
    def __init__(self, coordinator, entry, risk_name, name):
        super().__init__(coordinator); self.risk_name = risk_name; self._attr_name = name; self._attr_unique_id = f"{entry.entry_id}_{risk_name}"; self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}, "name": entry.title, "manufacturer": "Camper Weather"}
    @property
    def is_on(self): return any(r.name == self.risk_name for r in self.coordinator.data.get("risks", []))
    @property
    def extra_state_attributes(self): return {"reason": next((r.reason for r in self.coordinator.data.get("risks", []) if r.name == self.risk_name), None)}

