"""Number platform for Smart Lighting.

Exposes runtime-adjustable configuration values as number entities.
Changes take effect immediately without requiring integration reload.

Entities:
- Occupancy timeout [Spec §3]
- Failsafe timeout [Spec §8]
- Warning dim percentage [Spec §6]
- Warning dim duration [Spec §6]
"""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_AREA_NAME, DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Smart Lighting number entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    area_name = entry.data.get(CONF_AREA_NAME, "unknown")

    entities = [
        SmartLightingNumber(
            coordinator, entry, area_name,
            key="occupancy_timeout",
            name="Occupancy Timeout",
            prop_name="runtime_occupancy_timeout",
            min_value=10, max_value=7200, step=10,
            unit=UnitOfTime.SECONDS,
        ),
        SmartLightingNumber(
            coordinator, entry, area_name,
            key="failsafe_timeout",
            name="Failsafe Timeout",
            prop_name="runtime_failsafe_timeout",
            min_value=60, max_value=86400, step=60,
            unit=UnitOfTime.SECONDS,
        ),
        SmartLightingNumber(
            coordinator, entry, area_name,
            key="perm_override_timeout",
            name="Perm Override Timeout",
            prop_name="runtime_perm_override_timeout",
            min_value=60, max_value=86400, step=60,
            unit=UnitOfTime.SECONDS,
        ),
        SmartLightingNumber(
            coordinator, entry, area_name,
            key="temp_override_timeout",
            name="Temp Override Timeout",
            prop_name="runtime_temp_override_timeout",
            min_value=0, max_value=86400, step=60,
            unit=UnitOfTime.SECONDS,
        ),
        SmartLightingNumber(
            coordinator, entry, area_name,
            key="warning_dim_pct",
            name="Warning Dim Pct",
            prop_name="runtime_warning_dim_pct",
            min_value=5, max_value=80, step=5,
            unit="%",
        ),
        SmartLightingNumber(
            coordinator, entry, area_name,
            key="warning_dim_duration",
            name="Warning Dim Duration",
            prop_name="runtime_warning_dim_duration",
            min_value=3, max_value=60, step=1,
            unit=UnitOfTime.SECONDS,
        ),
        SmartLightingNumber(
            coordinator, entry, area_name,
            key="lux_threshold",
            name="Lux Threshold",
            prop_name="runtime_lux_threshold",
            min_value=0, max_value=1000, step=1,
            unit="lx",
        ),
        SmartLightingNumber(
            coordinator, entry, area_name,
            key="adaptive_window",
            name="Adaptive Window",
            prop_name="runtime_adaptive_window",
            min_value=60, max_value=3600, step=60,
            unit=UnitOfTime.SECONDS,
        ),
        SmartLightingNumber(
            coordinator, entry, area_name,
            key="adaptive_threshold",
            name="Adaptive Threshold",
            prop_name="runtime_adaptive_threshold",
            min_value=2, max_value=20, step=1,
            unit=None,
        ),
        SmartLightingNumber(
            coordinator, entry, area_name,
            key="adaptive_multiplier",
            name="Adaptive Multiplier",
            prop_name="runtime_adaptive_multiplier",
            min_value=1.1, max_value=3.0, step=0.1,
            unit=None,
        ),
        SmartLightingNumber(
            coordinator, entry, area_name,
            key="adaptive_max_factor",
            name="Adaptive Max Factor",
            prop_name="runtime_adaptive_max_factor",
            min_value=1.5, max_value=10.0, step=0.5,
            unit=None,
        ),
        SmartLightingNumber(
            coordinator, entry, area_name,
            key="lux_hysteresis_pct",
            name="Lux Hysteresis Pct",
            prop_name="runtime_lux_hysteresis_pct",
            min_value=5, max_value=100, step=1,
            unit="%",
        ),
        SmartLightingNumber(
            coordinator, entry, area_name,
            key="lux_hysteresis_time",
            name="Lux Hysteresis Time",
            prop_name="runtime_lux_hysteresis_time",
            min_value=1, max_value=30, step=1,
            unit=UnitOfTime.SECONDS,
        ),
    ]

    async_add_entities(entities)


class SmartLightingNumber(NumberEntity):
    """Number entity for runtime-adjustable config value.

    Reads/writes directly to coordinator properties.
    Changes take effect immediately AND persist to config entry
    so values survive HA restarts.
    """

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_entity_category = EntityCategory.CONFIG
    _attr_mode = NumberMode.BOX

    def __init__(
        self,
        coordinator,
        entry: ConfigEntry,
        area_name: str,
        key: str,
        name: str,
        prop_name: str,
        min_value: float,
        max_value: float,
        step: float,
        unit: str | None,
    ) -> None:
        """Initialize number entity.

        Args:
            coordinator: SmartLightingCoordinator instance.
            entry: Config entry (for persistence).
            area_name: Area display name.
            key: Unique key suffix — also used as config entry data key.
            name: Human-readable entity name.
            prop_name: Coordinator property name to read/write.
            min_value: Minimum allowed value.
            max_value: Maximum allowed value.
            step: Step increment.
            unit: Unit of measurement (or None).
        """
        self._coordinator = coordinator
        self._entry = entry
        self._prop_name = prop_name
        self._config_key = key  # matches CONF_* key name

        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_{key}"
        self._attr_name = name
        self._attr_device_info = coordinator.device_info
        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value
        self._attr_native_step = step
        if unit:
            self._attr_native_unit_of_measurement = unit

    @property
    def native_value(self) -> float:
        """Return current value from coordinator."""
        return getattr(self._coordinator, self._prop_name, 0)

    async def async_set_native_value(self, value: float) -> None:
        """Set new value — takes effect immediately and persists.

        Updates the coordinator property for immediate effect,
        then updates the config entry data so the value
        survives HA restarts.
        """
        setattr(self._coordinator, self._prop_name, value)

        # Persist to config entry
        new_data = dict(self._entry.data)
        new_data[self._config_key] = value
        self.hass.config_entries.async_update_entry(
            self._entry, data=new_data
        )

        self.async_write_ha_state()
