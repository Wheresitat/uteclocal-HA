"""Support for U-tec locks."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import UtecDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up U-tec locks from a config entry."""
    _LOGGER.info("=== Setting up U-tec lock platform ===")
    coordinator: UtecDataUpdateCoordinator = hass.data["uteclocal"][entry.entry_id]

    _LOGGER.info(f"Coordinator has {len(coordinator.data)} devices")
    
    entities = []
    for device_id, device_data in coordinator.data.items():
        _LOGGER.info(f"Checking device {device_id}: type={device_data.get('type')}, capabilities={list(device_data.get('capabilities', {}).keys())}")
        
        # Check if device is a lock
        is_lock = (
            device_data.get("type") == "lock" or
            "st.lock" in str(device_data.get("capabilities", {}))
        )
        
        if is_lock:
            _LOGGER.info(f"✅ Creating lock entity for {device_id}")
            entities.append(UtecLock(coordinator, device_id, device_data))
        else:
            _LOGGER.warning(f"❌ Device {device_id} is not a lock, skipping")

    _LOGGER.info(f"Adding {len(entities)} lock entities to Home Assistant")
    async_add_entities(entities)
    _LOGGER.info("=== Lock platform setup complete ===")


class UtecLock(CoordinatorEntity, LockEntity):
    """Representation of a U-tec lock."""

    def __init__(
        self,
        coordinator: UtecDataUpdateCoordinator,
        device_id: str,
        device_data: dict,
    ) -> None:
        """Initialize the lock."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._attr_name = device_data.get("name", f"U-tec Lock {device_id}")
        self._attr_unique_id = f"utec_{device_id}"
        _LOGGER.info(f"Lock entity initialized: {self._attr_name} ({self._attr_unique_id})")

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {("uteclocal", self._device_id)},
            "name": self._attr_name,
            "manufacturer": "U-tec",
            "model": self.coordinator.data[self._device_id].get("model", "Lock"),
        }

    @property
    def is_locked(self) -> bool | None:
        """Return true if lock is locked."""
        device_data = self.coordinator.data.get(self._device_id, {})
        
        # Try to get lock state from capabilities
        capabilities = device_data.get("capabilities", {})
        if "st.lock" in capabilities:
            lock_state = capabilities["st.lock"].get("state", {}).get("value")
            _LOGGER.debug(f"Lock {self._device_id} state from capabilities: {lock_state}")
            return lock_state == "locked"
        
        # Fallback to state field
        state = device_data.get("state")
        if state:
            locked = state.get("locked", False)
            _LOGGER.debug(f"Lock {self._device_id} state from state field: {locked}")
            return locked
        
        _LOGGER.warning(f"Could not determine lock state for {self._device_id}")
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._device_id in self.coordinator.data

    async def async_lock(self, **kwargs: Any) -> None:
        """Lock the device."""
        _LOGGER.info(f"Lock command called for {self._device_id}")
        success = await self.coordinator.async_lock(self._device_id)
        if success:
            await self.coordinator.async_request_refresh()

    async def async_unlock(self, **kwargs: Any) -> None:
        """Unlock the device."""
        _LOGGER.info(f"Unlock command called for {self._device_id}")
        success = await self.coordinator.async_unlock(self._device_id)
        if success:
            await self.coordinator.async_request_refresh()
