import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_BRIDGE_ID, CONF_NAME
from .coordinator import DutchBridgesDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the NDW Dutch Bridges sensor."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    bridge_id = entry.data[CONF_BRIDGE_ID]

    name = entry.options.get(CONF_NAME, entry.data.get(CONF_NAME, f"Bridge {bridge_id}"))

    async_add_entities([DutchBridgeNextOpeningSensor(coordinator, bridge_id, name)])

class DutchBridgeNextOpeningSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Dutch Bridge next opening sensor."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: DutchBridgesDataUpdateCoordinator, bridge_id: str, name: str):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._bridge_id = bridge_id
        self._attr_translation_key = "next_opening"
        self._attr_unique_id = f"dutch_bridge_next_opening_{self._bridge_id}"
        self._attr_device_class = "timestamp"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._bridge_id)},
            name=name,
            manufacturer="NDW",
            model="Dutch Bridge",
        )

    @property
    def native_value(self):
        """Return the next scheduled opening timestamp."""
        if isinstance(self.coordinator.data, dict):
            planned_openings = self.coordinator.data.get("planned_openings", {}).get(self._bridge_id, [])
            if planned_openings:
                return planned_openings[0]
        return None

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        attrs = {
            "bridge_id": self._bridge_id,
        }

        if isinstance(self.coordinator.data, dict):
            planned_openings = self.coordinator.data.get("planned_openings", {}).get(self._bridge_id, [])
            attrs["scheduled_openings"] = [dt.isoformat() for dt in planned_openings]

        return attrs
