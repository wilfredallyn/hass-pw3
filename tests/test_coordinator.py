import pytest
from custom_components.pw3.coordinator import Pw3DataUpdateCoordinator
from homeassistant.helpers.update_coordinator import UpdateFailed


async def test_coordinator_update(hass, mock_powerwall):
    """Test coordinator update."""
    mock_powerwall.solar.return_value = {
        "last_communication_time": "2023-05-01T12:00:00Z"
    }
    mock_powerwall.power.return_value = {"solar": 1500, "battery": 2000, "load": 3500}
    mock_powerwall.grid.return_value = -1000
    mock_powerwall.poll.return_value = {"percentage": 75.5}

    coordinator = Pw3DataUpdateCoordinator(hass, mock_powerwall)
    await coordinator._async_update_data()

    assert coordinator.data == {
        "solar": 1.5,
        "battery": 2.0,
        "home": 3.5,
        "grid": -1.0,
        "percentage": 75.5,
        "last_updated": "2023-05-01T12:00:00Z",
    }


async def test_coordinator_update_failure(hass, mock_powerwall):
    """Test coordinator update failure."""
    mock_powerwall.solar.return_value = None

    coordinator = Pw3DataUpdateCoordinator(hass, mock_powerwall)
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()
