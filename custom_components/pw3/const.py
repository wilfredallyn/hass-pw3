"""Constants for pw3."""

# Base component constants
NAME = "pw3"
DOMAIN = "pw3"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.1.0"

ATTRIBUTION = "Data provided by Tesla via pypowerwall"
ISSUE_URL = "https://github.com/wilfredallyn/pw3/issues"

# Icons
ICON = "mdi:format-quote-close"

# Device classes
BINARY_SENSOR_DEVICE_CLASS = "connectivity"

# Platforms
BINARY_SENSOR = "binary_sensor"
SENSOR = "sensor"
SWITCH = "switch"
ENERGY_SENSOR = "energy"
PLATFORMS = [SENSOR]


# Configuration and options
CONF_ENABLED = "enabled"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_SOLAR = "solar"
CONF_BATTERY = "battery"
CONF_HOME = "home"
CONF_GRID = "grid"

# Defaults
DEFAULT_NAME = DOMAIN

# Services
SERVICE_SET_RESERVE = "set_reserve"
SERVICE_SET_MODE = "set_mode"
SERVICE_SET_GRID_CHARGING = "set_grid_charging"

# Service attributes
ATTR_RESERVE_LEVEL = "reserve_level"
ATTR_OPERATION_MODE = "operation_mode"
ATTR_GRID_CHARGING = "enabled"

# Operation modes
MODE_SELF_CONSUMPTION = "self_consumption"
MODE_BACKUP = "backup"
MODE_AUTONOMOUS = "autonomous"


STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""
