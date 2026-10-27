import asyncio

import pytest

from custom_components.camper_weather.core import Hour
from custom_components.camper_weather.providers import async_dwd_warnings, async_met_norway, deduplicate_dwd_warnings, filter_dwd_warnings


class FakeResponse:
    def __init__(self, body):
        self.body = body

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    def raise_for_status(self):
        return None

    async def text(self):
        return self.body


class FakeSession:
    def __init__(self, body):
        self.body = body

    def get(self, *args, **kwargs):
        return FakeResponse(self.body)


def test_provider_module_exports_adapter():
    assert callable(async_met_norway)
    assert Hour.__name__ == "Hour"


def test_dwd_jsonp_is_normalized_to_warning_records():
    body = 'warnWetter.loadWarnings({"time": 1, "warnings": {"901": [{"level": 2, "regionName": "Testkreis"}]}});'
    warnings = asyncio.run(async_dwd_warnings(FakeSession(body)))
    assert warnings == [{"level": 2, "regionName": "Testkreis", "region_id": "901"}]


def test_dwd_empty_warning_groups_are_a_valid_empty_result():
    body = 'warnWetter.loadWarnings({"time": 1, "warnings": {}});'
    assert asyncio.run(async_dwd_warnings(FakeSession(body))) == []


def test_dwd_invalid_payload_is_not_reported_as_no_warnings():
    with pytest.raises((TypeError, ValueError)):
        asyncio.run(async_dwd_warnings(FakeSession("{}")))


def test_dwd_filter_removes_expired_and_low_altitude_warnings():
    warnings = [
        {"level": 3, "event": "STURM", "regionName": "Bergland", "start": 0, "end": 4102444800000, "altitudeStart": 1000},
        {"level": 2, "event": "WIND", "regionName": "Bergland", "start": 0, "end": 4102444800000},
    ]
    result = filter_dwd_warnings(warnings, latitude=51.0, longitude=10.0, elevation=100)
    assert len(result) == 1
    assert result[0]["altitude_uncertain"] is False


def test_dwd_filter_marks_district_only_scope_as_uncertain():
    result = filter_dwd_warnings([{"level": 2, "event": "WIND", "regionName": "Kreis Beispiel"}], latitude=51.0, longitude=10.0)
    assert result[0]["location_uncertain"] is True


def test_dwd_dedup_keeps_periods_and_areas_separate():
    base = {"warningId": "abc", "event": "Wind", "start": 100, "end": 200, "region_id": "1", "regionName": "Nord", "level": 2}
    result = deduplicate_dwd_warnings([base, {**base, "description": "gleich"}, {**base, "end": 300}, {**base, "region_id": "2", "regionName": "Süd"}])
    assert len(result) == 3
    assert all(item["summary"] == "Wind" for item in result)


def test_dwd_filter_sorting_and_summary_are_stable():
    result = filter_dwd_warnings([
        {"level": 1, "event": "Regen", "regionName": "Kreis", "start": 0, "end": 4102444800000},
        {"level": 3, "event": "Sturm", "regionName": "Kreis", "start": 0, "end": 4102444800000},
        {"level": 3, "event": "Sturm", "regionName": "Kreis", "start": 0, "end": 4102444800000},
    ], latitude=51.0, longitude=10.0)
    assert [item["level"] for item in result] == [3, 1]
    assert result[0]["summary"] == "Sturm"


def test_dwd_marine_area_is_not_a_local_camping_warning_for_saarland():
    result = filter_dwd_warnings([
        {"region_id": "501000005", "level": 2, "event": "STARKWIND", "headline": "Amtliche Warnung des Seewetterdienstes Hamburg", "start": 0},
        {"region_id": "100441000", "level": 2, "event": "WINDBÖEN", "regionName": "Saarland", "start": 0, "end": 4102444800000},
    ], latitude=49.3, longitude=6.9)
    assert len(result) == 1
    assert result[0]["region_id"] == "100441000"


def test_dwd_marine_area_is_not_filtered_by_headline_text():
    result = filter_dwd_warnings([
        {"region_id": "501000008", "level": 2, "event": "BÖEN", "headline": "BÖEN", "start": 0},
    ], latitude=54.5, longitude=9.5)
    assert result == []


def test_dwd_district_scope_is_explicitly_possible_or_unknown_not_confirmed():
    result = filter_dwd_warnings([{"region_id": "100", "level": 2, "event": "WIND", "regionName": "Saarland", "start": 0}], latitude=49.3, longitude=6.9, location_name="Saarland")
    assert result[0]["location_relevance"] == "possible"
    assert result[0]["location_relevance_reason"]


def test_dwd_marine_polygon_can_confirm_a_coastal_location():
    result = filter_dwd_warnings([{"region_id": "501000008", "level": 2, "event": "BÖEN", "start": 0, "polygon": "54.0,9.0 55.0,9.0 55.0,10.0 54.0,10.0"}], latitude=54.5, longitude=9.5)
    assert result[0]["location_relevance"] == "confirmed"


def test_official_warncell_geometry_excludes_remote_helgoland_and_aurich():
    geometries = {
        "501000002": [[(54.1, 7.8), (54.1, 8.0), (54.0, 8.0), (54.0, 7.8)]],
        "903452002": [[(53.4, 7.2), (53.4, 7.8), (53.0, 7.8), (53.0, 7.2)]],
    }
    warnings = [
        {"region_id": "501000002", "regionName": "Helgoland", "level": 2, "event": "WIND", "start": 0, "end": 4102444800000},
        {"region_id": "903452002", "regionName": "Kreis Aurich - Küste", "level": 2, "event": "WIND", "start": 0, "end": 4102444800000},
    ]
    assert filter_dwd_warnings(warnings, latitude=49.3, longitude=7.05, geometries=geometries) == []


def test_missing_official_geometry_remains_unknown_not_confirmed():
    result = filter_dwd_warnings([{"region_id": "903452002", "regionName": "Kreis Aurich - Küste", "level": 2, "event": "WIND", "start": 0, "end": 4102444800000}], latitude=49.3, longitude=7.05)
    assert result[0]["location_relevance"] == "unknown"


def test_official_multipolygon_confirms_when_point_is_in_any_part():
    geometries = {"100": [
        [(50.0, 6.0), (50.0, 6.1), (49.9, 6.1), (49.9, 6.0)],
        [(49.3, 7.0), (49.3, 7.1), (49.2, 7.1), (49.2, 7.0)],
    ]}
    result = filter_dwd_warnings([{"region_id": "100", "level": 2, "event": "WIND", "start": 0, "end": 4102444800000}], latitude=49.25, longitude=7.05, geometries=geometries)
    assert result[0]["location_relevance"] == "confirmed"
