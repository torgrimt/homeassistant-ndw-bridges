import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import DOMAIN, CONF_BRIDGE_ID, CONF_NAME, KNOWN_BRIDGES

DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_BRIDGE_ID): selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                selector.SelectOptionDict(value=k, label=v)
                for k, v in KNOWN_BRIDGES.items()
            ],
            custom_value=True,
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    ),
    vol.Optional(CONF_NAME): str,
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

            # Assign name automatically if not specified
            name = user_input.get(CONF_NAME)
            if not name:
                name = KNOWN_BRIDGES.get(bridge_id, f"Bridge {bridge_id}")
                user_input[CONF_NAME] = name

            return self.async_create_entry(title=name, data=user_input)

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
