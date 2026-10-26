"""Coordinator for one camper weather configuration."""
from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from aiohttp import ClientError
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_AWNING_WIND,
    CONF_DWD_ENABLED,
    CONF_FROST_TEMP,
    CONF_LATITUDE,
    CONF_LOCATION_MODE,
    CONF_LONGITUDE,
    CONF_MET_ENABLED,
    CONF_PROVIDER,
    CONF_RADAR_ENABLED,
    CONF_REFRESH,
    CONF_TRACKER,
    DEFAULT_AWNING_WIND,
    DEFAULT_FROST_TEMP,
    DEFAULT_REFRESH,
    DOMAIN,
    LOCATION_MANUAL,
    LOCATION_TRACKER,
    PROVIDER_MET_NORWAY,
    PROVIDER_OPEN_METEO,
)
from .core import Hour, activity_score, camping_score
from .providers import async_dwd_warnings, async_met_norway, async_open_meteo, async_radar_metadata

LOGGER = logging.getLogger(__name__)


class CamperWeatherCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch one location and keep provider provenance explicit."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.options = {**entry.data, **entry.options}
        super().__init__(
            hass, LOGGER, name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(minutes=int(self.options.get(CONF_REFRESH, DEFAULT_REFRESH))),
        )

    def _location(self) -> tuple[float, float, str]:
        if self.options.get(CONF_LOCATION_MODE, LOCATION_MANUAL) == LOCATION_TRACKER:
            state = self.hass.states.get(self.options.get(CONF_TRACKER, ""))
            if state and state.state not in {"unknown", "unavailable"}:
                lat, lon = state.attributes.get("latitude"), state.attributes.get("longitude")
                if lat is not None and lon is not None:
                    return float(lat), float(lon), "tracker"
        return float(self.options.get(CONF_LATITUDE, self.hass.config.latitude)), float(self.options.get(CONF_LONGITUDE, self.hass.config.longitude)), "manual"

    async def _async_update_data(self) -> dict[str, Any]:
        latitude, longitude, location_source = self._location()
        session = async_get_clientsession(self.hass)
        hours: tuple[Hour, ...] = ()
        provider = self.options.get(CONF_PROVIDER, PROVIDER_OPEN_METEO)
        errors: list[str] = []
        sources: list[str] = []
        try:
            if provider == PROVIDER_MET_NORWAY:
                hours = await async_met_norway(session, latitude, longitude)
                sources.append("met_norway")
            else:
                hours = await async_open_meteo(session, latitude, longitude)
                sources.append("open_meteo")
        except (ClientError, TimeoutError, ValueError) as err:
            LOGGER.warning("Weather provider failed (%s): %s", provider, type(err).__name__)
            errors.append(f"{provider}_failed")
            if provider == PROVIDER_OPEN_METEO and self.options.get(CONF_MET_ENABLED, True):
                try:
                    hours = await async_met_norway(session, latitude, longitude)
                    sources.append("met_norway_fallback")
                except (ClientError, TimeoutError, ValueError) as fallback_err:
                    LOGGER.warning("MET Norway fallback failed: %s", type(fallback_err).__name__)
                    errors.append("met_norway_failed")
        if not hours:
            raise UpdateFailed("Keine Wetterprognose verfügbar")
        current = hours[0]
        score, risks = camping_score(current, awning_wind=float(self.options.get(CONF_AWNING_WIND, DEFAULT_AWNING_WIND)), frost_temp=float(self.options.get(CONF_FROST_TEMP, DEFAULT_FROST_TEMP)))
        warnings: list[dict[str, Any]] = []
        radar: dict[str, Any] = {}
        if self.options.get(CONF_DWD_ENABLED, True):
            try:
                warnings = await async_dwd_warnings(session)
                sources.append("dwd")
            except (ClientError, TimeoutError, ValueError) as err:
                LOGGER.debug("DWD warnings unavailable: %s", type(err).__name__)
                errors.append("dwd_failed")
        if self.options.get(CONF_RADAR_ENABLED, True):
            try:
                radar = await async_radar_metadata(session)
                sources.append("rainviewer")
            except (ClientError, TimeoutError, ValueError) as err:
                LOGGER.debug("RainViewer metadata unavailable: %s", type(err).__name__)
                errors.append("rainviewer_failed")
        return {
            "location": {"latitude": latitude, "longitude": longitude, "source": location_source},
            "hours": hours,
            "current": current,
            "camping_score": score,
            "risks": risks,
            "warnings": warnings,
            "radar": radar,
            "sources": sorted(set(sources)),
            "errors": errors,
            "updated_at": datetime.now(UTC),
            "forecast": [{"time": h.time.isoformat(), "temperature": h.temperature, "wind": h.wind, "gusts": h.gusts, "precipitation": h.precipitation, "probability": h.precipitation_probability, "score": camping_score(h, awning_wind=float(self.options.get(CONF_AWNING_WIND, DEFAULT_AWNING_WIND)), frost_temp=float(self.options.get(CONF_FROST_TEMP, DEFAULT_FROST_TEMP)))[0]} for h in hours[:48]],
        }

    def activity(self, activity: str) -> tuple[int | None, list[Any]]:
        return activity_score(list(self.data.get("hours", ()))[:4], activity) if self.data else (None, [])
