import asyncio
import gzip
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, UPDATE_INTERVAL, NDW_PLANNING_URL

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

            async def fetch_url(url):
                async with asyncio.timeout(10):
                    async with session.get(url) as response:
                        response.raise_for_status()
                        return await response.read()

            results = await asyncio.gather(
                fetch_url(NDW_URL),
                fetch_url(NDW_PLANNING_URL),
                return_exceptions=True
            )

            current_data = results[0]
            planning_data = results[1]

            if isinstance(current_data, Exception):
                raise current_data

            if isinstance(planning_data, Exception):
                _LOGGER.warning(f"Error fetching NDW planning API: {planning_data}")
                planning_data = None

            data = await asyncio.to_thread(self._parse_xml, current_data, planning_data)
            self.bridge_states = data.get("bridges_in_operation", set())
            return data

        except Exception as err:
            raise UpdateFailed(f"Error communicating with NDW API: {err}")

    def _parse_xml(self, current_compressed_data, planning_compressed_data):
        """Decompress and parse XML to find bridge states and planned openings."""
        def strip_ns(tag):
            if '}' in tag:
                return tag.split('}', 1)[1]
            return tag

        bridges_in_operation = set()
        planned_openings = {}
        now = datetime.now(timezone.utc)
        today = now.date()

        try:
            xml_data = gzip.decompress(current_compressed_data)
            root = ET.fromstring(xml_data)

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
        except Exception as err:
            _LOGGER.error(f"Failed to parse current XML: {err}")
            raise

        if planning_compressed_data:
            try:
                xml_data_planning = gzip.decompress(planning_compressed_data)
                root_planning = ET.fromstring(xml_data_planning)

                for situation in root_planning.iter():
                    if strip_ns(situation.tag) == "situationRecord":
                        is_bridge = False
                        for child in situation.iter():
                            if strip_ns(child.tag) == "generalNetworkManagementType" and child.text == "bridgeSwingInOperation":
                                is_bridge = True
                                break

                        if is_bridge:
                            bridge_id = None
                            start_time_str = None

                            for child in situation.iter():
                                if strip_ns(child.tag) == "externalLocationCode" and child.text:
                                    bridge_id = child.text.strip()
                                if strip_ns(child.tag) == "overallStartTime" and child.text:
                                    start_time_str = child.text.strip()

                            if bridge_id and start_time_str:
                                try:
                                    # Expected format: 2026-10-20T17:42:00Z
                                    if start_time_str.endswith("Z"):
                                        start_time_str = start_time_str[:-1] + "+00:00"
                                    dt = datetime.fromisoformat(start_time_str)

                                    # Filter: must be today and in the future
                                    if dt.date() == today and dt > now:
                                        if bridge_id not in planned_openings:
                                            planned_openings[bridge_id] = []
                                        planned_openings[bridge_id].append(dt)
                                except ValueError:
                                    _LOGGER.warning(f"Failed to parse time string: {start_time_str}")
                                    continue
            except Exception as err:
                _LOGGER.error(f"Failed to parse planning XML: {err}")

        # Sort the planned openings
        for b_id in planned_openings:
            planned_openings[b_id].sort()

        return {
            "bridges_in_operation": bridges_in_operation,
            "planned_openings": planned_openings
        }
