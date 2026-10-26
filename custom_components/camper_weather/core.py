"""Provider-independent camping and activity calculations."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
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


@dataclass(frozen=True)
class Risk:
    name: str
    severity: str
    score_penalty: int
    reason: str
    at: datetime | None = None


ACTIVITY_PROFILES: dict[str, dict[str, float]] = {
    "walking": {"min_temp": 5, "max_temp": 28, "max_wind": 35, "max_rain": 1.5},
    "hiking": {"min_temp": 8, "max_temp": 25, "max_wind": 30, "max_rain": 0.8},
    "cycling": {"min_temp": 10, "max_temp": 28, "max_wind": 25, "max_rain": 0.5},
    "ebike": {"min_temp": 8, "max_temp": 30, "max_wind": 30, "max_rain": 0.8},
    "jogging": {"min_temp": 8, "max_temp": 24, "max_wind": 25, "max_rain": 0.5},
    "skiing": {"min_temp": -12, "max_temp": 5, "max_wind": 45, "max_rain": 2},
    "swimming": {"min_temp": 20, "max_temp": 34, "max_wind": 20, "max_rain": 0.2},
    "barbecue": {"min_temp": 16, "max_temp": 30, "max_wind": 25, "max_rain": 0.2},
    "fishing": {"min_temp": 8, "max_temp": 28, "max_wind": 25, "max_rain": 0.8},
    "outdoor": {"min_temp": 8, "max_temp": 30, "max_wind": 30, "max_rain": 1.0},
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
        values.append(max(0, score))
        risks.extend(risks_for_hour(hour))
    if any(r.severity == "critical" for r in risks):
        return 0, risks
    return max(0, min(100, round(sum(values) / len(values)))), risks


def normalize_open_meteo(payload: dict[str, Any]) -> tuple[Hour, ...]:
    hourly = payload.get("hourly") or {}
    times = hourly.get("time") or []
    fields = {key: hourly.get(key) or [] for key in (
        "temperature_2m", "apparent_temperature", "precipitation", "precipitation_probability",
        "wind_speed_10m", "wind_gusts_10m", "uv_index", "snowfall", "weather_code",
        "thunderstorm_probability",
    )}
    result: list[Hour] = []
    for index, raw_time in enumerate(times):
        try:
            timestamp = datetime.fromisoformat(str(raw_time))
        except ValueError:
            continue
        values = tuple(
            field_values[index] if index < len(field_values) else None
            for field_values in fields.values()
        )
        result.append(Hour(timestamp, *values))
    return tuple(result)
