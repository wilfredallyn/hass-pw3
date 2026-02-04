"""
Custom integration to integrate pw3 with Home Assistant.

For more details about this integration, please refer to
https://github.com/wilfredallyn/pw3
"""

import asyncio
import logging
from datetime import timedelta

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Config, HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from pypowerwall import Powerwall

from .const import (
    ATTR_GRID_CHARGING,
    ATTR_OPERATION_MODE,
    ATTR_RESERVE_LEVEL,
    DOMAIN,
    MODE_AUTONOMOUS,
    MODE_BACKUP,
    MODE_SELF_CONSUMPTION,
    PLATFORMS,
    SERVICE_SET_GRID_CHARGING,
    SERVICE_SET_MODE,
    SERVICE_SET_RESERVE,
    STARTUP_MESSAGE,
)
from .coordinator import Pw3DataUpdateCoordinator

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

SCAN_INTERVAL = timedelta(seconds=30)

_LOGGER: logging.Logger = logging.getLogger(__package__)

# Service schemas
SERVICE_SET_RESERVE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_RESERVE_LEVEL): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=100)
        ),
    }
)

SERVICE_SET_MODE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_OPERATION_MODE): vol.In(
            [MODE_SELF_CONSUMPTION, MODE_BACKUP, MODE_AUTONOMOUS]
        ),
    }
)

SERVICE_SET_GRID_CHARGING_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_GRID_CHARGING): cv.boolean,
    }
)


async def async_setup(hass: HomeAssistant, config: Config):
    """Set up this integration using YAML is not supported."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up this integration using UI."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info(STARTUP_MESSAGE)

    pw_email = entry.data.get("pw_email")
    pw_timezone = entry.data.get("pw_timezone")

    if not pw_email:
        _LOGGER.error("No email provided in configuration")
        return False

    def init_powerwall():
        return Powerwall(
            authpath=hass.config.path(),
            host="",
            password="",
            email=pw_email,
            timezone=pw_timezone,
            cloudmode=True,
        )

    try:
        pw = await hass.async_add_executor_job(init_powerwall)
    except Exception as e:
        _LOGGER.error(f"Error initializing Powerwall: {str(e)}")
        raise ConfigEntryNotReady from e

    coordinator = Pw3DataUpdateCoordinator(hass, pw)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Register services (only once for the domain)
    if not hass.services.has_service(DOMAIN, SERVICE_SET_RESERVE):
        await _async_register_services(hass)

    await hass.config_entries.async_forward_entry_setups(
        entry, [platform for platform in PLATFORMS if entry.options.get(platform, True)]
    )

    entry.add_update_listener(async_reload_entry)
    return True


async def _async_register_services(hass: HomeAssistant) -> None:
    """Register pw3 services."""

    def _get_powerwall() -> Powerwall:
        """Get the Powerwall instance from any entry."""
        for entry_id, coordinator in hass.data[DOMAIN].items():
            if hasattr(coordinator, "pw"):
                return coordinator.pw
        raise ValueError("No Powerwall instance available")

    async def async_set_reserve(call: ServiceCall) -> None:
        """Handle the set_reserve service call."""
        reserve_level = call.data[ATTR_RESERVE_LEVEL]
        _LOGGER.info(f"Setting Powerwall reserve level to {reserve_level}%")

        try:
            pw = _get_powerwall()
            result = await hass.async_add_executor_job(pw.set_reserve, reserve_level)
            if result:
                _LOGGER.info(f"Successfully set reserve to {reserve_level}%")
            else:
                _LOGGER.warning(f"set_reserve returned: {result}")
        except Exception as e:
            _LOGGER.error(f"Failed to set reserve level: {e}")
            raise

    async def async_set_mode(call: ServiceCall) -> None:
        """Handle the set_mode service call."""
        mode = call.data[ATTR_OPERATION_MODE]
        _LOGGER.info(f"Setting Powerwall operation mode to {mode}")

        try:
            pw = _get_powerwall()
            result = await hass.async_add_executor_job(pw.set_mode, mode)
            if result:
                _LOGGER.info(f"Successfully set mode to {mode}")
            else:
                _LOGGER.warning(f"set_mode returned: {result}")
        except Exception as e:
            _LOGGER.error(f"Failed to set operation mode: {e}")
            raise

    async def async_set_grid_charging(call: ServiceCall) -> None:
        """Handle the set_grid_charging service call."""
        enabled = call.data[ATTR_GRID_CHARGING]
        _LOGGER.info(f"Setting Powerwall grid charging to {enabled}")

        try:
            pw = _get_powerwall()
            result = await hass.async_add_executor_job(pw.set_grid_charging, enabled)
            if result:
                _LOGGER.info(f"Successfully set grid charging to {enabled}")
            else:
                _LOGGER.warning(f"set_grid_charging returned: {result}")
        except Exception as e:
            _LOGGER.error(f"Failed to set grid charging: {e}")
            raise

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_RESERVE,
        async_set_reserve,
        schema=SERVICE_SET_RESERVE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_MODE,
        async_set_mode,
        schema=SERVICE_SET_MODE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_GRID_CHARGING,
        async_set_grid_charging,
        schema=SERVICE_SET_GRID_CHARGING_SCHEMA,
    )


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    unloaded = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
                if platform in coordinator.platforms
            ]
        )
    )
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
