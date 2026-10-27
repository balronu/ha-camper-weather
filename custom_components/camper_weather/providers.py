"""Network adapters for the explicitly supported public providers."""
from __future__ import annotations

import json
import re
import struct
from datetime import UTC, datetime
from io import BytesIO
from typing import Any
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile

from aiohttp import ClientError, ClientSession

from .const import (
    DWD_CAP_INDEX_URL,
    DWD_COAST_SHAPE_URL,
    DWD_CUSTOMER_SHAPE_URL,
    DWD_URL,
    DWD_WARNINGS_PREFIX,
    MET_URL,
    OPEN_METEO_URL,
    RAINVIEWER_URL,
)
from .core import Hour, normalize_open_meteo

# WarnWetter's structured 501000xxx namespace identifies official marine
# areas. These records have no land polygon in the public JSON feed.
DWD_MARINE_AREA_PREFIX = "501000"


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
        "latitude": round(latitude, 4), "longitude": round(longitude, 4), "timezone": "auto",
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


def _parse_polygon(value: Any) -> list[tuple[float, float]]:
    if not isinstance(value, str):
        return []
    points: list[tuple[float, float]] = []
    for point in value.split():
        try:
            lat, lon = point.split(",", 1)
            points.append((float(lat), float(lon)))
        except (ValueError, TypeError):
            continue
    return points


def _read_dwd_shapefile(archive: bytes) -> dict[str, list[list[tuple[float, float]]]]:
    """Read the small official DWD polygon archive without extra HA dependencies."""
    geometries: dict[str, list[list[tuple[float, float]]]] = {}
    with ZipFile(BytesIO(archive)) as zipped:
        shp_name = next(name for name in zipped.namelist() if name.lower().endswith(".shp"))
        dbf_name = next(name for name in zipped.namelist() if name.lower().endswith(".dbf"))
        shp = zipped.read(shp_name)
        dbf = zipped.read(dbf_name)

    field_count = int.from_bytes(dbf[8:10], "little")
    record_size = int.from_bytes(dbf[10:12], "little")
    fields: list[tuple[str, int]] = []
    offset = 32
    while offset + 32 <= field_count:
        descriptor = dbf[offset : offset + 32]
        if descriptor[0] == 0x0D:
            break
        name = descriptor[:11].split(b"\0", 1)[0].decode("latin-1")
        fields.append((name, descriptor[16]))
        offset += 32
    header_size = field_count
    record_count = int.from_bytes(dbf[4:8], "little")
    attributes: list[dict[str, str]] = []
    for index in range(record_count):
        start = header_size + index * record_size
        row = dbf[start : start + record_size]
        values: dict[str, str] = {}
        cursor = 1
        for name, width in fields:
            values[name] = row[cursor : cursor + width].decode("latin-1").strip()
            cursor += width
        attributes.append(values)

    cursor = 100
    shape_index = 0
    while cursor + 8 <= len(shp) and shape_index < len(attributes):
        content_words = struct.unpack(">i", shp[cursor + 4 : cursor + 8])[0]
        content = shp[cursor + 8 : cursor + 8 + content_words * 2]
        cursor += 8 + content_words * 2
        shape_index += 1
        if len(content) < 44 or struct.unpack("<i", content[:4])[0] != 5:
            continue
        part_count, point_count = struct.unpack("<ii", content[36:44])
        parts_offset = 44
        parts = struct.unpack(f"<{part_count}i", content[parts_offset : parts_offset + 4 * part_count])
        points_offset = parts_offset + 4 * part_count
        points = [struct.unpack("<dd", content[points_offset + index * 16 : points_offset + (index + 1) * 16]) for index in range(point_count)]
        rings: list[list[tuple[float, float]]] = []
        for part_index, start in enumerate(parts):
            end = parts[part_index + 1] if part_index + 1 < len(parts) else point_count
            rings.append([(latitude, longitude) for longitude, latitude in points[start:end]])
        warncell = attributes[shape_index - 1].get("WARNCELLID", "")
        if warncell:
            geometries[warncell] = rings
    return geometries


async def async_dwd_warncell_geometries(session: ClientSession) -> dict[str, list[list[tuple[float, float]]]]:
    """Fetch official DWD county and coast polygons used by WarncellIDs."""
    geometries: dict[str, list[list[tuple[float, float]]]] = {}
    for url in (DWD_CUSTOMER_SHAPE_URL, DWD_COAST_SHAPE_URL):
        async with session.get(url, timeout=20) as response:
            response.raise_for_status()
            geometries.update(_read_dwd_shapefile(await response.read()))
    return geometries


def filter_dwd_warnings(
    warnings: list[dict[str, Any]], *, latitude: float, longitude: float,
    elevation: float | None = None, location_name: str | None = None,
    geometries: dict[str, list[list[tuple[float, float]]]] | None = None,
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
        parsed_polygons = [_parse_polygon(warning.get("polygon"))]
        if not parsed_polygons[0] and geometries:
            shape = geometries.get(str(warning.get("region_id", "")))
            if shape:
                parsed_polygons = [ring for ring in shape if ring]
                item["geography_source"] = "dwd_official_warncell_shape"
        if any(parsed_polygons):
            if not any(_point_in_polygon(latitude, longitude, polygon) for polygon in parsed_polygons):
                continue
            item["location_relevance"] = "confirmed"
            item["location_relevance_reason"] = "Standort liegt innerhalb der gelieferten DWD-Geometrie."
        else:
            region_name = str(warning.get("regionName") or "").casefold()
            location_matches = bool(location_name and region_name and region_name in location_name.casefold())
            item["location_relevance"] = "possible" if location_matches else "unknown"
            item["location_relevance_reason"] = "Gebietsname passt zum aktiven Ortsnamen, aber ein Polygon fehlt." if location_matches else "Polygon oder belastbare Gebietszuordnung fehlt."
            item["location_uncertain"] = True
        if str(warning.get("region_id", "")).startswith(DWD_MARINE_AREA_PREFIX) and item["location_relevance"] != "confirmed":
            # A marine record is only relevant when an official polygon proves
            # that the active point is inside the marine area.
            continue
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
    await _enrich_dwd_cap_geometry(session, warnings)
    try:
        geometries = await async_dwd_warncell_geometries(session)
    except (AttributeError, ClientError, OSError, TimeoutError, ValueError, BadZipFile, StopIteration, struct.error):
        geometries = {}
    for warning in warnings:
        polygon = geometries.get(str(warning.get("region_id", "")))
        if polygon and not warning.get("polygon"):
            warning["polygon"] = " ".join(f"{lat},{lon}" for lat, lon in polygon[0])
            warning["geography_source"] = "dwd_official_warncell_shape"
    return warnings


async def _enrich_dwd_cap_geometry(session: ClientSession, warnings: list[dict[str, Any]]) -> None:
    """Attach official CAP polygons when the WarnWetter JSON omits them.

    The JSON endpoint is the compact status feed; the official DWD CAP
    district-cells product carries the corresponding geometries. Enrichment
    is best-effort so a CAP outage never turns a valid JSON response into an
    outage. Matching uses structured event, area name and onset fields.
    """
    try:
        async with session.get(DWD_CAP_INDEX_URL, timeout=10) as response:
            response.raise_for_status()
            index = await response.text()
        match = re.search(r'href="([^"]+LATEST[^"/]+_DE\.zip)"', index)
        if not match:
            return
        url = DWD_CAP_INDEX_URL + match.group(1)
        async with session.get(url, timeout=15) as response:
            response.raise_for_status()
            archive = await response.read()
        polygons: dict[tuple[str, str, int | None], str] = {}
        with ZipFile(BytesIO(archive)) as zipped:
            for filename in zipped.namelist():
                if not filename.endswith(".xml"):
                    continue
                root = ElementTree.fromstring(zipped.read(filename))
                info = next((node for node in root.iter() if node.tag.endswith("}info")), None)
                area = next((node for node in root.iter() if node.tag.endswith("}area")), None)
                if info is None or area is None:
                    continue
                value = lambda parent, name: next((node.text for node in parent.iter() if node.tag.endswith("}" + name) and node.text), None)
                event = value(info, "event")
                onset = value(info, "onset")
                area_name = value(area, "areaDesc")
                polygon = value(area, "polygon")
                if not event or not area_name or not polygon:
                    continue
                try:
                    onset_ms = int(datetime.fromisoformat(onset).timestamp() * 1000) if onset else None
                except (TypeError, ValueError):
                    onset_ms = None
                polygons[(event, area_name, onset_ms)] = polygon
        for warning in warnings:
            key = (str(warning.get("event") or ""), str(warning.get("regionName") or ""), warning.get("start"))
            polygon = polygons.get(key)
            if polygon:
                warning["polygon"] = polygon
                warning["geography_source"] = "dwd_cap"
    except (ClientError, OSError, TimeoutError, ValueError, TypeError, KeyError, BadZipFile, ElementTree.ParseError):
        return


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
