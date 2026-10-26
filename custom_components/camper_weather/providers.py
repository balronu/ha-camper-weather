"""Network adapters for the explicitly supported public providers."""
from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from aiohttp import ClientSession

from .const import DWD_URL, DWD_WARNINGS_PREFIX, MET_URL, OPEN_METEO_URL, RAINVIEWER_URL
from .core import Hour, normalize_open_meteo


def _warning_identity(warning: dict[str, Any]) -> tuple[Any, ...]:
    """Return a stable identity that keeps periods and warning areas distinct."""
    identifier = next((warning.get(key) for key in ("warningId", "warning_id", "warnId", "identifier", "id") if warning.get(key) not in (None, "")), None)
    area = (warning.get("region_id"), warning.get("regionName"), warning.get("region"), warning.get("area"))
    period = (warning.get("start"), warning.get("end"), warning.get("altitudeStart"), warning.get("altitudeEnd"))
    if identifier is not None:
        return ("official", str(identifier), *area, *period)
    return ("semantic", warning.get("event"), warning.get("headline"), *area, *period, warning.get("level"))


def _warning_summary(warning: dict[str, Any]) -> str:
    text = str(warning.get("headline") or warning.get("event") or "Amtliche Wetterwarnung").strip()
    if len(text) <= 120:
        return text
    return f"{text[:117].rstrip()}…"


def deduplicate_dwd_warnings(warnings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge exact duplicate records while retaining distinct periods and areas."""
    merged: dict[tuple[Any, ...], dict[str, Any]] = {}
    for raw in warnings:
        item = dict(raw)
        key = _warning_identity(item)
        if key in merged:
            # Some DWD payloads split headline/description/instructions over records.
            merged[key] = {**merged[key], **{field: value for field, value in item.items() if value not in (None, "")}}
        else:
            merged[key] = item
    result = list(merged.values())
    for item in result:
        item["summary"] = _warning_summary(item)
    result.sort(key=lambda item: (-int(item.get("level") or 0), str(item.get("start") or ""), str(item.get("regionName") or "")))
    return result


async def async_open_meteo(session: ClientSession, latitude: float, longitude: float) -> tuple[Hour, ...]:
    params = {
        "latitude": round(latitude, 4), "longitude": round(longitude, 4), "timezone": "UTC",
        "forecast_days": 7,
        "hourly": "temperature_2m,apparent_temperature,precipitation,precipitation_probability,wind_speed_10m,wind_gusts_10m,uv_index,snowfall,weather_code,thunderstorm_probability,is_day",
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


def _point_in_polygon(latitude: float, longitude: float, polygon: list[tuple[float, float]]) -> bool:
    inside = False
    for index, (lat_a, lon_a) in enumerate(polygon):
        lat_b, lon_b = polygon[index - 1]
        if (lon_a > longitude) != (lon_b > longitude) and latitude < (lat_b - lat_a) * (longitude - lon_a) / (lon_b - lon_a) + lat_a:
            inside = not inside
    return inside


def filter_dwd_warnings(
    warnings: list[dict[str, Any]], *, latitude: float, longitude: float,
    elevation: float | None = None, location_name: str | None = None,
) -> list[dict[str, Any]]:
    """Filter active DWD records without turning unknown scope into all-clear.

    The WarnApp JSON feed is district-level and intentionally has no polygons.
    Records with a polygon are checked geometrically; district-only records are
    retained with an explicit uncertainty marker for conservative scoring.
    """
    now_ms = datetime.now(UTC).timestamp() * 1000
    result_by_identity: list[dict[str, Any]] = []
    for warning in warnings:
        try:
            if warning.get("start") and float(warning["start"]) > now_ms:
                continue
            if warning.get("end") and float(warning["end"]) < now_ms:
                continue
        except (TypeError, ValueError):
            continue
        altitude_start = warning.get("altitudeStart")
        altitude_end = warning.get("altitudeEnd")
        try:
            if elevation is not None and altitude_start is not None and elevation < float(altitude_start):
                continue
            if elevation is not None and altitude_end is not None and elevation > float(altitude_end):
                continue
        except (TypeError, ValueError):
            pass
        item = dict(warning)
        item["altitude_uncertain"] = bool((altitude_start is not None or altitude_end is not None) and elevation is None)
        polygon = warning.get("polygon")
        parsed_polygon: list[tuple[float, float]] = []
        if isinstance(polygon, str):
            for point in polygon.split():
                try:
                    lat, lon = point.split(",", 1)
                    parsed_polygon.append((float(lat), float(lon)))
                except (ValueError, TypeError):
                    continue
        if parsed_polygon:
            if not _point_in_polygon(latitude, longitude, parsed_polygon):
                continue
        else:
            region_name = str(warning.get("regionName") or "").casefold()
            item["location_uncertain"] = not bool(location_name and region_name and region_name in location_name.casefold())
        result_by_identity.append(item)
    return deduplicate_dwd_warnings(result_by_identity)


async def async_dwd_warnings(session: ClientSession) -> list[dict[str, Any]]:
    # The endpoint is a relatively large JSONP document. Keep the request
    # bounded so a provider outage cannot hold up the coordinator indefinitely.
    async with session.get(DWD_URL, timeout=10) as response:
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
