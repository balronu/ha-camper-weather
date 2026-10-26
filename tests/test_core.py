from datetime import UTC, datetime

from custom_components.camper_weather.core import (
    Hour,
    activity_score,
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
    assert not risks
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
    recommendations = suggest_activity_windows(hours, "cycling", duration_minutes=120)
    assert recommendations[0]["start"] == start.isoformat()
    assert recommendations[0]["score"] >= 0
