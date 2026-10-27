"""Provider-independent camping and activity calculations."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any


@dataclass(frozen=True)
class Hour:
    time: datetime
    temperature: float | None = None
    apparent_temperature: float | None = None
    precipitation: float | None = None
    precipitation_probability: float | None = None
    wind: float | None = None
    gusts: float | None = None
    uv: float | None = None
    snowfall: float | None = None
    weather_code: int | None = None
    thunderstorm_probability: float | None = None
    is_day: bool | None = None
    elevation: float | None = None


@dataclass(frozen=True)
class Risk:
    name: str
    severity: str
    score_penalty: int
    reason: str
    at: datetime | None = None


ACTIVITY_PROFILES: dict[str, dict[str, float | bool]] = {
    "walking": {"min_temp": 5, "max_temp": 28, "max_wind": 35, "max_rain": 1.5, "daylight": True},
    "hiking": {"min_temp": 8, "max_temp": 25, "max_wind": 30, "max_rain": 0.8, "daylight": True},
    "cycling": {"min_temp": 10, "max_temp": 28, "max_wind": 25, "max_rain": 0.5, "daylight": True},
    "ebike": {"min_temp": 8, "max_temp": 30, "max_wind": 30, "max_rain": 0.8, "daylight": True},
    "jogging": {"min_temp": 8, "max_temp": 24, "max_wind": 25, "max_rain": 0.5, "daylight": True},
    "skiing": {"min_temp": -12, "max_temp": 5, "max_wind": 45, "max_rain": 2, "daylight": True},
    "swimming": {"min_temp": 20, "max_temp": 34, "max_wind": 20, "max_rain": 0.2, "daylight": True, "water_data": False},
    "barbecue": {"min_temp": 16, "max_temp": 30, "max_wind": 25, "max_rain": 0.2, "daylight": True},
    "fishing": {"min_temp": 8, "max_temp": 28, "max_wind": 25, "max_rain": 0.8, "daylight": True},
    "outdoor": {"min_temp": 8, "max_temp": 30, "max_wind": 30, "max_rain": 1.0, "daylight": True},
}


def _missing(hour: Hour) -> bool:
    return hour.temperature is None or hour.wind is None


def risks_for_hour(hour: Hour, *, awning_wind: float = 38, frost_temp: float = 2) -> list[Risk]:
    risks: list[Risk] = []
    if hour.gusts is not None and hour.gusts >= awning_wind:
        risks.append(Risk("awning", "critical", 100, f"Böen {hour.gusts:.0f} km/h erreichen die Markisenschwelle", hour.time))
    if hour.wind is not None and hour.wind >= 50:
        risks.append(Risk("storm", "critical", 100, f"Starker Wind {hour.wind:.0f} km/h", hour.time))
    if hour.temperature is not None and hour.temperature <= frost_temp:
        risks.append(Risk("frost", "warning", 35, f"Temperatur {hour.temperature:.1f} °C liegt bei/unter Frostschwelle", hour.time))
    if (hour.precipitation_probability or 0) >= 70 and (hour.precipitation or 0) >= 5:
        risks.append(Risk("heavy_rain", "warning", 45, "Hohe Wahrscheinlichkeit für kräftigen Niederschlag", hour.time))
    if (hour.thunderstorm_probability or 0) >= 40 or hour.weather_code in {95, 96, 99}:
        risks.append(Risk("thunderstorm", "critical", 100, "Gewitterrisiko erkannt", hour.time))
    if hour.uv is not None and hour.uv >= 8:
        risks.append(Risk("uv", "warning", 15, f"Hoher UV-Index {hour.uv:.1f}", hour.time))
    return risks


def camping_score(hour: Hour, *, awning_wind: float = 38, frost_temp: float = 2) -> tuple[int | None, list[Risk]]:
    """Return a conservative 0-100 score; critical hazards always win."""
    if _missing(hour):
        return None, [Risk("data", "unknown", 0, "Temperatur oder Winddaten fehlen", hour.time)]
    risks = risks_for_hour(hour, awning_wind=awning_wind, frost_temp=frost_temp)
    if any(r.severity == "critical" for r in risks):
        return 0, risks
    score = 100
    score -= min(35, int(max(0, hour.wind or 0) * 0.8))
    score -= min(30, int(max(0, hour.precipitation_probability or 0) * 0.3))
    score -= sum(r.score_penalty for r in risks)
    if hour.temperature < 5 or hour.temperature > 30:
        score -= 15
    return max(0, min(100, score)), risks


def activity_score(hours: list[Hour], activity: str) -> tuple[int | None, list[Risk]]:
    """Assess a window; missing values stay unknown and critical risks cannot average away."""
    if not hours or any(_missing(hour) for hour in hours):
        return None, [Risk("data", "unknown", 0, "Für das Zeitfenster fehlen Wetterdaten")]
    profile = ACTIVITY_PROFILES.get(activity, ACTIVITY_PROFILES["outdoor"])
    values: list[int] = []
    risks: list[Risk] = []
    for hour in hours:
        score = 100
        temp = hour.apparent_temperature if hour.apparent_temperature is not None else hour.temperature
        if temp < profile["min_temp"]:
            score -= min(35, int(profile["min_temp"] - temp) * 4)
        if temp > profile["max_temp"]:
            score -= min(35, int(temp - profile["max_temp"]) * 4)
        if hour.wind and hour.wind > profile["max_wind"]:
            score -= min(40, int(hour.wind - profile["max_wind"]))
        if hour.precipitation and hour.precipitation > profile["max_rain"]:
            score -= 30
        if profile.get("daylight") and hour.is_day is False:
            score -= 50
            risks.append(Risk("daylight", "warning", 50, "Dieses Zeitfenster liegt ganz oder teilweise im Dunkeln", hour.time))
        elif profile.get("daylight") and hour.is_day is None:
            score -= 15
            risks.append(Risk("daylight_data", "unknown", 15, "Tageslichtdaten fehlen; Bewertung ist unsicher", hour.time))
        values.append(max(0, score))
        risks.extend(risks_for_hour(hour))
    if any(r.severity == "critical" for r in risks):
        return 0, risks
    result = max(0, min(100, round(sum(values) / len(values))))
    if activity == "swimming":
        risks.append(Risk("water_data", "unknown", 0, "Keine Wassertemperatur-, Wasserqualitäts- oder Gewässerdaten; nur Wettertauglichkeit bewertet"))
        result = min(result, 50)
    if activity == "skiing":
        risks.append(Risk("winter_data", "unknown", 0, "Keine Schneehöhen- oder Lawinendaten; keine vollständige Skitauglichkeit bestätigt"))
        result = min(result, 45)
    return result, risks


def apply_official_warning_risks(score: int | None, warnings: list[dict[str, Any]]) -> tuple[int | None, list[Risk]]:
    """Fold active official warnings into the camping score conservatively."""
    if score is None:
        return None, []
    risks: list[Risk] = []
    result = score
    seen: set[tuple[Any, ...]] = set()
    for warning in warnings:
        warning_key = (warning.get("warning_id"), warning.get("identifier"), warning.get("event"), warning.get("start"), warning.get("end"), warning.get("region_id"), warning.get("regionName"), warning.get("level"))
        if warning_key in seen:
            continue
        seen.add(warning_key)
        relevance = warning.get("location_relevance")
        confirmed = relevance in (None, "confirmed")
        try:
            level = int(warning.get("level", 0))
        except (TypeError, ValueError):
            level = 0
        event = str(warning.get("summary") or warning.get("event") or warning.get("headline") or "Amtliche Wetterwarnung")
        if not confirmed:
            risks.append(Risk("warning_scope", "unknown", 0, f"DWD-Warnung Stufe {level} ist {relevance or 'räumlich unbestimmt'}; keine bestätigte lokale Zuordnung.", None))
            continue
        if level >= 3:
            risks.append(Risk("official_warning", "critical", 100, f"Amtliche DWD-Warnung Stufe {level}: {event}"))
            result = 0
        elif level >= 2:
            risks.append(Risk("official_warning", "warning", 45, f"Amtliche DWD-Warnung Stufe {level}: {event}"))
            result = min(result, 55)
        elif level >= 1:
            risks.append(Risk("official_warning", "warning", 20, f"Amtliche DWD-Warnung Stufe {level}: {event}"))
            result = min(result, 80)
        if warning.get("altitude_uncertain") or warning.get("location_uncertain"):
            risks.append(Risk("warning_scope", "unknown", 0, "Genaue geografische oder höhenbezogene Gültigkeit der DWD-Warnung ist unbekannt"))
    return result, risks


def assess_activity_window(hours: list[Hour], activity: str, start: datetime, duration_minutes: int) -> tuple[int | None, list[Risk]]:
    """Assess every forecast hour covered by a planned activity.

    A missing edge hour is unknown instead of silently producing an optimistic score.
    """
    if duration_minutes <= 0:
        return None, [Risk("data", "unknown", 0, "Die Dauer muss größer als null sein")]
    end = start + timedelta(minutes=duration_minutes)
    selected = [hour for hour in hours if start <= hour.time < end]
    required = max(1, (duration_minutes + 59) // 60)
    if len(selected) < required:
        return None, [Risk("data", "unknown", 0, "Für den gesamten geplanten Zeitraum fehlen Prognosedaten")]
    return activity_score(selected, activity)


def suggest_activity_windows(
    hours: list[Hour], activity: str, duration_minutes: int = 120, limit: int = 3,
    reference_time: datetime | None = None, warnings: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Return deterministic, separated future windows from the next 48 hours."""
    if duration_minutes <= 0:
        return []
    reference_time = reference_time or datetime.now(UTC)
    horizon = reference_time + timedelta(hours=48)
    candidates: list[dict[str, Any]] = []
    for hour in hours:
        if hour.time < reference_time or hour.time >= horizon:
            continue
        score, risks = assess_activity_window(hours, activity, hour.time, duration_minutes)
        if score is None or any(r.severity == "critical" for r in risks):
            continue
        if warnings:
            score, official_risks = apply_official_warning_risks(score, warnings)
            risks = [*risks, *official_risks]
            if any(risk.severity == "critical" for risk in official_risks):
                continue
        selected = [row for row in hours if hour.time <= row.time < hour.time + timedelta(minutes=duration_minutes)]
        first = selected[0] if selected else hour
        critical = any(risk.severity == "critical" for risk in risks)
        uncertain = any(risk.severity == "unknown" for risk in risks)
        warning = any(risk.severity == "warning" for risk in risks)
        candidates.append({
            "start": hour.time.isoformat(), "duration_minutes": duration_minutes, "score": score,
            "temperature": first.temperature, "wind": first.wind, "gusts": first.gusts,
            "precipitation_probability": first.precipitation_probability, "weather_code": first.weather_code,
            "is_day": first.is_day, "safety_status": "red" if critical else "orange" if warning else "yellow" if uncertain else "green",
            "summary": f"{first.temperature:.0f} °C, Wind {first.wind:.0f} km/h" if first.temperature is not None and first.wind is not None else "Wetterdaten teilweise unbekannt",
            "risks": [risk.__dict__ for risk in risks],
        })
    candidates.sort(key=lambda item: (-int(item["score"] if item["score"] is not None else -1), item["start"]))
    selected: list[dict[str, Any]] = []
    separation = timedelta(minutes=max(duration_minutes, 180))
    for candidate in candidates:
        start = datetime.fromisoformat(candidate["start"])
        if all(abs(start - datetime.fromisoformat(item["start"])) >= separation for item in selected):
            selected.append(candidate)
            if len(selected) >= limit:
                break
    return sorted(selected, key=lambda item: item["start"])


def normalize_open_meteo(payload: dict[str, Any]) -> tuple[Hour, ...]:
    hourly = payload.get("hourly") or {}
    times = hourly.get("time") or []
    fields = {key: hourly.get(key) or [] for key in (
        "temperature_2m", "apparent_temperature", "precipitation", "precipitation_probability",
        "wind_speed_10m", "wind_gusts_10m", "uv_index", "snowfall", "weather_code",
        "thunderstorm_probability", "is_day",
    )}
    result: list[Hour] = []
    for index, raw_time in enumerate(times):
        try:
            timestamp = datetime.fromisoformat(str(raw_time))
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=UTC)
        except ValueError:
            continue
        values = [
            field_values[index] if index < len(field_values) else None
            for field_values in fields.values()
        ]
        values[-1] = bool(values[-1]) if values[-1] is not None else None
        result.append(Hour(timestamp, *values, elevation=payload.get("elevation")))
    return tuple(result)
