"""Network adapters for the explicitly supported public providers."""
from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from aiohttp import ClientSession

from .const import DWD_URL, DWD_WARNINGS_PREFIX, MET_URL, OPEN_METEO_URL, RAINVIEWER_URL
from .core import Hour, normalize_open_meteo


async def async_open_meteo(session: ClientSession, latitude: float, longitude: float) -> tuple[Hour, ...]:
    params = {
        "latitude": round(latitude, 4), "longitude": round(longitude, 4), "timezone": "UTC",
        "forecast_days": 7,
        "hourly": "temperature_2m,apparent_temperature,precipitation,precipitation_probability,wind_speed_10m,wind_gusts_10m,uv_index,snowfall,weather_code,thunderstorm_probability",
        "current": "temperature_2m,apparent_temperature,precipitation,wind_speed_10m,wind_gusts_10m,weather_code",
    }
    async with session.get(OPEN_METEO_URL, params=params, timeout=20) as response:
        response.raise_for_status()
        return normalize_open_meteo(await response.json())


async def async_met_norway(session: ClientSession, latitude: float, longitude: float) -> tuple[Hour, ...]:
    params = {"lat": f"{latitude:.4f}", "lon": f"{longitude:.4f}"}
    headers = {"User-Agent": "CamperWeather/0.1 (+https://www.smartcamper765.de)"}
    async with session.get(MET_URL, params=params, headers=headers, timeout=20) as response:
        response.raise_for_status()
        payload = await response.json()
    result: list[Hour] = []
    for item in payload.get("properties", {}).get("timeseries", []):
        instant = item.get("data", {}).get("instant", {}).get("details", {})
        next_hour = item.get("data", {}).get("next_1_hours", {}).get("details", {})
        try:
            timestamp = datetime.fromisoformat(item["time"])
        except (KeyError, ValueError):
            continue
        result.append(Hour(
            timestamp,
            instant.get("air_temperature"), instant.get("air_temperature")
            , next_hour.get("precipitation_amount"), next_hour.get("probability_of_precipitation"),
            instant.get("wind_speed"), instant.get("wind_speed_of_gust"),
        ))
    return tuple(result)


async def async_dwd_warnings(session: ClientSession) -> list[dict[str, Any]]:
    async with session.get(DWD_URL, timeout=20) as response:
        response.raise_for_status()
        raw = await response.text()
    # The WarnWetter endpoint returns JavaScript JSONP, not plain JSON.
    text = raw.strip()
    if text.startswith(DWD_WARNINGS_PREFIX):
        text = text[len(DWD_WARNINGS_PREFIX):].rstrip(";)").strip()
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise TypeError("DWD-Antwort hat kein Objektformat")
    if "warnings" not in payload:
        raise ValueError("DWD-Antwort enthält kein warnings-Feld")
    grouped = payload["warnings"]
    if not isinstance(grouped, dict):
        raise TypeError("DWD-Antwort enthält keine Warnungsgruppen")
    warnings: list[dict[str, Any]] = []
    for region_id, region_warnings in grouped.items():
        if not isinstance(region_warnings, list):
            continue
        for warning in region_warnings:
            if isinstance(warning, dict):
                warnings.append({**warning, "region_id": str(region_id)})
    return warnings


async def async_radar_metadata(session: ClientSession) -> dict[str, Any]:
    async with session.get(RAINVIEWER_URL, timeout=20) as response:
        response.raise_for_status()
        payload = await response.json()
    radar = payload.get("radar", {})
    host = payload.get("host", "https://tilecache.rainviewer.com")
    frames = []
    for frame in [*radar.get("past", []), *radar.get("nowcast", [])]:
        if not isinstance(frame, dict) or not frame.get("path"):
            continue
        frames.append({
            "time": frame.get("time"),
            "path": frame["path"],
            "tile_template": f"{host}{frame['path']}/256/{{z}}/{{x}}/{{y}}/2/1_1.png",
        })
    return {
        "source": "RainViewer",
        "generated": payload.get("generated"),
        "host": host,
        "past": radar.get("past", []),
        "nowcast": radar.get("nowcast", []),
        "frames": frames,
        "tile_template": frames[-1]["tile_template"] if frames else None,
        "retrieved_at": datetime.now(UTC).isoformat(),
    }
