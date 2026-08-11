"""Light platform for Smart Lighting [Spec §13].

One entity per area. Exposes the state machine as a light entity
with brightness support [Spec §5]. No helper entities [Spec §13].
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_AREA_NAME, DOMAIN
from .coordinator import SmartLightingCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Smart Lighting light from config entry [Spec §13]."""
    coordinator = SmartLightingCoordinator(
        hass, dict(entry.data), entry.entry_id
    )
    hass.data[DOMAIN][entry.entry_id]["coordinator"] = coordinator

    entity = SmartLightingLight(coordinator, entry)
    async_add_entities([entity])


class SmartLightingLight(LightEntity):
    """Representation of a Smart Lighting controller [Spec §13]."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}

    def __init__(
        self,
        coordinator: SmartLightingCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the light entity."""
        self._coordinator = coordinator
        self._entry = entry

        area_name = entry.data.get(CONF_AREA_NAME, "unknown")
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}"
        self._attr_name = None
        self._attr_device_info = coordinator.device_info

    @property
    def is_on(self) -> bool:
        """Return true if light is on [Spec §3]."""
        return self._coordinator.is_on

    @property
    def brightness(self) -> int | None:
        """Return the brightness [Spec §5]."""
        if self._coordinator.is_on:
            return self._coordinator.brightness
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes [Spec §10]."""
        return self._coordinator.extra_state_attributes

    async def async_added_to_hass(self) -> None:
        """Start coordinator when entity is added."""
        self._coordinator.set_update_callback(self._handle_coordinator_update)
        await self._coordinator.async_start()

    async def async_will_remove_from_hass(self) -> None:
        """Stop coordinator when entity is removed."""
        await self._coordinator.async_stop()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on from UI - single press [Spec §10]."""
        self._coordinator._handle_single_press()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off from UI - single press [Spec §10]."""
        self._coordinator._handle_single_press()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
