import logging

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_BRIDGE_ID, CONF_NAME
from .coordinator import DutchBridgesDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the NDW Dutch Bridges binary sensor."""
    # Use the mapped coordinator
    coordinator = hass.data[DOMAIN][entry.entry_id]
    bridge_id = entry.data[CONF_BRIDGE_ID]

    # Read name from options, fallback to data
    name = entry.options.get(CONF_NAME, entry.data.get(CONF_NAME, f"Bridge {bridge_id}"))

    async_add_entities([DutchBridgeBinarySensor(coordinator, bridge_id, name)])

class DutchBridgeBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a Dutch Bridge binary sensor."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: DutchBridgesDataUpdateCoordinator, bridge_id: str, name: str):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._bridge_id = bridge_id
        self._attr_name = "State"
        self._attr_unique_id = f"dutch_bridge_{self._bridge_id}"
        self._attr_device_class = BinarySensorDeviceClass.DOOR
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._bridge_id)},
            name=name,
            manufacturer="NDW",
            model="Dutch Bridge",
        )

    @property
    def is_on(self):
        """Return true if the bridge is open (swing in operation)."""
        open_bridges = self.coordinator.data or set()
        return self._bridge_id in open_bridges

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            "bridge_id": self._bridge_id,
        }
