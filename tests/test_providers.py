from custom_components.camper_weather.core import Hour
from custom_components.camper_weather.providers import async_met_norway


def test_provider_module_exports_adapter():
    assert callable(async_met_norway)
    assert Hour.__name__ == "Hour"

