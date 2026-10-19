import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN, CONF_BRIDGE_ID, CONF_NAME

DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_BRIDGE_ID): str,
    vol.Optional(CONF_NAME, default="Dutch Bridge"): str,
})


class DutchBridgesConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NDW Dutch Bridges."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Validate input if needed
            bridge_id = user_input[CONF_BRIDGE_ID]

            # Check if this bridge_id is already configured
            await self.async_set_unique_id(bridge_id)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return DutchBridgesOptionsFlowHandler(config_entry)


class DutchBridgesOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for NDW Dutch Bridges."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Get name from options, fallback to data
        current_name = self.config_entry.options.get(CONF_NAME, self.config_entry.data.get(CONF_NAME))

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(CONF_NAME, default=current_name): str,
            }),
        )
