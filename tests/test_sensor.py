from unittest.mock import patch, MagicMock
from homeassistant.const import CONF_EMAIL, CONF_TIMEZONE
from custom_components.pw3 import sensor


async def test_sensor_setup(hass, mock_powerwall, mock_config_entry):
    """Test sensor setup."""
    mock_coordinator = MagicMock()
    mock_coordinator.data = {
        "solar": 1.5,
        "battery": 2.0,
        "home": 3.5,
        "grid": -1.0,
        "percentage": 75.5,
        "last_updated": "2023-05-01T12:00:00Z",
    }

    with patch(
        "custom_components.pw3.sensor.Pw3DataUpdateCoordinator",
        return_value=mock_coordinator,
    ):
        await sensor.async_setup_entry(hass, mock_config_entry, MagicMock())

    assert len(hass.states.async_all()) == 5

    solar_state = hass.states.get("sensor.powerwall_solar_power")
    assert solar_state.state == "1.5"
    assert solar_state.attributes["unit_of_measurement"] == "kW"

    battery_state = hass.states.get("sensor.powerwall_battery_percentage")
    assert battery_state.state == "75.5"
    assert battery_state.attributes["unit_of_measurement"] == "%"
