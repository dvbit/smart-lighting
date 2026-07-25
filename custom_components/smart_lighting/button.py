"""Button platform for Smart Lighting.

Provides a button to capture the current lux sensor reading
and persist it as the new lux threshold in the config entry [Spec §9].
"""

from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_AREA_NAME,
    CONF_LUX_SENSOR,
    CONF_LUX_THRESHOLD,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Smart Lighting button entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    area_name = entry.data.get(CONF_AREA_NAME, "unknown")

    # Only create the button if a lux sensor is configured [Spec §9]
    if entry.data.get(CONF_LUX_SENSOR):
        async_add_entities(
            [SmartLightingSetLuxThresholdButton(coordinator, entry, area_name)]
        )


class SmartLightingSetLuxThresholdButton(ButtonEntity):
    """Button to set the lux threshold to the current sensor reading.

    Reads the current state of the configured lux sensor and
    persists it as the new lux_threshold in the config entry [Spec §9].
    The coordinator picks up the new value immediately on next check.
    """

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:brightness-auto"

    def __init__(
        self,
        coordinator,
        entry: ConfigEntry,
        area_name: str,
    ) -> None:
        """Initialize the button entity."""
        self._coordinator = coordinator
        self._entry = entry

        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_set_lux_threshold"
        self._attr_name = "Set Lux Threshold"
        self._attr_device_info = coordinator.device_info

    async def async_press(self) -> None:
        """Handle button press: capture current lux and persist.

        Reads the lux sensor state, updates the config entry data
        with the new threshold, and updates the coordinator config
        so the new value takes effect immediately [Spec §9].
        """
        lux_entity = self._entry.data.get(CONF_LUX_SENSOR)
        if not lux_entity:
            _LOGGER.warning("No lux sensor configured, ignoring press")
            return

        state = self.hass.states.get(lux_entity)
        if state is None:
            _LOGGER.warning("Lux sensor %s not available", lux_entity)
            return

        try:
            lux_value = round(float(state.state))
        except (ValueError, TypeError):
            _LOGGER.warning(
                "Lux sensor %s has non-numeric state: %s",
                lux_entity, state.state,
            )
            return

        # Persist in config entry [Spec §14]
        new_data = dict(self._entry.data)
        new_data[CONF_LUX_THRESHOLD] = lux_value
        self.hass.config_entries.async_update_entry(
            self._entry, data=new_data
        )

        # Update coordinator config for immediate effect [Spec §9]
        self._coordinator.config[CONF_LUX_THRESHOLD] = lux_value

        _LOGGER.info(
            "Lux threshold updated to %d from sensor %s",
            lux_value, lux_entity,
        )
