"""Coordinator for one camper weather configuration."""
from __future__ import annotations

import logging
import math
from datetime import UTC, datetime, timedelta
from typing import Any

from aiohttp import ClientError
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_AWNING_WIND,
    CONF_DESTINATION_NAME,
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
    LOCATION_DESTINATION,
    LOCATION_HOME_ZONE,
    LOCATION_MANUAL,
    LOCATION_TRACKER,
    PROVIDER_MET_NORWAY,
    PROVIDER_OPEN_METEO,
)
from .core import Hour, activity_score, apply_official_warning_risks, camping_score, suggest_activity_windows
from .providers import async_dwd_warnings, async_met_norway, async_open_meteo, async_radar_metadata, filter_dwd_warnings

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
        self._last_valid_location: tuple[float, float] | None = None
        self._last_query_location: tuple[float, float] | None = None
        self._location_diagnostic: dict[str, Any] = {"status": "unknown"}
        self._update_generation = 0

    def _location(self) -> tuple[float, float, str, bool]:
        runtime = self.hass.data.get(DOMAIN, {}).get(self.entry.entry_id, {}).get("location")
        override = getattr(runtime, "current", {}) if runtime else {}
        runtime_mode = override.get("mode")
        if runtime_mode == LOCATION_TRACKER:
            tracker_id = self.options.get(CONF_TRACKER, "")
            state = self.hass.states.get(tracker_id)
            if state and state.state not in {"unknown", "unavailable"}:
                lat, lon = state.attributes.get("latitude"), state.attributes.get("longitude")
                if self._valid_coordinates(lat, lon):
                    self._last_valid_location = (float(lat), float(lon))
                    self._location_diagnostic = {"status": "valid", "entity_id": tracker_id, "tracker_state": state.state, "updated_at": self._state_timestamp(state)}
                    return float(lat), float(lon), "tracker", False
            self._location_diagnostic = {"status": "unknown_tracker" if state is None else "unavailable_tracker" if state.state == "unavailable" else "missing_coordinates", "entity_id": tracker_id, "tracker_state": getattr(state, "state", None)}
            if self._last_valid_location:
                self._location_diagnostic["status"] = "stale"
                return (*self._last_valid_location, "tracker_stale", True)
            return float(self.hass.config.latitude), float(self.hass.config.longitude), "tracker_fallback", True
        if runtime_mode == LOCATION_HOME_ZONE:
            state = self.hass.states.get("zone.home")
            lat, lon = (state.attributes.get("latitude"), state.attributes.get("longitude")) if state else (None, None)
            if self._valid_coordinates(lat, lon):
                self._last_valid_location = (float(lat), float(lon))
                self._location_diagnostic = {"status": "valid", "source": "home_zone"}
                return float(lat), float(lon), "home_zone", False
        if runtime_mode in {LOCATION_MANUAL, LOCATION_DESTINATION} and self._valid_coordinates(override.get("latitude"), override.get("longitude")):
            self._last_valid_location = (float(override["latitude"]), float(override["longitude"]))
            self._location_diagnostic = {"status": "valid", "source": runtime_mode}
            return float(override["latitude"]), float(override["longitude"]), override.get("name", runtime_mode), False
        mode = self.options.get(CONF_LOCATION_MODE, LOCATION_MANUAL)
        if mode == LOCATION_TRACKER:
            tracker_id = self.options.get(CONF_TRACKER, "")
            state = self.hass.states.get(tracker_id)
            if state and state.state not in {"unknown", "unavailable"}:
                lat, lon = state.attributes.get("latitude"), state.attributes.get("longitude")
                if self._valid_coordinates(lat, lon):
                    self._last_valid_location = (float(lat), float(lon))
                    self._location_diagnostic = {"status": "valid", "entity_id": tracker_id, "tracker_state": state.state, "updated_at": self._state_timestamp(state)}
                    return float(lat), float(lon), "tracker", False
            self._location_diagnostic = {"status": "unknown_tracker" if state is None else "unavailable_tracker" if state.state == "unavailable" else "missing_coordinates", "entity_id": tracker_id, "tracker_state": getattr(state, "state", None)}
        if mode == LOCATION_HOME_ZONE:
            state = self.hass.states.get("zone.home")
            lat, lon = (state.attributes.get("latitude"), state.attributes.get("longitude")) if state else (None, None)
            if self._valid_coordinates(lat, lon):
                self._last_valid_location = (float(lat), float(lon))
                self._location_diagnostic = {"status": "valid", "source": "home_zone"}
                return float(lat), float(lon), "home_zone", False
        lat = self.options.get(CONF_LATITUDE, self.hass.config.latitude)
        lon = self.options.get(CONF_LONGITUDE, self.hass.config.longitude)
        if mode == LOCATION_DESTINATION and self._valid_coordinates(lat, lon):
            self._last_valid_location = (float(lat), float(lon))
            self._location_diagnostic = {"status": "valid", "source": "destination"}
            return float(lat), float(lon), self.options.get(CONF_DESTINATION_NAME, "destination"), False
        if mode == LOCATION_MANUAL and self._valid_coordinates(lat, lon):
            self._last_valid_location = (float(lat), float(lon))
            self._location_diagnostic = {"status": "valid", "source": "manual"}
            return float(lat), float(lon), "manual", False
        if self._last_valid_location:
            self._location_diagnostic = {"status": "stale", "source": mode}
            return (*self._last_valid_location, mode, True)
        self._location_diagnostic = {"status": "fallback", "source": mode}
        return float(self.hass.config.latitude), float(self.hass.config.longitude), f"{mode}_fallback", True

    @staticmethod
    def _state_timestamp(state: Any) -> str | None:
        value = getattr(state, "last_updated", None) or getattr(state, "last_changed", None)
        return value.isoformat() if hasattr(value, "isoformat") else None

    @staticmethod
    def _valid_coordinates(latitude: Any, longitude: Any) -> bool:
        try:
            return -90 <= float(latitude) <= 90 and -180 <= float(longitude) <= 180 and not (float(latitude) == 0 and float(longitude) == 0)
        except (TypeError, ValueError):
            return False

    @staticmethod
    def _distance_km(first: tuple[float, float], second: tuple[float, float]) -> float:
        lat1, lon1 = map(math.radians, first)
        lat2, lon2 = map(math.radians, second)
        value = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
        return 6371 * 2 * math.asin(min(1, math.sqrt(value)))

    async def _async_update_data(self) -> dict[str, Any]:
        self._update_generation += 1
        update_generation = self._update_generation
        latitude, longitude, location_source, location_stale = self._location()
        location_runtime = self.hass.data.get(DOMAIN, {}).get(self.entry.entry_id, {}).get("location")
        location_revision = getattr(location_runtime, "revision", 0)
        current_location = (latitude, longitude)
        if self.data and not location_stale and not self.data.get("errors") and self._last_query_location and self._distance_km(self._last_query_location, current_location) < 0.5:
            retained = {**self.data, "location": {**self.data.get("location", {}), "latitude": latitude, "longitude": longitude, "source": location_source, "stale": location_stale, "fallback": location_source.endswith("_fallback"), "diagnostic": self._location_diagnostic, "updated_at": datetime.now(UTC).isoformat()}}
            return retained
        self._last_query_location = current_location
        session = async_get_clientsession(self.hass)
        hours: tuple[Hour, ...] = ()
        provider = self.options.get(CONF_PROVIDER, PROVIDER_OPEN_METEO)
        errors: list[str] = []
        sources: list[str] = []
        provider_status: dict[str, dict[str, Any]] = {}
        try:
            if provider == PROVIDER_MET_NORWAY:
                hours = await async_met_norway(session, latitude, longitude)
                sources.append("met_norway")
                provider_status[PROVIDER_MET_NORWAY] = {"enabled": True, "status": "ok", "last_success": datetime.now(UTC).isoformat()}
            else:
                hours = await async_open_meteo(session, latitude, longitude)
                sources.append("open_meteo")
                provider_status[PROVIDER_OPEN_METEO] = {"enabled": True, "status": "ok", "last_success": datetime.now(UTC).isoformat()}
        except (ClientError, TimeoutError, ValueError) as err:
            LOGGER.warning("Weather provider failed (%s): %s", provider, type(err).__name__)
            errors.append(f"{provider}_failed")
            provider_status[provider] = {"enabled": True, "status": "error", "error": type(err).__name__}
            if provider == PROVIDER_OPEN_METEO and self.options.get(CONF_MET_ENABLED, True):
                try:
                    hours = await async_met_norway(session, latitude, longitude)
                    sources.append("met_norway_fallback")
                    provider_status[PROVIDER_MET_NORWAY] = {"enabled": True, "status": "fallback", "last_success": datetime.now(UTC).isoformat()}
                except (ClientError, TimeoutError, ValueError) as fallback_err:
                    LOGGER.warning("MET Norway fallback failed: %s", type(fallback_err).__name__)
                    errors.append("met_norway_failed")
                    provider_status[PROVIDER_MET_NORWAY] = {"enabled": True, "status": "error", "error": type(fallback_err).__name__}
        if not hours:
            raise UpdateFailed("Keine Wetterprognose verfügbar")
        current = hours[0]
        score, risks = camping_score(current, awning_wind=float(self.options.get(CONF_AWNING_WIND, DEFAULT_AWNING_WIND)), frost_temp=float(self.options.get(CONF_FROST_TEMP, DEFAULT_FROST_TEMP)))
        warnings: list[dict[str, Any]] = []
        dwd_status = "disabled"
        radar: dict[str, Any] = {}
        dwd_in_area = 47.0 <= latitude <= 55.2 and 5.5 <= longitude <= 15.5
        if self.options.get(CONF_DWD_ENABLED, True) and not dwd_in_area:
            dwd_status = "outside_supported_area"
            provider_status["dwd"] = {"enabled": True, "status": dwd_status}
        elif self.options.get(CONF_DWD_ENABLED, True):
            try:
                cached = getattr(self, "_dwd_cache", None)
                if cached and datetime.now(UTC) - cached[0] < timedelta(minutes=10):
                    warnings = cached[1]
                else:
                    warnings = await async_dwd_warnings(session)
                    self._dwd_cache = (datetime.now(UTC), warnings)
                sources.append("dwd")
                warnings = filter_dwd_warnings(warnings, latitude=latitude, longitude=longitude, elevation=current.elevation, location_name=location_source)
                dwd_status = "active_location_uncertain" if any(warning.get("location_uncertain") or warning.get("altitude_uncertain") for warning in warnings) else "active" if warnings else "no_warnings"
                provider_status["dwd"] = {"enabled": True, "status": dwd_status, "last_success": datetime.now(UTC).isoformat(), "warning_count": len(warnings)}
            except (ClientError, TimeoutError, ValueError) as err:
                LOGGER.debug("DWD warnings unavailable: %s", type(err).__name__)
                errors.append("dwd_failed")
                dwd_status = "unavailable"
                provider_status["dwd"] = {"enabled": True, "status": "unavailable", "error": type(err).__name__}
        warning_score, official_risks = apply_official_warning_risks(score, warnings)
        if official_risks:
            score = warning_score
            risks = [*risks, *official_risks]
        recommendations = {activity: suggest_activity_windows(list(hours), activity, reference_time=datetime.now(UTC)) for activity in ("walking", "hiking", "cycling", "ebike", "jogging", "skiing", "swimming", "barbecue", "fishing")}
        if any(risk.severity == "critical" for risk in official_risks):
            recommendations = {activity: [] for activity in recommendations}
        elif official_risks:
            for items in recommendations.values():
                for item in items:
                    item["score"] = min(item["score"], score if score is not None else 0)
                    item["risks"] = [*item["risks"], *[risk.__dict__ for risk in official_risks]]
        if self.options.get(CONF_RADAR_ENABLED, True):
            try:
                cached_radar = getattr(self, "_radar_cache", None)
                if cached_radar and datetime.now(UTC) - cached_radar[0] < timedelta(minutes=5):
                    radar = cached_radar[1]
                else:
                    radar = await async_radar_metadata(session)
                    self._radar_cache = (datetime.now(UTC), radar)
                sources.append("rainviewer")
                provider_status["rainviewer"] = {"enabled": True, "status": "ok", "last_success": radar.get("retrieved_at"), "frame_count": len(radar.get("frames", []))}
            except (ClientError, TimeoutError, ValueError) as err:
                LOGGER.debug("RainViewer metadata unavailable: %s", type(err).__name__)
                errors.append("rainviewer_failed")
                provider_status["rainviewer"] = {"enabled": True, "status": "unavailable", "error": type(err).__name__}
        latest_location = self.hass.data.get(DOMAIN, {}).get(self.entry.entry_id, {}).get("location")
        latest_revision = getattr(latest_location, "revision", location_revision)
        if latest_revision != location_revision or update_generation != self._update_generation:
            if getattr(self, "_location_retry_count", 0) == 0:
                self._location_retry_count = 1
                return await self._async_update_data()
            self._location_retry_count = 0
            raise UpdateFailed("Standort hat sich während der Wetterabfrage geändert")
        self._location_retry_count = 0
        return {
            "location": {"latitude": latitude, "longitude": longitude, "source": location_source, "stale": location_stale, "fallback": location_source.endswith("_fallback"), "diagnostic": self._location_diagnostic, "updated_at": datetime.now(UTC).isoformat()},
            "location_revision": location_revision,
            "hours": hours,
            "current": current,
            "camping_score": score,
            "risks": risks,
            "warnings": warnings,
            "radar": radar,
            "sources": sorted(set(sources)),
            "errors": errors,
            "dwd_status": dwd_status,
            "provider_status": provider_status,
            "updated_at": datetime.now(UTC),
            "forecast": [{"time": h.time.isoformat(), "temperature": h.temperature, "apparent_temperature": h.apparent_temperature, "wind": h.wind, "gusts": h.gusts, "precipitation": h.precipitation, "probability": h.precipitation_probability, "uv": h.uv, "weather_code": h.weather_code, "is_day": h.is_day, "score": camping_score(h, awning_wind=float(self.options.get(CONF_AWNING_WIND, DEFAULT_AWNING_WIND)), frost_temp=float(self.options.get(CONF_FROST_TEMP, DEFAULT_FROST_TEMP)))[0]} for h in hours[:168]],
            "recommendations": recommendations,
        }

    def activity(self, activity: str) -> tuple[int | None, list[Any]]:
        return activity_score(list(self.data.get("hours", ()))[:4], activity) if self.data else (None, [])
