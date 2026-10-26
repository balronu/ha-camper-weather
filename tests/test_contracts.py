from pathlib import Path

from custom_components.camper_weather.const import CARD_VERSION, RAINVIEWER_URL, VERSION


def test_backend_and_card_versions_match():
    card = Path("custom_components/camper_weather/www/camper-weather-card.js").read_text()
    assert VERSION == CARD_VERSION == "0.1.0-beta.5"
    assert f'const VERSION = "{VERSION}"' in card
    assert "tile.openstreetmap.org" not in card
    assert "openfreemap.org/styles/liberty" in card
    assert "maplibre-gl@5.6.2" in card
    assert "rainviewer.com" in card
    assert "camper_weather/planner/save" in card
    assert "camper_weather/location/geocode" in card
    assert "ResizeObserver" in card
    assert "weather-glyph" in card


def test_radar_provider_contract_has_frames_and_attribution():
    provider = Path("custom_components/camper_weather/providers.py").read_text()
    assert '"frames"' in provider
    assert "tile_template" in provider
    assert RAINVIEWER_URL == "https://api.rainviewer.com/public/weather-maps.json"
