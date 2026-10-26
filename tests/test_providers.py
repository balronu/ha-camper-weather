import asyncio

import pytest

from custom_components.camper_weather.core import Hour
from custom_components.camper_weather.providers import async_dwd_warnings, async_met_norway, filter_dwd_warnings


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
