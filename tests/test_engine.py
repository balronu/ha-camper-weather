from datetime import UTC, datetime, timedelta

from custom_components.camper_weather.core import Hour
from custom_components.camper_weather.engine import (
    DataQuality,
    LocationContext,
    WarningIdentity,
    comfort_assessment,
    detect_trends,
    evaluate_window,
    safety_assessment,
)
from custom_components.camper_weather.warning_state import WarningStateTracker


def hour(at: datetime, **values: object) -> Hour:
    defaults = {"temperature": 20, "wind": 10, "gusts": 12, "precipitation": 0, "precipitation_probability": 0}
    defaults.update(values)
    return Hour(at, **defaults)


def quality() -> DataQuality:
    return DataQuality("good", "ok", datetime.now(UTC), 0, True, ("open_meteo",))


def location() -> LocationContext:
    return LocationContext("tracker", "device_tracker.camper", "Camper", 49.3, 6.9, "Europe/Berlin", 200)


def test_critical_wind_is_red_even_with_good_comfort() -> None:
    current = hour(datetime.now(UTC), gusts=60)
    assert comfort_assessment(current).score == 0
    assessment = safety_assessment(current, [], data_quality=quality())
    assert assessment.status == "red"
    assert assessment.reasons


def test_missing_data_is_gray() -> None:
    assessment = safety_assessment(hour(datetime.now(UTC), temperature=None), [], data_quality=quality())
    assert assessment.status == "gray"


def test_warning_identity_is_stable_and_area_specific() -> None:
    warning = {"warningId": "a", "region_id": "1", "start": 1, "end": 2, "level": 2}
    assert WarningIdentity.from_warning(warning).key() == WarningIdentity.from_warning(dict(warning)).key()
    assert WarningIdentity.from_warning({**warning, "region_id": "2"}).key() != WarningIdentity.from_warning(warning).key()


def test_trends_only_report_supported_changes() -> None:
    start = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    trends = detect_trends([hour(start, wind=10), hour(start + timedelta(hours=1), wind=12), hour(start + timedelta(hours=2), wind=25)], now=start)
    assert any(trend.kind == "wind" and trend.direction == "increasing" for trend in trends)


def test_window_outside_horizon_is_incomplete() -> None:
    start = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    assessment = evaluate_window([hour(start)], [], "walking", start, 120, location=location(), quality=quality())
    assert assessment.score is None
    assert assessment.complete is False
    assert assessment.quality.status == "partial"


def test_warning_state_deduplicates_changes_and_does_not_end_on_outage() -> None:
    tracker = object.__new__(WarningStateTracker)
    tracker._active = {}
    tracker._loaded = True
    tracker._save = lambda: None
    warning = {"warningId": "wind-1", "region_id": "land", "event": "Wind", "level": 2}
    assert [event.phase for event in tracker.update([warning], available=True)] == ["started"]
    assert tracker.update([warning], available=True) == []
    assert tracker.update([], available=False) == []
    assert [event.phase for event in tracker.update([], available=True)] == ["ended"]
