import asyncio
import gzip
import logging
import xml.etree.ElementTree as ET
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

NDW_URL = "https://opendata.ndw.nu/actueel_beeld.xml.gz"

class DutchBridgesDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching NDW bridge data."""

    def __init__(self, hass: HomeAssistant):
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.bridge_states = set()

    async def _async_update_data(self):
        """Fetch data from NDW."""
        try:
            session = async_get_clientsession(self.hass)
            async with asyncio.timeout(10):
                async with session.get(NDW_URL) as response:
                    response.raise_for_status()
                    compressed_data = await response.read()

            data = await asyncio.to_thread(self._parse_xml, compressed_data)
            self.bridge_states = data
            return data

        except Exception as err:
            raise UpdateFailed(f"Error communicating with NDW API: {err}")

    def _parse_xml(self, compressed_data):
        """Decompress and parse XML to find bridge states."""
        try:
            xml_data = gzip.decompress(compressed_data)
            root = ET.fromstring(xml_data)

            def strip_ns(tag):
                if '}' in tag:
                    return tag.split('}', 1)[1]
                return tag

            bridges_in_operation = set()

            for situation in root.iter():
                if strip_ns(situation.tag) == "situationRecord":
                    is_bridge = False
                    for child in situation.iter():
                        if strip_ns(child.tag) == "generalNetworkManagementType" and child.text == "bridgeSwingInOperation":
                            is_bridge = True
                            break

                    if is_bridge:
                        for child in situation.iter():
                            if strip_ns(child.tag) == "externalLocationCode" and child.text:
                                bridges_in_operation.add(child.text.strip())

            return bridges_in_operation

        except Exception as err:
            _LOGGER.error(f"Failed to parse XML: {err}")
            raise
