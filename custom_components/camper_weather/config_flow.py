"""Config and options flow for Camper Weather."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import callback
from homeassistant.helpers.selector import EntitySelector, EntitySelectorConfig, SelectSelector, SelectSelectorConfig, SelectSelectorMode

from .const import *


def _schema(values: dict[str, Any], hass, *, options: bool = False) -> vol.Schema:
    return vol.Schema({
        vol.Required(CONF_NAME, default=values.get(CONF_NAME, "Wohnmobil")): str,
        vol.Required(CONF_PROVIDER, default=values.get(CONF_PROVIDER, PROVIDER_OPEN_METEO)): SelectSelector(SelectSelectorConfig(options=[{"value": PROVIDER_OPEN_METEO, "label": "Open-Meteo"}, {"value": PROVIDER_MET_NORWAY, "label": "MET Norway"}], mode=SelectSelectorMode.DROPDOWN)),
        vol.Required(CONF_LOCATION_MODE, default=values.get(CONF_LOCATION_MODE, LOCATION_TRACKER)): SelectSelector(SelectSelectorConfig(options=[{"value": LOCATION_TRACKER, "label": "Home-Assistant-Device-Tracker"}, {"value": LOCATION_MANUAL, "label": "Manueller Standort"}, {"value": LOCATION_HOME_ZONE, "label": "Home Assistant Home-Zone"}, {"value": LOCATION_DESTINATION, "label": "Temporärer Zielort"}], mode=SelectSelectorMode.DROPDOWN)),
        vol.Optional(CONF_TRACKER, default=values.get(CONF_TRACKER, "device_tracker.wohnmobil_zoe")): EntitySelector(EntitySelectorConfig(domain="device_tracker")),
        vol.Optional(CONF_LATITUDE, default=values.get(CONF_LATITUDE, hass.config.latitude)): vol.Coerce(float),
        vol.Optional(CONF_LONGITUDE, default=values.get(CONF_LONGITUDE, hass.config.longitude)): vol.Coerce(float),
        vol.Optional(CONF_DESTINATION_NAME, default=values.get(CONF_DESTINATION_NAME, "Zielort")): str,
        vol.Required(CONF_MET_ENABLED, default=values.get(CONF_MET_ENABLED, True)): bool,
        vol.Required(CONF_DWD_ENABLED, default=values.get(CONF_DWD_ENABLED, True)): bool,
        vol.Required(CONF_RADAR_ENABLED, default=values.get(CONF_RADAR_ENABLED, True)): bool,
        vol.Required(CONF_REFRESH, default=values.get(CONF_REFRESH, DEFAULT_REFRESH)): vol.All(vol.Coerce(int), vol.Range(min=10, max=1440)),
        vol.Required(CONF_AWNING_WIND, default=values.get(CONF_AWNING_WIND, DEFAULT_AWNING_WIND)): vol.All(vol.Coerce(float), vol.Range(min=10, max=150)),
        vol.Required(CONF_FROST_TEMP, default=values.get(CONF_FROST_TEMP, DEFAULT_FROST_TEMP)): vol.All(vol.Coerce(float), vol.Range(min=-20, max=10)),
    })


class CamperWeatherConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            mode = user_input.get(CONF_LOCATION_MODE, LOCATION_TRACKER)
            if mode in {LOCATION_MANUAL, LOCATION_DESTINATION} and (CONF_LATITUDE not in user_input or CONF_LONGITUDE not in user_input):
                return self.async_show_form(step_id="user", data_schema=_schema(user_input, self.hass), errors={"base": "location_required"})
            if CONF_LATITUDE in user_input and not -90 <= float(user_input[CONF_LATITUDE]) <= 90:
                return self.async_show_form(step_id="user", data_schema=_schema(user_input, self.hass), errors={CONF_LATITUDE: "invalid_latitude"})
            if CONF_LONGITUDE in user_input and not -180 <= float(user_input[CONF_LONGITUDE]) <= 180:
                return self.async_show_form(step_id="user", data_schema=_schema(user_input, self.hass), errors={CONF_LONGITUDE: "invalid_longitude"})
            await self.async_set_unique_id(user_input[CONF_NAME].strip().lower())
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)
        return self.async_show_form(step_id="user", data_schema=_schema({}, self.hass))

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return CamperWeatherOptionsFlow()


class CamperWeatherOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            mode = user_input.get(CONF_LOCATION_MODE, LOCATION_TRACKER)
            if mode in {LOCATION_MANUAL, LOCATION_DESTINATION} and (CONF_LATITUDE not in user_input or CONF_LONGITUDE not in user_input):
                return self.async_show_form(step_id="init", data_schema=_schema(user_input, self.hass), errors={"base": "location_required"})
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(step_id="init", data_schema=_schema({**self.config_entry.data, **self.config_entry.options}, self.hass, options=True))
