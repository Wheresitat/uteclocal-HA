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
    _LOGGER.info("=== U-tec Integration Setup Started ===")
    host = entry.data[CONF_HOST]
    _LOGGER.info(f"Gateway host: {host}")
    
    coordinator = UtecDataUpdateCoordinator(hass, host)
    
    _LOGGER.info("Performing first refresh...")
    await coordinator.async_config_entry_first_refresh()
    
    _LOGGER.info(f"First refresh complete. Found {len(coordinator.data)} devices")
    for device_id, device_data in coordinator.data.items():
        _LOGGER.info(f"  - Device {device_id}: {device_data.get('name', 'Unknown')}")

    hass.data.setdefault("uteclocal", {})[entry.entry_id] = coordinator

    _LOGGER.info(f"Setting up platforms: {PLATFORMS}")
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    _LOGGER.info("=== U-tec Integration Setup Complete ===")
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
        _LOGGER.info(f"Coordinator initialized with host: {host}")

        super().__init__(
            hass,
            _LOGGER,
            name="U-tec Local Gateway",
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self):
        """Update data via library."""
        _LOGGER.debug(f"Fetching devices from {self.host}/api/devices")
        try:
            async with async_timeout.timeout(10):
                devices_response = await self.session.get(f"{self.host}/api/devices")
                devices_data = await devices_response.json()
                
                _LOGGER.debug(f"Raw device response: {devices_data}")
                
                devices = {}
                if "payload" in devices_data and "devices" in devices_data["payload"]:
                    device_list = devices_data["payload"]["devices"]
                    _LOGGER.info(f"Found {len(device_list)} devices in API response")
                    
                    for device in device_list:
                        device_id = device.get("id")
                        device_name = device.get("name", "Unknown")
                        _LOGGER.info(f"Processing device: {device_id} ({device_name})")
                        
                        if device_id:
                            # Get status for each device
                            try:
                                _LOGGER.debug(f"Getting status for {device_id}")
                                status_response = await self.session.post(
                                    f"{self.host}/api/status",
                                    json={"id": device_id}
                                )
                                status_data = await status_response.json()
                                _LOGGER.debug(f"Status response for {device_id}: {status_data}")
                                
                                # Merge device info with status
                                device_info = device.copy()
                                if "payload" in status_data and "devices" in status_data["payload"]:
                                    if status_data["payload"]["devices"]:
                                        device_info.update(status_data["payload"]["devices"][0])
                                
                                devices[device_id] = device_info
                                _LOGGER.info(f"Device {device_id} added to coordinator data")
                            except Exception as err:
                                _LOGGER.warning(f"Error getting status for {device_id}: {err}")
                                devices[device_id] = device
                else:
                    _LOGGER.warning(f"Unexpected API response structure: {devices_data}")
                
                _LOGGER.info(f"Update complete. Total devices: {len(devices)}")
                return devices
        except Exception as err:
            _LOGGER.error(f"Error communicating with API: {err}", exc_info=True)
            raise UpdateFailed(f"Error communicating with API: {err}")

    async def async_lock(self, device_id: str) -> bool:
        """Lock a device."""
        _LOGGER.info(f"Locking device {device_id}")
        try:
            async with async_timeout.timeout(10):
                response = await self.session.post(
                    f"{self.host}/api/lock",
                    json={"id": device_id}
                )
                success = response.status == 200
                _LOGGER.info(f"Lock command for {device_id}: {'success' if success else 'failed'}")
                return success
        except Exception as err:
            _LOGGER.error(f"Error locking device {device_id}: {err}")
            return False

    async def async_unlock(self, device_id: str) -> bool:
        """Unlock a device."""
        _LOGGER.info(f"Unlocking device {device_id}")
        try:
            async with async_timeout.timeout(10):
                response = await self.session.post(
                    f"{self.host}/api/unlock",
                    json={"id": device_id}
                )
                success = response.status == 200
                _LOGGER.info(f"Unlock command for {device_id}: {'success' if success else 'failed'}")
                return success
        except Exception as err:
            _LOGGER.error(f"Error unlocking device {device_id}: {err}")
            return False
