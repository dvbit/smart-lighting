"""Sensor platform for Smart Lighting.

Exposes timer remaining values, active profile, and state machine status
as sensor entities. All sensors are diagnostic [Spec §13].

Timer sensors:
- Occupancy timer remaining [Spec §3]
- Failsafe timer remaining [Spec §8]
- Override timer remaining [Spec §11]
- Warning timer remaining [Spec §6]

Status sensors:
- Active profile (normal/soft) [Spec §12]
- State machine state [Spec §3, §10]
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval

from .const import CONF_AREA_NAME, DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Smart Lighting sensor entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    area_name = entry.data.get(CONF_AREA_NAME, "unknown")

    entities = [
        # Timer sensors
        SmartLightingTimerSensor(
            coordinator, entry, area_name, "occupancy_timer",
            "Occupancy Timer", "occupancy_timer_remaining",
        ),
        SmartLightingTimerSensor(
            coordinator, entry, area_name, "failsafe_timer",
            "Failsafe Timer", "failsafe_timer_remaining",
        ),
        SmartLightingTimerSensor(
            coordinator, entry, area_name, "override_timer",
            "Override Timer", "active_override_timer_remaining",
        ),
        SmartLightingTimerSensor(
            coordinator, entry, area_name, "warning_timer",
            "Warning Timer", "warning_timer_remaining",
        ),
        # Status sensors
        SmartLightingProfileSensor(coordinator, entry, area_name),
        SmartLightingStateSensor(coordinator, entry, area_name),
        # Adaptive timeout sensors
        SmartLightingAdaptiveSensor(
            coordinator, entry, area_name, "adaptive_factor",
            "Adaptive Factor", "adaptive_factor",
        ),
        SmartLightingAdaptiveSensor(
            coordinator, entry, area_name, "activation_count",
            "Activation Count", "activation_count",
        ),
        # Lux mirror sensor [Spec §9]
        SmartLightingLuxSensor(coordinator, entry, area_name),
    ]

    async_add_entities(entities)


class SmartLightingTimerSensor(SensorEntity):
    """Sensor showing remaining seconds on a coordinator timer.

    Uses polling via async_track_time_interval to update
    the remaining time every second while active.
    """

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator,
        entry: ConfigEntry,
        area_name: str,
        key: str,
        name: str,
        prop_name: str,
    ) -> None:
        """Initialize timer sensor.

        Args:
            coordinator: SmartLightingCoordinator instance.
            entry: Config entry.
            area_name: Area display name.
            key: Unique key suffix for entity_id.
            name: Human-readable sensor name.
            prop_name: Coordinator property name returning remaining seconds.
        """
        self._coordinator = coordinator
        self._entry = entry
        self._prop_name = prop_name
        self._unsub_interval = None

        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_{key}"
        self._attr_name = name
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> float:
        """Return remaining seconds."""
        return getattr(self._coordinator, self._prop_name, 0.0)

    async def async_added_to_hass(self) -> None:
        """Start periodic update for timer countdown."""
        # Update every second for live countdown
        self._unsub_interval = async_track_time_interval(
            self.hass,
            self._async_timer_tick,
            timedelta(seconds=1),
        )
        # Also listen to coordinator updates
        self._coordinator.set_update_callback(self._handle_coordinator_update)

    async def async_will_remove_from_hass(self) -> None:
        """Stop periodic update."""
        if self._unsub_interval:
            self._unsub_interval()
            self._unsub_interval = None

    @callback
    def _async_timer_tick(self, _now=None) -> None:
        """Update sensor value every second."""
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle coordinator state change."""
        self.async_write_ha_state()


class SmartLightingProfileSensor(SensorEntity):
    """Sensor showing current active profile [Spec §12].

    State is 'normal' or 'soft'.
    """

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self, coordinator, entry: ConfigEntry, area_name: str
    ) -> None:
        """Initialize profile sensor."""
        self._coordinator = coordinator
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_profile"
        self._attr_name = "Profile"
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> str:
        """Return current profile name [Spec §12]."""
        return self._coordinator.current_profile

    async def async_added_to_hass(self) -> None:
        """Register for coordinator updates."""
        self._coordinator.set_update_callback(self._handle_coordinator_update)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle coordinator state change."""
        self.async_write_ha_state()


class SmartLightingStateSensor(SensorEntity):
    """Sensor showing current state machine state [Spec §3, §10].

    State is one of: idle, active, warning, temp_override, perm_override.
    """

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self, coordinator, entry: ConfigEntry, area_name: str
    ) -> None:
        """Initialize state sensor."""
        self._coordinator = coordinator
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_state"
        self._attr_name = "State"
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> str:
        """Return current state machine state."""
        return self._coordinator.state

    async def async_added_to_hass(self) -> None:
        """Register for coordinator updates."""
        self._coordinator.set_update_callback(self._handle_coordinator_update)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle coordinator state change."""
        self.async_write_ha_state()


class SmartLightingAdaptiveSensor(SensorEntity):
    """Sensor showing adaptive timeout metrics.

    Exposes adaptive_factor (multiplier) and activation_count
    (activations in window) for monitoring anti-flicker behavior.
    """

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator,
        entry: ConfigEntry,
        area_name: str,
        key: str,
        name: str,
        prop_name: str,
    ) -> None:
        """Initialize adaptive sensor."""
        self._coordinator = coordinator
        self._prop_name = prop_name
        self._unsub_interval = None

        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_{key}"
        self._attr_name = name
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> float | int:
        """Return current adaptive metric value."""
        return getattr(self._coordinator, self._prop_name, 0)

    async def async_added_to_hass(self) -> None:
        """Start periodic update for live values."""
        self._unsub_interval = async_track_time_interval(
            self.hass,
            self._async_tick,
            timedelta(seconds=5),
        )
        self._coordinator.set_update_callback(self._handle_coordinator_update)

    async def async_will_remove_from_hass(self) -> None:
        """Stop periodic update."""
        if self._unsub_interval:
            self._unsub_interval()
            self._unsub_interval = None

    @callback
    def _async_tick(self, _now=None) -> None:
        """Update sensor value periodically."""
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle coordinator state change."""
        self.async_write_ha_state()


class SmartLightingLuxSensor(SensorEntity):
    """Sensor mirroring the configured lux sensor value [Spec §9].

    Exposes the current ambient light level within the Smart Lighting
    device, updated in real-time via state change tracking on the
    source lux entity.
    """

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_device_class = SensorDeviceClass.ILLUMINANCE
    _attr_native_unit_of_measurement = "lx"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self, coordinator, entry: ConfigEntry, area_name: str
    ) -> None:
        """Initialize lux mirror sensor."""
        self._coordinator = coordinator
        self._entry = entry
        self._unsub_track = None

        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_lux"
        self._attr_name = "Lux"
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> float | None:
        """Return current lux from coordinator."""
        return self._coordinator.current_lux

    async def async_added_to_hass(self) -> None:
        """Track source lux entity for real-time updates."""
        from homeassistant.helpers.event import async_track_state_change_event
        from .const import CONF_LUX_SENSOR

        lux_entity = self._entry.data.get(CONF_LUX_SENSOR)
        if lux_entity:
            self._unsub_track = async_track_state_change_event(
                self.hass,
                [lux_entity],
                self._async_lux_changed,
            )
        # Also listen to coordinator updates
        self._coordinator.set_update_callback(self._handle_coordinator_update)

    async def async_will_remove_from_hass(self) -> None:
        """Stop tracking."""
        if self._unsub_track:
            self._unsub_track()
            self._unsub_track = None

    @callback
    def _async_lux_changed(self, event) -> None:
        """Handle source lux entity state change — update immediately."""
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle coordinator state change."""
        self.async_write_ha_state()
