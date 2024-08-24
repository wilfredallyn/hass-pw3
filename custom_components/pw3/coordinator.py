from datetime import timedelta
import logging
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from pypowerwall import Powerwall

from .const import DOMAIN

SCAN_INTERVAL = timedelta(seconds=30)

_LOGGER: logging.Logger = logging.getLogger(__package__)


class Pw3DataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, pw: Powerwall) -> None:
        """Initialize."""
        self.pw = pw
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=5),
        )

    async def _async_update_data(self):
        """Update data via library."""
        try:
            solar_raw = await self.hass.async_add_executor_job(
                self.pw.solar, verbose=True
            )
            if solar_raw is None:
                raise UpdateFailed("Failed to fetch solar data")

            at = solar_raw["last_communication_time"]
            power = await self.hass.async_add_executor_job(self.pw.power)
            grid = await self.hass.async_add_executor_job(self.pw.grid)
            perc = await self.hass.async_add_executor_job(
                self.pw.poll, "/api/system_status/soe"
            )

            return {
                "solar": round(power["solar"] / 1000.0, 2),
                "battery": round(power["battery"] / 1000.0, 2),
                "home": round(power["load"] / 1000.0, 2),
                "grid": round(grid / 1000.0, 2),
                "percentage": round(perc["percentage"], 2),
                "last_updated": at,
            }
        except Exception as exception:
            raise UpdateFailed() from exception
