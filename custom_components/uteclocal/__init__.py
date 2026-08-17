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
    DataUpdateCoordinator,
    UpdateFailed,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.LOCK, Platform.SENSOR]
SCAN_INTERVAL = timedelta(seconds=30)
DOMAIN = "uteclocal"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up U-tec Local Gateway from a config entry."""
    _LOGGER.info("=== U-tec Integration Setup Started ===")
    host = entry.data[CONF_HOST]
    _LOGGER.info(f"Gateway host: {host}")

    coordinator = UtecDataUpdateCoordinator(hass, host)

    _LOGGER.info("Performing first refresh...")
    await coordinator.async_config_entry_first_refresh()

    _LOGGER.info(f"First refresh complete. Found {len(coordinator.data)} devices")

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    _LOGGER.info(f"Setting up platforms: {PLATFORMS}")
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _LOGGER.info("=== U-tec Integration Setup Complete ===")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class UtecDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching U-tec data from the local gateway."""

    def __init__(self, hass: HomeAssistant, host: str) -> None:
        """Initialize."""
        self.host = host.rstrip("/")
        self.session = async_get_clientsession(hass)
        _LOGGER.info(f"Coordinator initialized with host: {self.host}")

        super().__init__(
            hass,
            _LOGGER,
            name="U-tec Local Gateway",
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self):
        """Fetch devices and state from local gateway."""
        _LOGGER.debug(f"Fetching devices from {self.host}/api/devices")
        try:
            async with async_timeout.timeout(10):
                devices_response = await self.session.get(f"{self.host}/api/devices")

                if devices_response.status == 401:
                    _LOGGER.error("U-tec Gateway returned 401. Session requires authorization on gateway UI.")
                    raise UpdateFailed("Local gateway session expired (401 Unauthorized).")

                if devices_response.status != 200:
                    raise UpdateFailed(f"Gateway returned HTTP {devices_response.status}")

                devices_data = await devices_response.json()

                devices = {}
                if "payload" in devices_data and "devices" in devices_data["payload"]:
                    device_list = devices_data["payload"]["devices"]

                    for device in device_list:
                        device_id = device.get("id")
                        if device_id:
                            try:
                                status_response = await self.session.post(
                                    f"{self.host}/api/status",
                                    json={"id": device_id}
                                )
                                status_data = await status_response.json()

                                device_info = device.copy()
                                if "payload" in status_data and "devices" in status_data["payload"]:
                                    if status_data["payload"]["devices"]:
                                        status_device = status_data["payload"]["devices"][0]
                                        device_info.update(status_device)

                                devices[device_id] = device_info
                            except Exception as err:
                                _LOGGER.warning(f"Error getting status for {device_id}: {err}")
                                devices[device_id] = device

                return devices
        except Exception as err:
            _LOGGER.error(f"Error communicating with API: {err}")
            raise UpdateFailed(f"Error communicating with API: {err}")

    async def async_lock(self, device_id: str) -> bool:
        """Lock a device via local gateway."""
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
        """Unlock a device via local gateway."""
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
