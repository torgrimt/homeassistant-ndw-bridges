import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import DutchBridgesDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["binary_sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up NDW Dutch Bridges from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Use a single shared coordinator for all bridge entities
    # Set it before awaiting refresh to avoid race conditions
    if "coordinator" not in hass.data[DOMAIN]:
        coordinator = DutchBridgesDataUpdateCoordinator(hass)
        hass.data[DOMAIN]["coordinator"] = coordinator
        await coordinator.async_config_entry_first_refresh()
    else:
        coordinator = hass.data[DOMAIN]["coordinator"]
        # In case the first refresh is still running or hasn't started,
        # ensuring it's updated is good, but HA's coordinator handles concurrent
        # initializations reasonably well. We don't need to force refresh here
        # since it will wait for the first one if in progress, or use cached data.
        if not coordinator.last_update_success:
             await coordinator.async_config_entry_first_refresh()

    # Register an update listener for options changes
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Do not pop the coordinator here, as it might be used by other entries.
    # A complete cleanup would check if this is the last entry being removed.
    if not hass.config_entries.async_entries(DOMAIN):
        hass.data.pop(DOMAIN, None)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
