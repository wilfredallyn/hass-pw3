"""Sensor platform for pw3."""
from .const import DEFAULT_NAME
from .const import DOMAIN
from .const import ICON
from .const import SENSOR
from .entity import Pw3Entity

from datetime import timedelta
import os
import logging
from pypowerwall import Powerwall
from homeassistant.util import Throttle

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=5)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    auth_file = os.path.join(hass.config.path(), '.pypowerwall.auth')
    site_file = os.path.join(hass.config.path(), '.pypowerwall.site')
    pw_sensor = Pw3Sensor(auth_file, site_file)
    async_add_entities([pw_sensor])


class Pw3Sensor(Pw3Entity):
    def __init__(self, auth_file, site_file):
        self._auth_file = auth_file
        self._site_file = site_file
        self._pw = None
        self._state = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{DEFAULT_NAME}_{SENSOR}"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get("body")

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON

    @property
    def device_class(self):
        """Return device class of the sensor."""
        return "pw3__custom_device_class"

    @Throttle(SCAN_INTERVAL)
    async def async_update(self):
        if not self._pw:
            self._pw = Powerwall(auth_file=self._auth_file, site_file=self._site_file)

            # PW_HOST = os.getenv("PW_HOST", "")
            # PW_PASSWORD = os.getenv("PW_PASSWORD", "")
            # PW_EMAIL = os.getenv("PW_EMAIL", "")
            # PW_TIMEZONE = os.getenv("PW_TIMEZONE", "")
            # pw = Powerwall(
            #     host=PW_HOST,
            #     password=PW_PASSWORD,
            #     email=PW_EMAIL,
            #     timezone=PW_TIMEZONE,
            #     cloudmode=True,
            #     # auto_select=True,
            # )
        try:
            await self._pw.update()
            self._state = self._pw.get_solar_power()
        except Exception as e:
            _LOGGER.error("Error updating Powerwall data: %s", e)
            self._state = None
