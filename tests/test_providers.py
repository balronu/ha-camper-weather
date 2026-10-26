import asyncio

import pytest

from custom_components.camper_weather.core import Hour
from custom_components.camper_weather.providers import async_dwd_warnings, async_met_norway


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
    with pytest.raises(ValueError):
        asyncio.run(async_dwd_warnings(FakeSession("{}")))
