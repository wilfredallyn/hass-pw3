"""Sensor platform for pw3."""

from datetime import datetime, timedelta
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
        PowerwallEnergySensor(coordinator, "solar", "Solar Energy", "kWh"),
        PowerwallEnergySensor(coordinator, "battery", "Battery Energy", "kWh"),
        PowerwallEnergySensor(coordinator, "home", "Home Energy", "kWh"),
        PowerwallEnergySensor(coordinator, "grid", "Grid Energy", "kWh"),
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


class PowerwallEnergySensor(PowerwallSensor):
    """Representation of a Powerwall energy sensor."""

    def __init__(self, coordinator, sensor_type, name, unit):
        super().__init__(coordinator, sensor_type, name, unit)
        self._attr_unique_id = f"powerwall_{sensor_type}_energy"
        self._last_update = None
        self._energy_value = 0
        self._last_reported = None

    @property
    def native_value(self):
        """Return the state of the sensor."""
        current_power = self.coordinator.data.get(self._sensor_type)
        current_time = datetime.now()

        if self._last_update is not None:
            time_diff = (
                current_time - self._last_update
            ).total_seconds() / 3600  # Convert to hours
            self._energy_value += current_power * time_diff

        self._last_update = current_time

        # Report energy hourly
        if self._last_reported is None or (
            current_time - self._last_reported
        ) >= timedelta(hours=1):
            self._last_reported = current_time
            return round(self._energy_value, 3)

        # Return None if it's not time to report yet
        return None

    @property
    def device_class(self):
        return SensorDeviceClass.ENERGY

    @property
    def state_class(self):
        return SensorStateClass.TOTAL_INCREASING

    @property
    def native_unit_of_measurement(self):
        return "kWh"
