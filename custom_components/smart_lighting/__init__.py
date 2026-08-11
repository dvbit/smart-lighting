"""Smart Lighting integration.

Area-based smart lighting automation for Home Assistant [Spec §1].
Architecture: UI only (config_flow), one entity per area,
no helper entities, dynamic runtime updates [Spec §13].

The custom Lovelace card is automatically registered as a
frontend resource on first config entry setup, so the user
does not need to copy files or add resources manually.
"""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.frontend import (
    async_register_built_in_panel,
)
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.LIGHT, Platform.SENSOR, Platform.NUMBER, Platform.BUTTON]

# Frontend card registration constants
CARD_JS = "smart-lighting-card.js"
CARD_URL = f"/{DOMAIN}/{CARD_JS}"
CARD_DIR = Path(__file__).parent / "www"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Smart Lighting component (YAML not supported).

    Registers the static path for the custom card so it is
    served by HA at /smart_lighting/smart-lighting-card.js.
    """
    hass.data.setdefault(DOMAIN, {})

    # Register the www/ directory as a static path
    # This makes files available at /{DOMAIN}/filename
    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL, str(CARD_DIR / CARD_JS), cache_headers=False)]
    )
    _LOGGER.debug("Registered static path: %s -> %s", CARD_URL, CARD_DIR / CARD_JS)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Smart Lighting from a config entry [Spec §13]."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {}

    # Auto-register the card as a Lovelace resource (once)
    await _async_register_card_resource(hass)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    # Support dynamic runtime updates via options [Spec §13]
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def _async_update_listener(
    hass: HomeAssistant, entry: ConfigEntry
) -> None:
    """Handle options update - reload for dynamic config [Spec §13]."""
    await hass.config_entries.async_reload(entry.entry_id)


async def _async_register_card_resource(hass: HomeAssistant) -> None:
    """Register the custom card as a Lovelace frontend resource.

    Only registers once per HA session. The resource URL points
    to the static path served by async_setup above.
    Uses the lovelace resources collection to add the JS module
    so the user doesn't need to manually add it.
    """
    # Check if already registered this session
    if hass.data[DOMAIN].get("card_registered"):
        return

    try:
        # Access the lovelace resources collection
        resources = hass.data.get("lovelace_resources")
        if resources is None:
            # Try loading the resources collection
            from homeassistant.components.lovelace import (
                ResourceStorageCollection,
            )
            resources = hass.data.get("lovelace_resources")

        if resources is not None:
            # Check if already registered in persistent storage
            existing = [
                r
                for r in resources.async_items()
                if CARD_JS in r.get("url", "")
            ]

            if not existing:
                await resources.async_create_item(
                    {"res_type": "module", "url": CARD_URL}
                )
                _LOGGER.info(
                    "Registered Lovelace resource: %s (module)", CARD_URL
                )
            else:
                _LOGGER.debug("Card resource already registered")
        else:
            _LOGGER.warning(
                "Lovelace resources not available. "
                "Add manually: %s as JavaScript Module",
                CARD_URL,
            )

    except Exception:
        _LOGGER.warning(
            "Could not auto-register card resource. "
            "Add manually: %s as JavaScript Module",
            CARD_URL,
        )

    hass.data[DOMAIN]["card_registered"] = True
