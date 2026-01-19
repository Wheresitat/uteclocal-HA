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
        _LOGGER.info(f"Checking device {device_id}: category={device_data.get('category')}, handleType={device_data.get('handleType')}, type={device_data.get('type')}, capabilities={list(device_data.get('capabilities', {}).keys())}")
        
        # Check if device is a lock - multiple detection methods
        is_lock = (
            device_data.get("type") == "lock" or
            device_data.get("category") == "SmartLock" or
            device_data.get("handleType") == "utec-lock" or
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
        
        # Method 1: Parse states array (U-tec API format)
        states = device_data.get("states", [])
        if states:
            for state in states:
                if state.get("capability") == "st.lock" and state.get("name") == "lockState":
                    lock_state = state.get("value", "").lower()
                    _LOGGER.debug(f"Lock {self._device_id} state from states array: {lock_state}")
                    return lock_state == "locked"
        
        # Method 2: Try capabilities.st.lock.state.value
        capabilities = device_data.get("capabilities", {})
        if "st.lock" in capabilities:
            lock_state = capabilities["st.lock"].get("state", {}).get("value")
            _LOGGER.debug(f"Lock {self._device_id} state from capabilities: {lock_state}")
            return lock_state == "locked"
        
        # Method 3: Try state.locked field
        state = device_data.get("state")
        if state and "locked" in state:
            locked = state.get("locked", False)
            _LOGGER.debug(f"Lock {self._device_id} state from state.locked: {locked}")
            return locked
        
        # Method 4: Try attributes or status fields
        attributes = device_data.get("attributes", {})
        if "lockState" in attributes:
            lock_state = attributes.get("lockState")
            _LOGGER.debug(f"Lock {self._device_id} state from attributes.lockState: {lock_state}")
            return lock_state in ["locked", "LOCKED", "Locked", 1, True]
        
        # Method 5: Check if there's a direct status field
        status = device_data.get("status")
        if status:
            _LOGGER.debug(f"Lock {self._device_id} status field: {status}")
            if isinstance(status, dict):
                if "locked" in status:
                    return status["locked"]
                if "lock" in status:
                    return status["lock"] in ["locked", "LOCKED", "Locked", 1, True]
            elif isinstance(status, str):
                return status.lower() == "locked"
        
        _LOGGER.warning(f"Could not determine lock state for {self._device_id}. Device data keys: {device_data.keys()}")
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
