"""Support for U-tec sensors."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
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
    """Set up U-tec sensors from a config entry."""
    coordinator: UtecDataUpdateCoordinator = hass.data["uteclocal"][entry.entry_id]

    entities = []
    for device_id, device_data in coordinator.data.items():
        # Add battery sensor if available in any format
        capabilities = device_data.get("capabilities", {})
        attributes = device_data.get("attributes", {})
        
        # Check multiple battery field locations
        has_battery = (
            "st.battery" in capabilities or
            "batteryLevel" in attributes or
            "batteryLevelRange" in attributes or
            "battery" in device_data
        )
        
        if has_battery:
            _LOGGER.info(f"Adding battery sensor for {device_id}")
            entities.append(UtecBatterySensor(coordinator, device_id, device_data))

    async_add_entities(entities)


class UtecBatterySensor(CoordinatorEntity, SensorEntity):
    """Representation of a U-tec battery sensor."""

    _attr_native_unit_of_measurement = "%"
    _attr_device_class = "battery"

    def __init__(
        self,
        coordinator: UtecDataUpdateCoordinator,
        device_id: str,
        device_data: dict,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._device_id = device_id
        device_name = device_data.get("name", f"U-tec Lock {device_id}")
        self._attr_name = f"{device_name} Battery"
        self._attr_unique_id = f"utec_{device_id}_battery"

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {("uteclocal", self._device_id)},
            "name": self.coordinator.data[self._device_id].get("name", f"U-tec Lock {self._device_id}"),
            "manufacturer": "U-tec",
            "model": self.coordinator.data[self._device_id].get("model", "Lock"),
        }

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        device_data = self.coordinator.data.get(self._device_id, {})
        
        # Method 1: capabilities.st.battery.state.value
        capabilities = device_data.get("capabilities", {})
        if "st.battery" in capabilities:
            battery_level = capabilities["st.battery"].get("state", {}).get("value")
            if battery_level is not None:
                return int(battery_level)
        
        # Method 2: attributes.batteryLevel
        attributes = device_data.get("attributes", {})
        if "batteryLevel" in attributes:
            battery_level = attributes.get("batteryLevel")
            if battery_level is not None:
                return int(battery_level)
        
        # Method 3: Direct battery field
        if "battery" in device_data:
            battery_level = device_data.get("battery")
            if battery_level is not None:
                return int(battery_level)
        
        # Method 4: status.battery
        status = device_data.get("status", {})
        if isinstance(status, dict) and "battery" in status:
            battery_level = status.get("battery")
            if battery_level is not None:
                return int(battery_level)
        
        _LOGGER.debug(f"Could not find battery level for {self._device_id}")
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._device_id in self.coordinator.data
