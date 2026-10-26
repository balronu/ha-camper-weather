import asyncio

from homeassistant.core import HomeAssistant

from custom_components.camper_weather.api import async_setup_websocket


def test_websocket_handlers_register_literal_commands(tmp_path):
    async def run() -> None:
        hass = HomeAssistant(str(tmp_path))
        await async_setup_websocket(hass)
        handlers = hass.data["websocket_api"]
        expected = {
            "camper_weather/card_data",
            "camper_weather/list_entries",
            "camper_weather/planner/list",
            "camper_weather/planner/save",
            "camper_weather/planner/delete",
            "camper_weather/planner/assess",
            "camper_weather/location/get",
            "camper_weather/location/set",
            "camper_weather/location/geocode",
            "camper_weather/location/save_destination",
            "camper_weather/location/delete_destination",
        }
        assert expected <= handlers.keys()
        assert all(command.startswith("camper_weather/") for command in expected)
        await hass.async_stop()

    asyncio.run(run())
