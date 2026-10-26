"""Weather entity exposing the selected provider forecast."""
from __future__ import annotations

from homeassistant.components.weather import Forecast, WeatherEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfSpeed, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CamperWeatherCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([CamperWeatherEntity(hass.data[DOMAIN][entry.entry_id]["coordinator"], entry)])


class CamperWeatherEntity(CoordinatorEntity[CamperWeatherCoordinator], WeatherEntity):
    _attr_has_entity_name = True
    _attr_name = "Wetter"
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR
    def __init__(self, coordinator, entry):
        super().__init__(coordinator); self._attr_unique_id = f"{entry.entry_id}_weather"; self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}, "name": entry.title, "manufacturer": "Camper Weather"}
    @property
    def native_temperature(self): return self.coordinator.data.get("current").temperature if self.coordinator.data.get("current") else None
    @property
    def native_apparent_temperature(self): return self.coordinator.data.get("current").apparent_temperature if self.coordinator.data.get("current") else None
    @property
    def wind_speed(self): return self.coordinator.data.get("current").wind if self.coordinator.data.get("current") else None
    @property
    def condition(self): return "sunny" if (self.coordinator.data.get("camping_score") or 0) >= 70 else "cloudy"
    @property
    def forecast(self) -> list[Forecast]: return self.coordinator.data.get("forecast", [])

