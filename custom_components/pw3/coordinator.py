import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.update_coordinator import UpdateFailed
from pypowerwall import Powerwall

from .const import DOMAIN

SCAN_INTERVAL = timedelta(seconds=30)

_LOGGER: logging.Logger = logging.getLogger(__package__)


class Pw3DataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, pw: Powerwall) -> None:
        """Initialize."""
        self.pw = pw
        self.platforms = []
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=1),
            # always_update=False,
        )

    async def _async_update_data(self):
        """Update data via library."""
        try:
            power = await self.hass.async_add_executor_job(self.pw.power)
            grid_raw = await self.hass.async_add_executor_job(self.pw.grid)
            perc = await self.hass.async_add_executor_job(
                self.pw.poll, "/api/system_status/soe"
            )
            battery = self._split_power_val(power["battery"])
            grid = self._split_power_val(grid_raw)

            data = {
                "solar": round(power["solar"]),
                "home": round(power["load"]),
                "battery_consumption": round(battery["consumption"]),
                "battery_production": round(battery["production"]),
                "grid_consumption": round(grid["consumption"]),
                "grid_production": round(grid["production"]),
                "percentage": round(perc["percentage"], 2),
                "last_updated": self.hass.loop.time(),
            }
            return data
        except Exception as exception:
            _LOGGER.error(f"Error updating Powerwall data: {str(exception)}")
            raise UpdateFailed() from exception

    def _split_power_val(self, val: float) -> dict:
        if val < 0:
            return {"consumption": 0, "production": abs(val)}
        else:
            return {"consumption": val, "production": 0}
