"""Sensor platform for pw3."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
import logging
from .const import DOMAIN

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorStateClass,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Powerwall sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    sensors = [
        PowerwallSensor(coordinator, "solar", "Solar Power", "kW"),
        PowerwallSensor(coordinator, "battery", "Battery Power", "kW"),
        PowerwallSensor(coordinator, "home", "Home Power", "kW"),
        PowerwallSensor(coordinator, "grid", "Grid Power", "kW"),
        PowerwallSensor(coordinator, "percentage", "Battery Percentage", "%"),
    ]

    async_add_entities(sensors, True)


class PowerwallSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Powerwall sensor."""

    def __init__(self, coordinator, sensor_type, name, unit):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._name = name
        self._unit = unit
        self._attr_unique_id = f"powerwall_{sensor_type}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"Powerwall {self._name}"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get(self._sensor_type)

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        if self._unit == "kW":
            return SensorDeviceClass.POWER
        elif self._unit == "%":
            return SensorDeviceClass.BATTERY
        return None

    @property
    def state_class(self):
        """Return the state class of the sensor."""
        if self._unit == "kW":
            return SensorStateClass.MEASUREMENT
        elif self._unit == "%":
            return SensorStateClass.MEASUREMENT
        return None

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        attributes = super().extra_state_attributes or {}
        attributes["last_updated"] = self.coordinator.data.get("last_updated")
        if self._sensor_type == "grid":
            attributes["power_type"] = "production" if self.state < 0 else "consumption"
        return attributes
