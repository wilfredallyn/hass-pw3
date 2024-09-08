"""Adds config flow for pw3."""

import voluptuous as vol
from homeassistant import config_entries

from .const import DOMAIN


class Pw3ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        errors = {}
        if user_input is not None:
            # Validate email
            if "@" not in user_input["pw_email"]:
                errors["pw_email"] = "invalid_email"
            else:
                return self.async_create_entry(title="PW3", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "pw_email", description="Your Tesla account email"
                    ): str,
                    vol.Required(
                        "pw_timezone",
                        description="Your timezone (e.g., America/New_York)",
                        default="America/New_York",
                    ): str,
                }
            ),
            errors=errors,
        )

    # Ensure the integration always starts with the user step
    async_step_import = async_step_user
