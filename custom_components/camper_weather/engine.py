"""Shared, provider-independent weather assessments for Camper Weather.

The coordinator owns fetching and normalising provider data.  This module owns
the small immutable result objects consumed by sensors, the API, the planner,
and the Lovelace card.  It deliberately contains no Home Assistant imports so
the safety and window logic can be tested offline.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from .core import Hour, Risk, assess_activity_window, camping_score, risks_for_hour


@dataclass(frozen=True)
class LocationContext:
    mode: str
    reference: str | None
    name: str | None
    latitude: float | None
    longitude: float | None
    timezone: str
    elevation: float | None
    stale: bool = False


@dataclass(frozen=True)
class DataQuality:
    status: str
    reason: str
    updated_at: datetime | None = None
    age_seconds: int | None = None
    forecast_complete: bool = True
    sources: tuple[str, ...] = ()


@dataclass(frozen=True)
class SafetyAssessment:
    status: str
    level: int
    reasons: tuple[str, ...] = ()
    next_risk: str | None = None


@dataclass(frozen=True)
class ComfortAssessment:
    score: int | None
    label: str
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class WeatherTrend:
    kind: str
    direction: str
    at: datetime | None
    reason: str
    confidence: str = "medium"


@dataclass(frozen=True)
class WindowAssessment:
    start: datetime
    end: datetime
    activity: str
    location: LocationContext
    score: int | None
    safety: SafetyAssessment
    quality: DataQuality
    reasons: tuple[str, ...] = ()
    complete: bool = True


@dataclass(frozen=True)
class WarningIdentity:
    """Stable identity for one warning/area/period, independent of text."""

    identifier: str
    area: str
    start: str | None
    end: str | None
    level: int

    @classmethod
    def from_warning(cls, warning: dict[str, Any]) -> WarningIdentity:
        identifier = next((warning.get(key) for key in ("warningId", "warning_id", "identifier", "id") if warning.get(key)), None)
        if identifier is None:
            identifier = "|".join(str(warning.get(key) or "") for key in ("event", "headline", "region_id", "regionName"))
        try:
            level = int(warning.get("level", 0))
        except (TypeError, ValueError):
            level = 0
        return cls(str(identifier), str(warning.get("region_id") or warning.get("regionName") or "unknown"),
                   _text_time(warning.get("start")), _text_time(warning.get("end")), level)

    def key(self) -> str:
        return "|".join((self.identifier, self.area, self.start or "", self.end or ""))


@dataclass(frozen=True)
class WarningState:
    identity: WarningIdentity
    phase: str
    level: int
    event: str
    source: str
    observed_at: datetime
    quality: str


@dataclass(frozen=True)
class WeatherSnapshot:
    location: LocationContext
    current: Hour | None
    hours: tuple[Hour, ...]
    comfort: ComfortAssessment
    safety: SafetyAssessment
    quality: DataQuality
    trends: tuple[WeatherTrend, ...] = ()
    warnings: tuple[dict[str, Any], ...] = ()
    summary: str = ""
    summary_en: str = ""


def _text_time(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _risk_reason(risk: Risk) -> str:
    return risk.reason


def safety_assessment(current: Hour | None, warnings: Iterable[dict[str, Any]], *, data_quality: DataQuality) -> SafetyAssessment:
    if current is None or current.temperature is None or current.wind is None or data_quality.status in {"unavailable", "unknown", "stale", "partial"}:
        return SafetyAssessment("gray", 0, ("Sicherheitsrelevante Wetterdaten sind nicht vollständig verfügbar.",))
    risks = risks_for_hour(current)
    reasons = [_risk_reason(risk) for risk in risks]
    highest_warning = 0
    for warning in warnings:
        try:
            highest_warning = max(highest_warning, int(warning.get("level", 0)))
        except (TypeError, ValueError):
            continue
        if warning.get("location_uncertain") or warning.get("altitude_uncertain"):
            reasons.append("Die räumliche oder höhenbezogene Gültigkeit einer amtlichen Warnung ist teilweise unklar.")
        reasons.append(str(warning.get("summary") or warning.get("event") or "Amtliche Wetterwarnung"))
    critical = any(risk.severity == "critical" for risk in risks) or highest_warning >= 3
    elevated = highest_warning >= 2 or any(risk.severity == "warning" for risk in risks)
    if critical:
        status, level = "red", 3
    elif elevated:
        status, level = ("orange", 2) if highest_warning >= 2 or any(risk.name in {"heavy_rain", "frost"} for risk in risks) else ("yellow", 1)
    else:
        status, level = "green", 0
    return SafetyAssessment(status, level, tuple(dict.fromkeys(reasons)), reasons[0] if reasons else None)


def comfort_assessment(current: Hour | None, *, awning_wind: float = 38, frost_temp: float = 2) -> ComfortAssessment:
    if current is None:
        return ComfortAssessment(None, "unknown", ("Temperatur- oder Winddaten fehlen.",))
    score, risks = camping_score(current, awning_wind=awning_wind, frost_temp=frost_temp)
    if score is None:
        return ComfortAssessment(None, "unknown", tuple(_risk_reason(risk) for risk in risks))
    label = "sehr gut" if score >= 85 else "gut" if score >= 70 else "eingeschränkt" if score >= 40 else "schlecht"
    return ComfortAssessment(score, label, tuple(dict.fromkeys(_risk_reason(risk) for risk in risks)))


def detect_trends(hours: Iterable[Hour], *, now: datetime | None = None) -> tuple[WeatherTrend, ...]:
    rows = [hour for hour in hours if hour.time is not None]
    if len(rows) < 2:
        return ()
    now = now or datetime.now(UTC)
    future = [hour for hour in rows if hour.time >= now] or rows
    baseline, later = future[0], future[min(2, len(future) - 1)]
    trends: list[WeatherTrend] = []
    if baseline.wind is not None and later.wind is not None and later.wind - baseline.wind >= 10:
        trends.append(WeatherTrend("wind", "increasing", later.time, f"Wind nimmt voraussichtlich von {baseline.wind:.0f} auf {later.wind:.0f} km/h zu."))
    elif baseline.wind is not None and later.wind is not None and baseline.wind - later.wind >= 10:
        trends.append(WeatherTrend("wind", "decreasing", later.time, f"Wind lässt voraussichtlich von {baseline.wind:.0f} auf {later.wind:.0f} km/h nach."))
    rain_before = sum((hour.precipitation or 0) for hour in future[:2])
    rain_after = sum((hour.precipitation or 0) for hour in future[2:4])
    if rain_before < 0.2 and rain_after >= 1:
        trends.append(WeatherTrend("rain", "starting", future[min(2, len(future) - 1)].time, "Niederschlag setzt voraussichtlich ein."))
    elif rain_before >= 1 and rain_after < 0.2:
        trends.append(WeatherTrend("rain", "ending", future[min(2, len(future) - 1)].time, "Niederschlag lässt voraussichtlich nach."))
    if baseline.temperature is not None and later.temperature is not None and later.temperature - baseline.temperature <= -5:
        trends.append(WeatherTrend("temperature", "falling", later.time, f"Temperatur fällt voraussichtlich um {baseline.temperature - later.temperature:.0f} °C."))
    return tuple(trends)


def build_summary(snapshot: WeatherSnapshot, language: str = "de") -> str:
    if snapshot.current is None:
        return "Wetterdaten sind derzeit nicht ausreichend verfügbar." if language == "de" else "Weather data is currently insufficient."
    current = snapshot.current
    rain = "trocken" if (current.precipitation or 0) < 0.2 else "nass"
    wind = f"Wind {current.wind:.0f} km/h" if current.wind is not None else "Winddaten fehlen"
    trend = snapshot.trends[0].reason if snapshot.trends else ""
    if language == "de":
        parts = [f"Aktuell {current.temperature:.0f} °C und {rain}; {wind}.", trend, snapshot.safety.reasons[0] if snapshot.safety.reasons else "Keine besonderen Sicherheitsrisiken erkannt."]
    else:
        parts = [f"Currently {current.temperature:.0f} °C and {rain}; {wind}.", trend, "No specific safety risks detected." if not snapshot.safety.reasons else snapshot.safety.reasons[0]]
    return " ".join(part for part in parts if part).strip()


def evaluate_window(hours: Iterable[Hour], warnings: Iterable[dict[str, Any]], activity: str, start: datetime, duration_minutes: int, *, location: LocationContext, quality: DataQuality) -> WindowAssessment:
    end = start + timedelta(minutes=duration_minutes)
    rows = list(hours)
    warning_rows = list(warnings)
    score, risks = assess_activity_window(rows, activity, start, duration_minutes)
    selected = [hour for hour in rows if start <= hour.time < end]
    current = selected[0] if selected else None
    safety = safety_assessment(current, warning_rows, data_quality=quality)
    reasons = tuple(dict.fromkeys([risk.reason for risk in risks] + list(safety.reasons)))
    complete = score is not None and quality.forecast_complete
    if not complete:
        quality = DataQuality("partial", "Das Zeitfenster liegt teilweise außerhalb des verfügbaren Prognosehorizonts.", quality.updated_at, quality.age_seconds, False, quality.sources)
    return WindowAssessment(start, end, activity, location, score, safety, quality, reasons, complete)


def serialise(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "__dataclass_fields__"):
        return {key: serialise(item) for key, item in asdict(value).items()}
    if isinstance(value, tuple):
        return [serialise(item) for item in value]
    if isinstance(value, list):
        return [serialise(item) for item in value]
    if isinstance(value, dict):
        return {key: serialise(item) for key, item in value.items()}
    return value
