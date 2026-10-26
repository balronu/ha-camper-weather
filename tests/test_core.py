from datetime import UTC, datetime

from custom_components.camper_weather.core import (
    Hour,
    activity_score,
    apply_official_warning_risks,
    assess_activity_window,
    camping_score,
    normalize_open_meteo,
    risks_for_hour,
    suggest_activity_windows,
)


def hour(**kwargs):
    values = {"temperature": 20, "wind": 10}
    timestamp = kwargs.pop("time", datetime(2026, 10, 26, 10, tzinfo=UTC))
    values.update(kwargs)
    return Hour(timestamp, **values)


def test_missing_data_is_unknown_not_good():
    score, risks = camping_score(hour(temperature=None))
    assert score is None
    assert risks[0].name == "data"


def test_critical_gust_cannot_be_averaged_away():
    score, risks = camping_score(hour(gusts=45))
    assert score == 0
    assert any(r.name == "awning" for r in risks)


def test_activity_score_and_critical_risk():
    score, _ = activity_score([hour(), hour()], "cycling")
    assert score >= 0
    score, _ = activity_score([hour(gusts=60)], "cycling")
    assert score == 0


def test_open_meteo_normalization():
    result = normalize_open_meteo({"hourly": {"time": ["2026-10-26T10:00:00Z"], "temperature_2m": [20], "wind_speed_10m": [10]}})
    assert len(result) == 1
    assert result[0].temperature == 20


def test_warning_thresholds():
    assert any(r.name == "frost" for r in risks_for_hour(hour(temperature=1)))


def test_planner_requires_complete_window_and_scores_complete_window():
    start = datetime(2026, 10, 26, 10, tzinfo=UTC)
    score, risks = assess_activity_window([hour(time=start), hour(time=start.replace(hour=11))], "cycling", start, 120)
    assert score is not None
    assert all(risk.name != "official_warning" for risk in risks)
    score, risks = assess_activity_window([hour(time=start)], "cycling", start, 120)
    assert score is None
    assert risks[0].name == "data"


def test_recommendations_exclude_critical_weather():
    start = datetime(2026, 10, 26, 10, tzinfo=UTC)
    hours = [hour(time=start, gusts=60), hour(time=start.replace(hour=11), gusts=60)]
    assert suggest_activity_windows(hours, "cycling") == []


def test_recommendations_return_reproducible_good_window():
    start = datetime(2026, 10, 26, 10, tzinfo=UTC)
    hours = [hour(time=start, gusts=10), hour(time=start.replace(hour=11), gusts=10)]
    recommendations = suggest_activity_windows(hours, "cycling", duration_minutes=120, reference_time=start)
    assert recommendations[0]["start"] == start.isoformat()
    assert recommendations[0]["score"] >= 0


def test_recommendations_skip_past_windows():
    start = datetime(2026, 10, 26, 10, tzinfo=UTC)
    hours = [hour(time=start), hour(time=start.replace(hour=11)), hour(time=start.replace(hour=12))]
    assert suggest_activity_windows(hours, "cycling", reference_time=start.replace(hour=11))
    assert all(item["start"] >= start.replace(hour=11).isoformat() for item in suggest_activity_windows(hours, "cycling", reference_time=start.replace(hour=11)))


def test_night_activity_is_not_perfect_without_daylight():
    score, risks = activity_score([hour(is_day=False), hour(is_day=False)], "walking")
    assert score < 100
    assert any(risk.name == "daylight" for risk in risks)


def test_swimming_and_skiing_are_limited_without_specialist_data():
    swimming, swimming_risks = activity_score([hour(is_day=True)], "swimming")
    skiing, skiing_risks = activity_score([hour(temperature=-2, is_day=True)], "skiing")
    assert swimming <= 50 and any(risk.name == "water_data" for risk in swimming_risks)
    assert skiing <= 45 and any(risk.name == "winter_data" for risk in skiing_risks)


def test_critical_official_warning_overrides_comfort_score():
    score, risks = apply_official_warning_risks(91, [{"level": 3, "event": "STURM"}])
    assert score == 0
    assert risks[0].severity == "critical"
