"""Camper Weather constants."""
from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "camper_weather"
VERSION = "0.1.1"
CARD_VERSION = VERSION
CARD_PATH = "/camper_weather/camper-weather-card.js"
PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.WEATHER]

CONF_NAME = "name"
CONF_PROVIDER = "provider"
CONF_TRACKER = "tracker"
CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"
CONF_LOCATION_MODE = "location_mode"
CONF_MET_ENABLED = "met_enabled"
CONF_DWD_ENABLED = "dwd_enabled"
CONF_RADAR_ENABLED = "radar_enabled"
CONF_REFRESH = "refresh_minutes"
CONF_AWNING_WIND = "awning_wind_kmh"
CONF_FROST_TEMP = "frost_temperature_c"
CONF_DESTINATION_NAME = "destination_name"

LOCATION_TRACKER = "tracker"
LOCATION_MANUAL = "manual"
LOCATION_HOME_ZONE = "home_zone"
LOCATION_DESTINATION = "destination"
PROVIDER_OPEN_METEO = "open_meteo"
PROVIDER_MET_NORWAY = "met_norway"

DEFAULT_REFRESH = 30
DEFAULT_AWNING_WIND = 38.0
DEFAULT_FROST_TEMP = 2.0
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
MET_URL = "https://api.met.no/weatherapi/locationforecast/2.0/compact"
DWD_URL = "https://www.dwd.de/DWD/warnungen/warnapp/json/warnings.json"
DWD_CAP_INDEX_URL = "https://opendata.dwd.de/weather/alerts/cap/DISTRICT_CELLS_STAT/"
DWD_CUSTOMER_SHAPE_URL = "https://www.dwd.de/DE/leistungen/opendata/help/warnungen/cap_landkreise_shape_zip.zip?__blob=publicationFile&v=11"
DWD_COAST_SHAPE_URL = "https://www.dwd.de/DE/leistungen/opendata/help/warnungen/cap_kueste_shape_zip.zip?__blob=publicationFile&v=6"
RAINVIEWER_URL = "https://api.rainviewer.com/public/weather-maps.json"
DWD_WARNINGS_PREFIX = "warnWetter.loadWarnings("
GEOCODING_URL = "https://nominatim.openstreetmap.org/search"

ACTIVITIES = (("walking", "Spazieren"), ("hiking", "Wandern"), ("cycling", "Fahrrad"), ("ebike", "E-Bike"), ("jogging", "Joggen"), ("skiing", "Skifahren"), ("swimming", "Schwimmen"), ("barbecue", "Grillen"), ("fishing", "Angeln"))
