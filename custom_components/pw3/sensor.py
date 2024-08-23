"""Sensor platform for pw3."""

from .const import DEFAULT_NAME
from .const import DOMAIN
from .const import ICON
from .const import SENSOR
from .entity import Pw3Entity

from datetime import timedelta
import os
import logging
from homeassistant.helpers import config_validation as cv
from homeassistant.util import Throttle
from pypowerwall import Powerwall
import voluptuous as vol


_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=5)


class Pw3Sensor(Pw3Entity):
    def __init__(self, authpath, pw_email, pw_timezone):
        self._authpath = authpath
        self._pw_email = pw_email
        self._pw_timezone = pw_timezone
        self._pw = None
        self._state = None
        self._init_pw()

    def _init_pw(self):
        if os.path.exists(self._authpath):
            self._pw = Powerwall(
                authpath=self._authpath,
                host="",
                password="",
                email=self._pw_email,
                timezone=self._pw_timezone,
                cloudmode=True,
            )
        else:
            raise FileNotFoundError(
                f"Pypowerwall authentication files not found in {self._authpath}"
            )

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

    async def query_data(self):
        """Fetch Powerwall data and store it in Home Assistant."""
        solar_raw = self._pw.solar(verbose=True)
        if solar_raw is None:
            return

        at = solar_raw["last_communication_time"]
        power = self._pw.power()

        # Prepare the data
        data = {
            "solar": power["solar"] / 1000.0,
            "battery": power["battery"] / 1000.0,
            "home": power["load"] / 1000.0,
            "grid": self._pw.grid() / 1000.0,
            "perc": self._pw.poll("/api/system_status/soe")["percentage"],
        }

        self.hass.states.set(
            "sensor.powerwall_solar",
            data["solar"],
            {"unit_of_measurement": "kW", "last_updated": at},
        )
        self.hass.states.set(
            "sensor.powerwall_battery",
            data["battery"],
            {"unit_of_measurement": "kW", "last_updated": at},
        )
        self.hass.states.set(
            "sensor.powerwall_home",
            data["home"],
            {"unit_of_measurement": "kW", "last_updated": at},
        )
        self.hass.states.set(
            "sensor.powerwall_grid",
            data["grid"],
            {"unit_of_measurement": "kW", "last_updated": at},
        )
        self.hass.states.set(
            "sensor.powerwall_percentage",
            data["perc"],
            {"unit_of_measurement": "%", "last_updated": at},
        )

    async def async_added_to_hass(self):
        self._unsub_timer = self.hass.helpers.event.async_track_time_interval(
            self.query_data, timedelta(minutes=5)
        )

    async def async_will_remove_from_hass(self):
        self._unsub_timer()


PLATFORM_SCHEMA = vol.Schema(
    {
        vol.Required("authpath"): cv.string,
        vol.Required("pw_email"): cv.string,
        vol.Required("pw_timezone"): cv.string,
    }
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    authpath = config["authpath"]
    pw_email = config["pw_email"]
    pw_timezone = config["pw_timezone"]
    pw_sensor = Pw3Sensor(
        authpath=authpath,
        pw_email=pw_email,
        pw_timezone=pw_timezone,
    )
    async_add_entities([pw_sensor], update_before_add=True)
