"""Support for U-tec sensors."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity, SensorStateClass
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
        states = device_data.get("states", [])
        
        # Check multiple battery field locations
        has_battery = (
            "st.battery" in capabilities or
            "batteryLevel" in attributes or
            "batteryLevelRange" in attributes or
            "battery" in device_data or
            any(s.get("capability") == "st.batteryLevel" for s in states)
        )
        
        if has_battery:
            _LOGGER.info(f"Adding battery sensor for {device_id}")
            entities.append(UtecBatterySensor(coordinator, device_id, device_data))
        
        # Add health check sensor
        has_health_check = (
            "st.healthCheck" in capabilities or
            any(s.get("capability") == "st.healthCheck" for s in states)
        )
        
        if has_health_check:
            _LOGGER.info(f"Adding health check sensor for {device_id}")
            entities.append(UtecHealthSensor(coordinator, device_id, device_data))

    async_add_entities(entities)


class UtecBatterySensor(CoordinatorEntity, SensorEntity):
    """Representation of a U-tec battery sensor."""

    _attr_native_unit_of_measurement = "%"
    _attr_device_class = "battery"
    _attr_state_class = "measurement"

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
        
        # Method 1: Parse states array (U-tec API format)
        states = device_data.get("states", [])
        if states:
            for state in states:
                if state.get("capability") == "st.batteryLevel" and state.get("name") == "level":
                    battery_level = state.get("value")
                    if battery_level is not None:
                        return self._convert_battery_level(battery_level)
        
        # Method 2: capabilities.st.battery.state.value
        capabilities = device_data.get("capabilities", {})
        if "st.battery" in capabilities:
            battery_level = capabilities["st.battery"].get("state", {}).get("value")
            if battery_level is not None:
                return self._convert_battery_level(battery_level)
        
        # Method 3: attributes.batteryLevel
        attributes = device_data.get("attributes", {})
        if "batteryLevel" in attributes:
            battery_level = attributes.get("batteryLevel")
            if battery_level is not None:
                return self._convert_battery_level(battery_level)
        
        # Method 4: Direct battery field
        if "battery" in device_data:
            battery_level = device_data.get("battery")
            if battery_level is not None:
                return self._convert_battery_level(battery_level)
        
        # Method 5: status.battery or status.batteryLevel
        status = device_data.get("status", {})
        if isinstance(status, dict):
            if "battery" in status:
                battery_level = status.get("battery")
                if battery_level is not None:
                    return self._convert_battery_level(battery_level)
            if "batteryLevel" in status:
                battery_level = status.get("batteryLevel")
                if battery_level is not None:
                    return self._convert_battery_level(battery_level)
        
        _LOGGER.debug(f"Could not find battery level for {self._device_id}")
        return None
    
    def _convert_battery_level(self, level) -> int:
        """Convert battery level to percentage.
        
        U-tec uses 1-5 scale:
        5 = 100% (full)
        4 = 80%
        3 = 60%
        2 = 40%
        1 = 20%
        0 = 0% (empty)
        """
        try:
            level = int(level)
            # If already in percentage (0-100), return as-is
            if level > 5:
                return level
            # Convert 0-5 scale to 0-100%
            return level * 20
        except (ValueError, TypeError):
            _LOGGER.warning(f"Invalid battery level: {level}")
            return 0

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._device_id in self.coordinator.data


class UtecHealthSensor(CoordinatorEntity, SensorEntity):
    """Representation of a U-tec health check sensor."""

    _attr_device_class = None
    _attr_icon = "mdi:heart-pulse"

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
        self._attr_name = f"{device_name} Status"
        self._attr_unique_id = f"utec_{device_id}_health"

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
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        device_data = self.coordinator.data.get(self._device_id, {})
        
        # Method 1: Parse states array (U-tec API format)
        states = device_data.get("states", [])
        if states:
            for state in states:
                if state.get("capability") == "st.healthCheck" and state.get("name") == "status":
                    health_status = state.get("value")
                    if health_status:
                        _LOGGER.debug(f"Health status for {self._device_id}: {health_status}")
                        return str(health_status)
        
        # Method 2: capabilities.st.healthCheck
        capabilities = device_data.get("capabilities", {})
        if "st.healthCheck" in capabilities:
            health_status = capabilities["st.healthCheck"].get("state", {}).get("value")
            if health_status:
                return str(health_status)
        
        # Method 3: Direct health or online field
        if "health" in device_data:
            return str(device_data.get("health"))
        if "online" in device_data:
            return "Online" if device_data.get("online") else "Offline"
        
        return None
    
    @property
    def icon(self) -> str:
        """Return the icon based on status."""
        if self.native_value:
            status = self.native_value.lower()
            if status in ["online", "connected", "active"]:
                return "mdi:check-network"
            elif status in ["offline", "disconnected", "inactive"]:
                return "mdi:network-off"
        return "mdi:help-network"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._device_id in self.coordinator.data
