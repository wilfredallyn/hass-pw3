"""
Custom integration to integrate pw3 with Home Assistant.

For more details about this integration, please refer to
https://github.com/wilfredallyn/pw3
"""

import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Config
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from pypowerwall import Powerwall

from .const import DOMAIN
from .const import PLATFORMS
from .const import STARTUP_MESSAGE
from .coordinator import Pw3DataUpdateCoordinator

from homeassistant.helpers import config_validation as cv

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

SCAN_INTERVAL = timedelta(seconds=30)

_LOGGER: logging.Logger = logging.getLogger(__package__)


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

    await hass.config_entries.async_forward_entry_setups(
        entry, [platform for platform in PLATFORMS if entry.options.get(platform, True)]
    )

    entry.add_update_listener(async_reload_entry)
    return True


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
