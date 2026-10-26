"""Camper Weather sensors."""
from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfSpeed, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CamperWeatherCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: CamperWeatherCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([CampingScoreSensor(coordinator, entry), CurrentTemperatureSensor(coordinator, entry), WindSensor(coordinator, entry), WarningCountSensor(coordinator, entry)])


class Base(CoordinatorEntity[CamperWeatherCoordinator], SensorEntity):
    _attr_has_entity_name = True
    def __init__(self, coordinator, entry):
        super().__init__(coordinator); self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}, "name": entry.title, "manufacturer": "Camper Weather"}


class CampingScoreSensor(Base):
    _attr_name = "Campingwetter"
    _attr_unique_id_suffix = "camping_score"
    _attr_native_unit_of_measurement = PERCENTAGE
    def __init__(self, c, e): super().__init__(c, e); self._attr_unique_id = f"{e.entry_id}_camping_score"
    @property
    def native_value(self): return self.coordinator.data.get("camping_score")
    @property
    def extra_state_attributes(self): return {"source": self.coordinator.data.get("sources", []), "risks": [r.__dict__ for r in self.coordinator.data.get("risks", [])]}


class CurrentTemperatureSensor(Base):
    _attr_name = "Temperatur"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    def __init__(self, c, e): super().__init__(c, e); self._attr_unique_id = f"{e.entry_id}_temperature"
    @property
    def native_value(self): return self.coordinator.data.get("current").temperature if self.coordinator.data.get("current") else None


class WindSensor(Base):
    _attr_name = "Wind"
    _attr_native_unit_of_measurement = UnitOfSpeed.KILOMETERS_PER_HOUR
    def __init__(self, c, e): super().__init__(c, e); self._attr_unique_id = f"{e.entry_id}_wind"
    @property
    def native_value(self): return self.coordinator.data.get("current").wind if self.coordinator.data.get("current") else None


class WarningCountSensor(Base):
    _attr_name = "Amtliche Warnungen"
    def __init__(self, c, e): super().__init__(c, e); self._attr_unique_id = f"{e.entry_id}_warning_count"
    @property
    def native_value(self): return len(self.coordinator.data.get("warnings", []))

