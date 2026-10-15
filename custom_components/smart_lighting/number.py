"""Number platform for Smart Lighting.

Exposes runtime-adjustable configuration values as number entities.
Changes take effect immediately without requiring integration reload.

Entities: one per runtime parameter (timeouts, warning dim, lux threshold,
adaptive timeout, natural-light auto-off) [Spec §3, §6, §8, §9, §9b, §17].

Each entity exposes a ``description`` attribute: the same help text shown
under the field in the config flow (``data_description``), in the HA
language, English fallback. Excluded from the recorder [Spec §19].
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    EVENT_CORE_CONFIG_UPDATE,
    EntityCategory,
    UnitOfTime,
)
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.translation import async_get_translations

from .const import CONF_AREA_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)

# Attribute carrying the parameter help text [Spec §19]
ATTR_DESCRIPTION = "description"

# Config flow step whose data_description documents each key [Spec §19].
# Only lux_threshold lives in "sensors"; all others are in "timings".
_DESCRIPTION_STEP = {"lux_threshold": "sensors"}


async def _async_load_description(hass: HomeAssistant, key: str) -> str | None:
    """Return the data_description of ``key`` in the HA language.

    Reads the integration's ``config`` translations, so the text is the
    same one shown in the config/options flow. Falls back to English.
    """
    step = _DESCRIPTION_STEP.get(key, "timings")
    tkey = f"component.{DOMAIN}.config.step.{step}.data_description.{key}"
    for language in dict.fromkeys((hass.config.language, "en")):
        translations = await async_get_translations(
            hass, language, "config", [DOMAIN]
        )
        if text := translations.get(tkey):
            return text
    _LOGGER.debug("No description translation for %s", key)
    return None


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
            prop_name="runtime_occupancy_timeout",
            min_value=10, max_value=7200, step=10,
            unit=UnitOfTime.SECONDS,
        ),
        SmartLightingNumber(
            coordinator, entry, area_name,
            key="failsafe_timeout",
            prop_name="runtime_failsafe_timeout",
            min_value=60, max_value=86400, step=60,
            unit=UnitOfTime.SECONDS,
        ),
        SmartLightingNumber(
            coordinator, entry, area_name,
            key="perm_override_timeout",
            prop_name="runtime_perm_override_timeout",
            min_value=60, max_value=86400, step=60,
            unit=UnitOfTime.SECONDS,
        ),
        SmartLightingNumber(
            coordinator, entry, area_name,
            key="temp_override_timeout",
            prop_name="runtime_temp_override_timeout",
            min_value=0, max_value=86400, step=60,
            unit=UnitOfTime.SECONDS,
        ),
        SmartLightingNumber(
            coordinator, entry, area_name,
            key="warning_dim_pct",
            prop_name="runtime_warning_dim_pct",
            min_value=5, max_value=80, step=5,
            unit="%",
        ),
        SmartLightingNumber(
            coordinator, entry, area_name,
            key="warning_dim_duration",
            prop_name="runtime_warning_dim_duration",
            min_value=3, max_value=60, step=1,
            unit=UnitOfTime.SECONDS,
        ),
        SmartLightingNumber(
            coordinator, entry, area_name,
            key="lux_threshold",
            prop_name="runtime_lux_threshold",
            min_value=0, max_value=1000, step=1,
            unit="lx",
        ),
        SmartLightingNumber(
            coordinator, entry, area_name,
            key="adaptive_window",
            prop_name="runtime_adaptive_window",
            min_value=60, max_value=3600, step=60,
            unit=UnitOfTime.SECONDS,
        ),
        SmartLightingNumber(
            coordinator, entry, area_name,
            key="adaptive_threshold",
            prop_name="runtime_adaptive_threshold",
            min_value=2, max_value=20, step=1,
            unit=None,
        ),
        SmartLightingNumber(
            coordinator, entry, area_name,
            key="adaptive_multiplier",
            prop_name="runtime_adaptive_multiplier",
            min_value=1.1, max_value=3.0, step=0.1,
            unit=None,
        ),
        SmartLightingNumber(
            coordinator, entry, area_name,
            key="adaptive_max_factor",
            prop_name="runtime_adaptive_max_factor",
            min_value=1.5, max_value=10.0, step=0.5,
            unit=None,
        ),
        SmartLightingNumber(
            coordinator, entry, area_name,
            key="lux_hysteresis_pct",
            prop_name="runtime_lux_hysteresis_pct",
            min_value=5, max_value=100, step=1,
            unit="%",
        ),
        SmartLightingNumber(
            coordinator, entry, area_name,
            key="lux_hysteresis_time",
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
    # Static help text: keep it out of the recorder database [Spec §19]
    _unrecorded_attributes = frozenset({ATTR_DESCRIPTION})

    def __init__(
        self,
        coordinator,
        entry: ConfigEntry,
        area_name: str,
        key: str,
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
        # Display name from translations: entity.number.<key> [Spec §13]
        self._attr_translation_key = key
        self._attr_device_info = coordinator.device_info
        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value
        self._attr_native_step = step
        if unit:
            self._attr_native_unit_of_measurement = unit
        self._description: str | None = None

    async def async_added_to_hass(self) -> None:
        """Load the help text and reload it when the HA language changes."""
        await self._async_refresh_description()

        @callback
        def _on_core_config_update(event: Event) -> None:
            # Language may have changed in Settings > General [Spec §19]
            self.hass.async_create_task(self._async_refresh_description())

        self.async_on_remove(
            self.hass.bus.async_listen(
                EVENT_CORE_CONFIG_UPDATE, _on_core_config_update
            )
        )

    async def _async_refresh_description(self) -> None:
        """Fetch the localized description and publish it."""
        description = await _async_load_description(self.hass, self._config_key)
        if description != self._description:
            self._description = description
            _LOGGER.debug(
                "Description loaded for %s (%s)",
                self.entity_id, self.hass.config.language,
            )
            if self.hass is not None and self.entity_id:
                self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Expose the parameter help text [Spec §19]."""
        if self._description is None:
            return None
        return {ATTR_DESCRIPTION: self._description}

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
