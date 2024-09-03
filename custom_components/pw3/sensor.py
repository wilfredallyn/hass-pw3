"""Sensor platform for pw3."""

import logging
from datetime import datetime
from datetime import timedelta

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor import SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfPower,
    UnitOfEnergy,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
import logging
from .const import DOMAIN
from .coordinator import Pw3DataUpdateCoordinator
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)


ENTITY_DESCRIPTION_KEY_MAP: dict[str, SensorEntityDescription] = {
    "solar": SensorEntityDescription(
        key="Solar Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "home": SensorEntityDescription(
        key="Home Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "battery_production": SensorEntityDescription(
        key="Battery Production Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "battery_consumption": SensorEntityDescription(
        key="Battery Consumption Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "grid_production": SensorEntityDescription(
        key="Grid Production Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "grid_consumption": SensorEntityDescription(
        key="Grid Consumption Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "solar_energy": SensorEntityDescription(
        key="Solar Energy",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    "home_energy": SensorEntityDescription(
        key="Home Energy",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    "battery_production_energy": SensorEntityDescription(
        key="Battery Production Energy",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    "battery_consumption_energy": SensorEntityDescription(
        key="Battery Consumption Energy",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    "grid_production_energy": SensorEntityDescription(
        key="Grid Production Energy",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    "grid_consumption_energy": SensorEntityDescription(
        key="Grid Consumption Energy",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    "percentage": SensorEntityDescription(
        key="Battery %",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
}

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Powerwall sensor platform."""
    coordinator: Pw3DataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    def _create_entity(
        sensor_key: str,
    ) -> PowerwallSensor:
        """Create the appropriate sensor entity based on the sensor key."""
        description = ENTITY_DESCRIPTION_KEY_MAP.get(sensor_key)
        if description is None:
            raise ValueError(f"Unknown sensor key: {sensor_key}")

        return PowerwallSensor(
            coordinator=coordinator,
            sensor_key=sensor_key,
            description=description,
        )

    def _create_energy_entity(power_sensor_key: str) -> PowerwallEnergySensor:
        energy_sensor_key = f"{power_sensor_key}_energy"
        description = ENTITY_DESCRIPTION_KEY_MAP.get(energy_sensor_key)
        if description is None:
            raise ValueError(f"Unknown sensor key: {energy_sensor_key}")

        return PowerwallEnergySensor(
            coordinator=coordinator,
            power_sensor_key=power_sensor_key,
            description=description,
        )

    await coordinator.async_config_entry_first_refresh()
    sensors = []

    for power_sensor_key in coordinator.data:
        if power_sensor_key in ENTITY_DESCRIPTION_KEY_MAP:
            power_sensor = _create_entity(power_sensor_key)
            sensors.append(power_sensor)

            energy_sensor_key = f"{power_sensor_key}_energy"
            if energy_sensor_key in ENTITY_DESCRIPTION_KEY_MAP:
                energy_sensor = _create_energy_entity(power_sensor_key)
                sensors.append(energy_sensor)

    async_add_entities(sensors)


class PowerwallSensor(CoordinatorEntity[Pw3DataUpdateCoordinator], SensorEntity):
    """Representation of a Powerwall sensor."""

    def __init__(
        self,
        coordinator: Pw3DataUpdateCoordinator,
        sensor_key: str,
        description: SensorEntityDescription,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._sensor_key = sensor_key
        self._attr_unique_id = f"pw_{sensor_key}"

    @property
    def name(self) -> str | None:
        """Return name of the entity."""
        return f"PW {self.entity_description.key}"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get(self._sensor_key)

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        attributes = super().extra_state_attributes or {}
        attributes["last_updated"] = self.coordinator.data.get("last_updated")
        return attributes


class PowerwallEnergySensor(CoordinatorEntity[Pw3DataUpdateCoordinator], SensorEntity):
    """Representation of a Powerwall energy sensor."""

    def __init__(
        self,
        coordinator: Pw3DataUpdateCoordinator,
        power_sensor_key: str,
        description: SensorEntityDescription,
    ):
        super().__init__(coordinator)
        self.entity_description = description
        self._power_sensor_key = power_sensor_key
        self._attr_unique_id = f"pw_{power_sensor_key}_energy"
        self._energy_value = 0
        self._last_update = None
        self._last_reported = None

    @property
    def name(self) -> str | None:
        """Return name of the entity."""
        return f"PW {self.entity_description.key}"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        current_power = self.coordinator.data.get(self._power_sensor_key, 0)
        current_time = datetime.now()

        if self._last_update is not None:
            time_diff = (current_time - self._last_update).total_seconds() / 3600
            self._energy_value += current_power * time_diff

        self._last_update = current_time

        if self._last_reported is None or (
            current_time - self._last_reported
        ) >= timedelta(hours=1):
            self._last_reported = current_time
            return round(self._energy_value, 3)

        return None
