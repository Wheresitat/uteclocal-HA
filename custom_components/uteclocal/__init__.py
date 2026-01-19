"""The U-tec Local Gateway integration."""
from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp
import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.LOCK, Platform.SENSOR]

SCAN_INTERVAL = timedelta(seconds=30)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up U-tec Local Gateway from a config entry."""
    host = entry.data[CONF_HOST]
    
    coordinator = UtecDataUpdateCoordinator(hass, host)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault("uteclocal", {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data["uteclocal"].pop(entry.entry_id)

    return unload_ok


class UtecDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching U-tec data."""

    def __init__(self, hass: HomeAssistant, host: str) -> None:
        """Initialize."""
        self.host = host
        self.session = async_get_clientsession(hass)

        super().__init__(
            hass,
            _LOGGER,
            name="U-tec Local Gateway",
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self):
        """Update data via library."""
        try:
            async with async_timeout.timeout(10):
                devices_response = await self.session.get(f"{self.host}/api/devices")
                devices_data = await devices_response.json()
                
                devices = {}
                if "payload" in devices_data and "devices" in devices_data["payload"]:
                    for device in devices_data["payload"]["devices"]:
                        device_id = device.get("id")
                        if device_id:
                            # Get status for each device
                            try:
                                status_response = await self.session.post(
                                    f"{self.host}/api/status",
                                    json={"id": device_id}
                                )
                                status_data = await status_response.json()
                                
                                # Merge device info with status
                                device_info = device.copy()
                                if "payload" in status_data and "devices" in status_data["payload"]:
                                    if status_data["payload"]["devices"]:
                                        device_info.update(status_data["payload"]["devices"][0])
                                
                                devices[device_id] = device_info
                            except Exception as err:
                                _LOGGER.warning(f"Error getting status for {device_id}: {err}")
                                devices[device_id] = device
                
                return devices
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")

    async def async_lock(self, device_id: str) -> bool:
        """Lock a device."""
        try:
            async with async_timeout.timeout(10):
                response = await self.session.post(
                    f"{self.host}/api/lock",
                    json={"id": device_id}
                )
                return response.status == 200
        except Exception as err:
            _LOGGER.error(f"Error locking device {device_id}: {err}")
            return False

    async def async_unlock(self, device_id: str) -> bool:
        """Unlock a device."""
        try:
            async with async_timeout.timeout(10):
                response = await self.session.post(
                    f"{self.host}/api/unlock",
                    json={"id": device_id}
                )
                return response.status == 200
        except Exception as err:
            _LOGGER.error(f"Error unlocking device {device_id}: {err}")
            return False
