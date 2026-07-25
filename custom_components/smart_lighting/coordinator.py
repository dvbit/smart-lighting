"""Coordinator for Smart Lighting - core state machine.

Implements the state machine described in the Smart Lighting Specification v1.0.
Each method references the relevant specification section as [Spec §N].

State machine transitions:
    IDLE -> ACTIVE        : motion + lux < threshold [Spec §3]
    ACTIVE -> WARNING     : occupancy timeout expires [Spec §3, §6]
    WARNING -> IDLE       : dim sequence completes [Spec §6]
    WARNING -> ACTIVE     : motion or occupancy detected [Spec §6, §7]
    ACTIVE -> TEMP_OVERRIDE  : single press (clicks=1) [Spec §10]
    ACTIVE -> PERM_OVERRIDE  : double press (clicks=2) [Spec §10]
    TEMP_OVERRIDE -> IDLE : occupancy cycle completes [Spec §11]
    PERM_OVERRIDE -> IDLE : double press or timeout [Spec §11]
    ANY -> IDLE           : failsafe timeout [Spec §8]
"""

from __future__ import annotations

import asyncio
from datetime import time
import logging
from typing import Any

from homeassistant.const import (
    STATE_ON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import (
    CALLBACK_TYPE,
    Event,
    HomeAssistant,
    State,
    callback,
)
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_interval,
)
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    CONF_ADAPTIVE_MAX_FACTOR,
    CONF_ADAPTIVE_MULTIPLIER,
    CONF_ADAPTIVE_THRESHOLD,
    CONF_ADAPTIVE_WINDOW,
    CONF_AREA_NAME,
    CONF_BRIGHTNESS_NORMAL,
    CONF_BRIGHTNESS_SOFT,
    CONF_BULB_ENTITY,
    CONF_CLICK_TIME_WINDOW,
    CONF_FAILSAFE_TIMEOUT,
    CONF_LUX_HYSTERESIS_PCT,
    CONF_LUX_HYSTERESIS_TIME,
    CONF_LUX_SENSOR,
    CONF_LUX_THRESHOLD,
    CONF_MONITORED_SWITCH,
    CONF_MOTION_SENSORS,
    CONF_OCCUPANCY_SENSOR,
    CONF_OCCUPANCY_TIMEOUT,
    CONF_PERM_OVERRIDE_TIMEOUT,
    CONF_PROFILE_MODE,
    CONF_RELAY_ENTITY,
    CONF_SOFT_BULB_ENTITY,
    CONF_SOFT_ENTITY,
    CONF_SOFT_RELAY_ENTITY,
    CONF_SOFT_TIME_END,
    CONF_SOFT_TIME_START,
    CONF_SUSPEND_ENTITY,
    CONF_TEMP_OVERRIDE_TIMEOUT,
    CONF_WARNING_DIM_DURATION,
    CONF_WARNING_DIM_PCT,
    CONF_NO_MOTION_TIMEOUT,
    DEFAULT_ADAPTIVE_MAX_FACTOR,
    DEFAULT_ADAPTIVE_MULTIPLIER,
    DEFAULT_ADAPTIVE_THRESHOLD,
    DEFAULT_ADAPTIVE_WINDOW,
    DEFAULT_BRIGHTNESS_NORMAL,
    DEFAULT_BRIGHTNESS_SOFT,
    DEFAULT_CLICK_TIME_WINDOW,
    DEFAULT_FAILSAFE_TIMEOUT,
    DEFAULT_LUX_HYSTERESIS_PCT,
    DEFAULT_LUX_HYSTERESIS_TIME,
    DEFAULT_LUX_THRESHOLD,
    DEFAULT_OCCUPANCY_TIMEOUT,
    DEFAULT_PERM_OVERRIDE_TIMEOUT,
    DEFAULT_TEMP_OVERRIDE_TIMEOUT,
    DEFAULT_WARNING_DIM_DURATION,
    DEFAULT_WARNING_DIM_PCT,
    DEFAULT_NO_MOTION_TIMEOUT,
    DOMAIN,
    PERSIST_LAST_MANUAL_ACTION,
    PERSIST_OVERRIDE_STATE,
    PROFILE_MODE_ENTITY,
    PROFILE_MODE_TIME,
    STATE_ACTIVE,
    STATE_IDLE,
    STATE_PERM_OVERRIDE,
    STATE_SUSPENDED,
    STATE_TEMP_OVERRIDE,
    STATE_WARNING,
)

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1


class SmartLightingCoordinator:
    """Coordinate smart lighting state machine.

    Central controller that listens to sensor events and drives actuators
    according to the rules defined in the specification. One instance
    per configured area [Spec §13].
    """

    def __init__(
        self,
        hass: HomeAssistant,
        config: dict[str, Any],
        entry_id: str,
    ) -> None:
        """Initialize coordinator."""
        self.hass = hass
        self.config = config
        self.entry_id = entry_id

        # ── State machine [Spec §3] ──────────────────────────────
        self._state: str = STATE_IDLE
        self._is_on: bool = False
        self._brightness: int = 0

        # ── Timers [Spec §3, §6, §8] ─────────────────────────────
        self._occupancy_timer: asyncio.TimerHandle | None = None
        self._failsafe_timer: asyncio.TimerHandle | None = None
        self._warning_task: asyncio.Task[None] | None = None
        self._perm_override_timer: asyncio.TimerHandle | None = None

        # ── Timer remaining tracking (for sensor entities) ────────
        self._occupancy_timer_end: float | None = None
        self._failsafe_timer_end: float | None = None
        self._perm_override_timer_end: float | None = None
        self._warning_start: float | None = None

        # ── Runtime-adjustable config values (number entities) ────
        self._runtime_occupancy_timeout: float = float(
            config.get(CONF_OCCUPANCY_TIMEOUT, DEFAULT_OCCUPANCY_TIMEOUT)
        )
        self._runtime_failsafe_timeout: float = float(
            config.get(CONF_FAILSAFE_TIMEOUT, DEFAULT_FAILSAFE_TIMEOUT)
        )
        self._runtime_perm_override_timeout: float = float(
            config.get(CONF_PERM_OVERRIDE_TIMEOUT, DEFAULT_PERM_OVERRIDE_TIMEOUT)
        )
        self._runtime_warning_dim_pct: float = float(
            config.get(CONF_WARNING_DIM_PCT, DEFAULT_WARNING_DIM_PCT)
        )
        self._runtime_warning_dim_duration: float = float(
            config.get(CONF_WARNING_DIM_DURATION, DEFAULT_WARNING_DIM_DURATION)
        )
        self._runtime_no_motion_timeout: float = float(
            config.get(CONF_NO_MOTION_TIMEOUT, DEFAULT_NO_MOTION_TIMEOUT)
        )

        # ── Listeners ─────────────────────────────────────────────
        self._unsub_listeners: list[CALLBACK_TYPE] = []

        # ── Persistence [Spec §14] ───────────────────────────────
        self._store = Store[dict[str, Any]](
            hass, STORAGE_VERSION, f"{DOMAIN}.{entry_id}"
        )
        self._persisted_data: dict[str, Any] = {}

        # ── Entity notification callbacks ────────────────────────
        self._update_callbacks: list[CALLBACK_TYPE] = []

        # ── Adaptive timeout (anti-flickering) ────────────────────
        # Tracks activation timestamps within the rolling window
        self._activation_timestamps: list[float] = []
        self._adaptive_factor: float = 1.0

        # ── Natural Light Auto-Off [Spec §9b] ────────────────────
        self._lux_high_since: float | None = None  # timestamp when lux exceeded

        # ── Suspend [Spec §15] ────────────────────────────────────
        self._suspended: bool = False
        self._pre_suspend_state: str | None = None

        # ── Embedded click detection [Spec §10] ──────────────────
        self._click_count: int = 0
        self._click_timer: asyncio.TimerHandle | None = None
        self._last_interaction_type: str = "Unknown"
        self._last_acting_user: str = "Unknown"
        self._click_time_window: float = float(
            config.get(CONF_CLICK_TIME_WINDOW, DEFAULT_CLICK_TIME_WINDOW)
        )

        # ── Temp override timer [Spec §10] ───────────────────────
        self._temp_override_timer: asyncio.TimerHandle | None = None
        self._temp_override_timer_end: float | None = None
        self._runtime_temp_override_timeout: float = float(
            config.get(CONF_TEMP_OVERRIDE_TIMEOUT, DEFAULT_TEMP_OVERRIDE_TIMEOUT)
        )

        # ── No-motion fallback timer [Spec §16] ─────────────────
        self._no_motion_timer: asyncio.TimerHandle | None = None
        self._no_motion_timer_end: float | None = None
        self._last_motion_time: float = 0.0

    # ── Properties ───────────────────────────────────────────────

    @property
    def state(self) -> str:
        """Return current state machine state."""
        return self._state

    @property
    def is_on(self) -> bool:
        """Return whether the light should be on."""
        return self._is_on

    @property
    def brightness(self) -> int:
        """Return current brightness [Spec §5]."""
        return self._brightness

    @property
    def current_profile(self) -> str:
        """Return current profile name [Spec §12]."""
        return "soft" if self._is_soft_profile_active() else "normal"

    @property
    def current_lux(self) -> float | None:
        """Return current lux reading from the configured lux sensor."""
        lux_entity = self.config.get(CONF_LUX_SENSOR)
        if not lux_entity:
            return None
        lux_state = self.hass.states.get(lux_entity)
        if lux_state is None:
            return None
        try:
            return float(lux_state.state)
        except (ValueError, TypeError):
            return None

    @property
    def device_info(self):
        """Return device info for grouping all entities under one device."""
        from homeassistant.helpers.device_registry import DeviceInfo

        area_name = self.config.get(
            CONF_AREA_NAME, "Unknown"
        )
        return DeviceInfo(
            identifiers={(DOMAIN, self.entry_id)},
            name=f"Smart Lighting {area_name}",
            manufacturer="Smart Lighting",
            model="Area Controller",
            sw_version="3.3.1",
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes exposing state machine internals.

        Includes motion, occupancy, and lux status so the custom
        card can read them without needing separate config.
        """
        lux_entity = self.config.get(CONF_LUX_SENSOR)
        lux_value = None
        if lux_entity:
            lux_state = self.hass.states.get(lux_entity)
            if lux_state is not None:
                try:
                    lux_value = float(lux_state.state)
                except (ValueError, TypeError):
                    pass

        threshold = float(
            self.config.get(CONF_LUX_THRESHOLD, DEFAULT_LUX_THRESHOLD)
        )

        return {
            "smart_lighting_state": self._state,
            "override_active": self._state
            in (STATE_TEMP_OVERRIDE, STATE_PERM_OVERRIDE),
            "motion_active": self._any_motion_active(),
            "occupancy_active": self._is_occupied(),
            "lux_value": lux_value,
            "lux_threshold": threshold,
            "lux_sufficient": (
                lux_value >= threshold if lux_value is not None else False
            ),
            "profile": self.current_profile,
            # Source entity IDs for card more-info popups
            "motion_sensors": self.config.get(CONF_MOTION_SENSORS, []),
            "occupancy_sensor": self.config.get(CONF_OCCUPANCY_SENSOR, ""),
            "lux_sensor": self.config.get(CONF_LUX_SENSOR, ""),
        }

    # ── Timer remaining seconds (for sensor entities) ────────────

    @property
    def occupancy_timer_remaining(self) -> float:
        """Return seconds remaining on occupancy timer."""
        if self._occupancy_timer_end is None:
            return 0.0
        remaining = self._occupancy_timer_end - self.hass.loop.time()
        return max(0.0, round(remaining, 1))

    @property
    def failsafe_timer_remaining(self) -> float:
        """Return seconds remaining on failsafe timer."""
        if self._failsafe_timer_end is None:
            return 0.0
        remaining = self._failsafe_timer_end - self.hass.loop.time()
        return max(0.0, round(remaining, 1))

    @property
    def perm_override_timer_remaining(self) -> float:
        """Return seconds remaining on perm override timer."""
        if self._perm_override_timer_end is None:
            return 0.0
        remaining = self._perm_override_timer_end - self.hass.loop.time()
        return max(0.0, round(remaining, 1))

    @property
    def temp_override_timer_remaining(self) -> float:
        """Return seconds remaining on temp override timer (0 if no timeout)."""
        if self._temp_override_timer_end is None:
            return 0.0
        remaining = self._temp_override_timer_end - self.hass.loop.time()
        return max(0.0, round(remaining, 1))

    @property
    def active_override_timer_remaining(self) -> float:
        """Return remaining seconds on whichever override timer is active."""
        if self._state == STATE_PERM_OVERRIDE:
            return self.perm_override_timer_remaining
        if self._state == STATE_TEMP_OVERRIDE:
            return self.temp_override_timer_remaining
        return 0.0

    @property
    def warning_timer_remaining(self) -> float:
        """Return seconds remaining on warning dim sequence."""
        if self._warning_start is None or self._state != STATE_WARNING:
            return 0.0
        total = self._runtime_warning_dim_duration
        elapsed = self.hass.loop.time() - self._warning_start
        return max(0.0, round(total - elapsed, 1))

    # ── Click detection properties [Spec §10] ────────────────────

    @property
    def click_count(self) -> int:
        """Return current click count in active window."""
        return self._click_count

    @property
    def interaction_type(self) -> str:
        """Return last interaction type: Physical/Automation/UI."""
        return self._last_interaction_type

    @property
    def acting_user(self) -> str:
        """Return last acting user or 'Physical'."""
        return self._last_acting_user

    @property
    def click_time_window(self) -> float:
        """Return configured click time window."""
        return self._click_time_window

    # ── Adaptive timeout properties ──────────────────────────────

    @property
    def adaptive_factor(self) -> float:
        """Return current adaptive timeout multiplier."""
        return round(self._adaptive_factor, 2)

    @property
    def activation_count(self) -> int:
        """Return number of activations within the adaptive window."""
        self._prune_activation_timestamps()
        return len(self._activation_timestamps)

    @property
    def effective_occupancy_timeout(self) -> float:
        """Return occupancy timeout adjusted by adaptive factor."""
        return round(
            self._runtime_occupancy_timeout * self._adaptive_factor, 1
        )

    # ── Runtime config access (for number entities) ──────────────

    @property
    def runtime_occupancy_timeout(self) -> float:
        """Return current runtime occupancy timeout value."""
        return self._runtime_occupancy_timeout

    @runtime_occupancy_timeout.setter
    def runtime_occupancy_timeout(self, value: float) -> None:
        """Set runtime occupancy timeout."""
        self._runtime_occupancy_timeout = value

    @property
    def runtime_failsafe_timeout(self) -> float:
        """Return current runtime failsafe timeout value."""
        return self._runtime_failsafe_timeout

    @runtime_failsafe_timeout.setter
    def runtime_failsafe_timeout(self, value: float) -> None:
        """Set runtime failsafe timeout."""
        self._runtime_failsafe_timeout = value

    @property
    def runtime_perm_override_timeout(self) -> float:
        """Return current runtime perm override timeout value [Spec §11]."""
        return self._runtime_perm_override_timeout

    @runtime_perm_override_timeout.setter
    def runtime_perm_override_timeout(self, value: float) -> None:
        """Set runtime perm override timeout [Spec §11]."""
        self._runtime_perm_override_timeout = value

    @property
    def runtime_temp_override_timeout(self) -> float:
        """Return current runtime temp override timeout [Spec §10]."""
        return self._runtime_temp_override_timeout

    @runtime_temp_override_timeout.setter
    def runtime_temp_override_timeout(self, value: float) -> None:
        """Set runtime temp override timeout (0=no timeout) [Spec §10]."""
        self._runtime_temp_override_timeout = value

    @property
    def runtime_warning_dim_pct(self) -> float:
        """Return current warning dim percentage [Spec §6]."""
        return self._runtime_warning_dim_pct

    @runtime_warning_dim_pct.setter
    def runtime_warning_dim_pct(self, value: float) -> None:
        """Set warning dim percentage."""
        self._runtime_warning_dim_pct = value

    @property
    def runtime_warning_dim_duration(self) -> float:
        """Return current warning dim duration [Spec §6]."""
        return self._runtime_warning_dim_duration

    @runtime_warning_dim_duration.setter
    def runtime_warning_dim_duration(self, value: float) -> None:
        """Set warning dim duration."""
        self._runtime_warning_dim_duration = value

    @property
    def runtime_no_motion_timeout(self) -> float:
        """Return current no-motion fallback timeout [Spec §16]."""
        return self._runtime_no_motion_timeout

    @runtime_no_motion_timeout.setter
    def runtime_no_motion_timeout(self, value: float) -> None:
        """Set no-motion fallback timeout."""
        self._runtime_no_motion_timeout = value

    @property
    def runtime_lux_threshold(self) -> float:
        """Return current runtime lux threshold [Spec §9]."""
        return float(self.config.get(CONF_LUX_THRESHOLD, DEFAULT_LUX_THRESHOLD))

    @runtime_lux_threshold.setter
    def runtime_lux_threshold(self, value: float) -> None:
        """Set runtime lux threshold and persist [Spec §9]."""
        self.config[CONF_LUX_THRESHOLD] = value

    @property
    def runtime_adaptive_window(self) -> float:
        """Return adaptive window value."""
        return float(self.config.get(CONF_ADAPTIVE_WINDOW, DEFAULT_ADAPTIVE_WINDOW))

    @runtime_adaptive_window.setter
    def runtime_adaptive_window(self, value: float) -> None:
        """Set adaptive window."""
        self.config[CONF_ADAPTIVE_WINDOW] = value

    @property
    def runtime_adaptive_threshold(self) -> float:
        """Return adaptive threshold value."""
        return float(self.config.get(CONF_ADAPTIVE_THRESHOLD, DEFAULT_ADAPTIVE_THRESHOLD))

    @runtime_adaptive_threshold.setter
    def runtime_adaptive_threshold(self, value: float) -> None:
        """Set adaptive threshold."""
        self.config[CONF_ADAPTIVE_THRESHOLD] = value

    @property
    def runtime_adaptive_multiplier(self) -> float:
        """Return adaptive multiplier value."""
        return float(self.config.get(CONF_ADAPTIVE_MULTIPLIER, DEFAULT_ADAPTIVE_MULTIPLIER))

    @runtime_adaptive_multiplier.setter
    def runtime_adaptive_multiplier(self, value: float) -> None:
        """Set adaptive multiplier."""
        self.config[CONF_ADAPTIVE_MULTIPLIER] = value

    @property
    def runtime_adaptive_max_factor(self) -> float:
        """Return adaptive max factor value."""
        return float(self.config.get(CONF_ADAPTIVE_MAX_FACTOR, DEFAULT_ADAPTIVE_MAX_FACTOR))

    @runtime_adaptive_max_factor.setter
    def runtime_adaptive_max_factor(self, value: float) -> None:
        """Set adaptive max factor."""
        self.config[CONF_ADAPTIVE_MAX_FACTOR] = value

    @property
    def runtime_lux_hysteresis_pct(self) -> float:
        """Return lux hysteresis percentage [Spec §9b]."""
        return float(self.config.get(CONF_LUX_HYSTERESIS_PCT, DEFAULT_LUX_HYSTERESIS_PCT))

    @runtime_lux_hysteresis_pct.setter
    def runtime_lux_hysteresis_pct(self, value: float) -> None:
        """Set lux hysteresis percentage."""
        self.config[CONF_LUX_HYSTERESIS_PCT] = value

    @property
    def runtime_lux_hysteresis_time(self) -> float:
        """Return lux hysteresis time [Spec §9b]."""
        return float(self.config.get(CONF_LUX_HYSTERESIS_TIME, DEFAULT_LUX_HYSTERESIS_TIME))

    @runtime_lux_hysteresis_time.setter
    def runtime_lux_hysteresis_time(self, value: float) -> None:
        """Set lux hysteresis time."""
        self.config[CONF_LUX_HYSTERESIS_TIME] = value

    def set_update_callback(self, callback_fn: CALLBACK_TYPE) -> None:
        """Register a callback to notify entities of state changes.

        Multiple entities can register callbacks; all will be
        called on state updates.
        """
        if callback_fn not in self._update_callbacks:
            self._update_callbacks.append(callback_fn)

    # ── Lifecycle ────────────────────────────────────────────────

    async def async_start(self) -> None:
        """Start the coordinator: restore state and subscribe to events."""
        await self._async_load_persisted()
        self._setup_listeners()

    async def async_stop(self) -> None:
        """Stop the coordinator: cancel timers, unsubscribe, persist."""
        self._cancel_all_timers()
        for unsub in self._unsub_listeners:
            unsub()
        self._unsub_listeners.clear()
        await self._async_save_persisted()

    # ── Persistence [Spec §14] ───────────────────────────────────

    async def _async_load_persisted(self) -> None:
        """Load persisted data [Spec §14]."""
        data = await self._store.async_load()
        if data:
            self._persisted_data = data
            override = data.get(PERSIST_OVERRIDE_STATE)
            if override in (STATE_PERM_OVERRIDE, STATE_TEMP_OVERRIDE):
                self._state = override
                _LOGGER.debug("Restored override state: %s", override)

    async def _async_save_persisted(self) -> None:
        """Save state for persistence [Spec §14]."""
        self._persisted_data[PERSIST_OVERRIDE_STATE] = self._state
        self._persisted_data[PERSIST_LAST_MANUAL_ACTION] = (
            dt_util.utcnow().isoformat()
        )
        await self._store.async_save(self._persisted_data)

    # ── Listeners [Spec §2] ──────────────────────────────────────

    def _setup_listeners(self) -> None:
        """Subscribe to state changes for all configured entities."""
        entities_to_track: list[str] = []

        motion_sensors = self.config.get(CONF_MOTION_SENSORS, [])
        entities_to_track.extend(motion_sensors)

        occupancy = self.config.get(CONF_OCCUPANCY_SENSOR)
        if occupancy:
            entities_to_track.append(occupancy)

        lux = self.config.get(CONF_LUX_SENSOR)
        if lux:
            entities_to_track.append(lux)

        interaction = self.config.get(CONF_MONITORED_SWITCH)
        if interaction:
            entities_to_track.append(interaction)

        soft_entity = self.config.get(CONF_SOFT_ENTITY)
        if soft_entity:
            entities_to_track.append(soft_entity)

        suspend_entity = self.config.get(CONF_SUSPEND_ENTITY)
        if suspend_entity:
            entities_to_track.append(suspend_entity)

        if entities_to_track:
            self._unsub_listeners.append(
                async_track_state_change_event(
                    self.hass, entities_to_track, self._async_state_changed
                )
            )

    @callback
    def _async_state_changed(self, event: Event) -> None:
        """Route state change events to the appropriate handler."""
        entity_id = event.data.get("entity_id", "")
        new_state: State | None = event.data.get("new_state")
        old_state: State | None = event.data.get("old_state")

        if new_state is None or new_state.state in (
            STATE_UNAVAILABLE,
            STATE_UNKNOWN,
        ):
            return

        motion_sensors = self.config.get(CONF_MOTION_SENSORS, [])
        occupancy = self.config.get(CONF_OCCUPANCY_SENSOR)
        lux = self.config.get(CONF_LUX_SENSOR)
        monitored = self.config.get(CONF_MONITORED_SWITCH)
        suspend = self.config.get(CONF_SUSPEND_ENTITY)

        # Suspend entity is always handled, even when suspended [Spec §15]
        if entity_id == suspend:
            self._handle_suspend(new_state)
            return

        # When suspended, ignore all other events [Spec §15]
        if self._suspended:
            return

        if entity_id in motion_sensors:
            self._handle_motion(new_state)
        elif entity_id == occupancy:
            self._handle_occupancy(new_state)
        elif entity_id == lux:
            self._handle_lux(new_state)
        elif entity_id == monitored:
            self._handle_monitored_switch(event)

    # ── Motion Handling [Spec §7] ────────────────────────────────

    @callback
    def _handle_motion(self, state: State) -> None:
        """Handle motion sensor state change [Spec §7, §8, §16].

        Motion always resets and restarts the failsafe timer,
        even during override states. Failsafe protects against
        a stuck occupancy sensor [Spec §8].
        Also resets the no-motion fallback timer [Spec §16].
        Always notifies update so card icons reflect current state.
        """
        is_motion = state.state == STATE_ON

        if not is_motion:
            # Motion OFF: start no-motion fallback timer if active [Spec §16]
            if self._state == STATE_ACTIVE:
                self._start_no_motion_timer()
            self._notify_update()
            return

        _LOGGER.debug("Motion detected, current state: %s", self._state)

        # Motion always resets occupancy timer [Spec §7]
        self._cancel_occupancy_timer()

        # Reset no-motion fallback [Spec §16]
        self._cancel_no_motion_timer()
        self._last_motion_time = self.hass.loop.time()

        # Failsafe resets on every motion [Spec §8]
        self._start_failsafe_timer()

        # Cancel warning if active [Spec §7]
        if self._state == STATE_WARNING:
            self._cancel_warning()

        # In override states, motion is ignored for activation [Spec §10]
        if self._state in (STATE_TEMP_OVERRIDE, STATE_PERM_OVERRIDE):
            self._notify_update()
            return

        # Check lux threshold [Spec §3, §9]
        if not self._is_lux_below_threshold():
            self._notify_update()
            return

        # Activate if idle or was in warning [Spec §3]
        if self._state in (STATE_IDLE, STATE_WARNING):
            self._activate()

    # ── Occupancy Handling [Spec §3, §11] ────────────────────────

    @callback
    def _handle_occupancy(self, state: State) -> None:
        """Handle occupancy sensor state change [Spec §3].

        During override states, occupancy changes are ignored.
        Always notifies update so card icons reflect current state.
        """
        is_occupied = state.state == STATE_ON

        # In override states, occupancy is ignored [Spec §10]
        if self._state in (STATE_TEMP_OVERRIDE, STATE_PERM_OVERRIDE):
            self._notify_update()
            return

        if is_occupied:
            self._cancel_occupancy_timer()
            if self._state == STATE_WARNING:
                self._cancel_warning()
                self._state = STATE_ACTIVE
            self._notify_update()
        else:
            if self._state == STATE_ACTIVE:
                self._start_occupancy_timer()
            self._notify_update()

    # ── Lux Handling [Spec §9] ───────────────────────────────────

    @callback
    def _handle_lux(self, state: State) -> None:
        """Handle lux sensor state change [Spec §9, §9b].

        §9: If active and lux >= threshold and not occupied, deactivate.
        §9b: Natural Light Auto-Off: if active, normal profile,
             not override, and lux exceeds threshold×(1+pct/100)
             for hysteresis_time seconds, deactivate (windows opened).
        """
        if self._state in (STATE_TEMP_OVERRIDE, STATE_PERM_OVERRIDE):
            self._lux_high_since = None
            return

        try:
            lux_value = float(state.state)
        except (ValueError, TypeError):
            return

        threshold = float(
            self.config.get(CONF_LUX_THRESHOLD, DEFAULT_LUX_THRESHOLD)
        )

        # §9: Standard lux check
        if self._state == STATE_ACTIVE and lux_value >= threshold:
            if not self._is_occupied():
                _LOGGER.debug(
                    "Lux above threshold and not occupied, deactivating"
                )
                self._lux_high_since = None
                self._deactivate()
                return

        # §9b: Natural Light Auto-Off (only active + normal profile)
        if self._state == STATE_ACTIVE and not self._is_soft_profile_active():
            pct = float(
                self.config.get(
                    CONF_LUX_HYSTERESIS_PCT, DEFAULT_LUX_HYSTERESIS_PCT
                )
            )
            high_threshold = threshold * (1.0 + pct / 100.0)
            hysteresis_time = float(
                self.config.get(
                    CONF_LUX_HYSTERESIS_TIME, DEFAULT_LUX_HYSTERESIS_TIME
                )
            )

            if lux_value >= high_threshold:
                now = self.hass.loop.time()
                if self._lux_high_since is None:
                    # Start counting
                    self._lux_high_since = now
                    _LOGGER.debug(
                        "Lux %.0f >= high threshold %.0f, "
                        "starting hysteresis (%.0fs)",
                        lux_value, high_threshold, hysteresis_time,
                    )
                elif (now - self._lux_high_since) >= hysteresis_time:
                    # Hysteresis elapsed, natural light is sufficient
                    _LOGGER.info(
                        "Natural light auto-off: lux %.0f above %.0f "
                        "for %.0fs [Spec §9b]",
                        lux_value, high_threshold, hysteresis_time,
                    )
                    self._lux_high_since = None
                    self._deactivate()
            else:
                # Lux dropped back below high threshold, reset
                self._lux_high_since = None
        else:
            self._lux_high_since = None

        # Always notify so lux_sufficient attribute updates in card
        self._notify_update()

    # ── Suspend [Spec §15] ───────────────────────────────────────

    @callback
    def _handle_suspend(self, state: State) -> None:
        """Handle suspend entity state change [Spec §15].

        ON: suspend all automation, cancel timers, freeze state.
        OFF: resume, re-evaluate conditions.
        """
        is_suspended = state.state == STATE_ON

        if is_suspended and not self._suspended:
            # Entering suspend mode
            _LOGGER.info("Suspend activated [Spec §15]")
            self._suspended = True
            self._pre_suspend_state = self._state
            self._cancel_all_timers()
            self._state = STATE_SUSPENDED
            self._notify_update()

        elif not is_suspended and self._suspended:
            # Exiting suspend mode - re-evaluate conditions
            _LOGGER.info("Suspend deactivated, re-evaluating [Spec §15]")
            self._suspended = False
            self._state = STATE_IDLE

            # Re-evaluate: if motion+lux conditions met, activate
            if (
                self._any_motion_active()
                and self._is_lux_below_threshold()
            ):
                self._activate()
            else:
                self._deactivate()

    # ── Manual Override [Spec §10] ───────────────────────────────

    @callback
    def _handle_monitored_switch(self, event: Event) -> None:
        """Handle monitored switch state change [Spec §10].

        Analyzes the event context to determine the interaction type:
        - context.user_id is None → Physical (wall switch)
        - context.user_id is set → UI or Automation
        Only Physical interactions are counted for override detection.
        Click counting uses a time window to distinguish single/double press.
        """
        new_state: State | None = event.data.get("new_state")
        old_state: State | None = event.data.get("old_state")
        if new_state is None or old_state is None:
            _LOGGER.debug("Monitored switch: missing old/new state, ignoring")
            return

        # Skip if state didn't actually change
        if new_state.state == old_state.state:
            _LOGGER.debug(
                "Monitored switch: state unchanged (%s), ignoring",
                new_state.state,
            )
            return

        # Determine interaction type from context [Spec §10]
        context = new_state.context
        user_id = context.user_id if context else None
        parent_id = context.parent_id if context else None

        _LOGGER.debug(
            "Monitored switch event: %s → %s, context.user_id=%s, "
            "context.parent_id=%s",
            old_state.state, new_state.state, user_id, parent_id,
        )

        if user_id is None:
            # No user_id → Physical interaction (wall switch)
            interaction_type = "Physical"
            acting_user = "Physical"
        else:
            # Has user_id → check if it's a person or automation
            if parent_id is not None:
                interaction_type = "Automation"
                acting_user = str(user_id)
            else:
                interaction_type = "UI"
                acting_user = str(user_id)

        # Update exposed state
        self._last_interaction_type = interaction_type
        self._last_acting_user = acting_user

        _LOGGER.info(
            "Monitored switch: type=%s, user=%s, current_clicks=%d",
            interaction_type, acting_user, self._click_count,
        )

        # Only count Physical interactions for override [Spec §10]
        if interaction_type != "Physical":
            _LOGGER.debug("Non-physical interaction, ignoring for override")
            self._notify_update()
            return

        # ── Click counting with time window ──────────────────
        self._click_count += 1
        _LOGGER.info(
            "Physical click counted: total=%d, window=%.1fs",
            self._click_count, self._click_time_window,
        )

        # Cancel previous click timer
        if self._click_timer is not None:
            self._click_timer.cancel()
            self._click_timer = None

        # Start new timer: after window expires, evaluate clicks
        self._click_timer = self.hass.loop.call_later(
            self._click_time_window,
            lambda: self.hass.async_create_task(
                self._async_evaluate_clicks()
            ),
        )
        self._notify_update()

    async def _async_evaluate_clicks(self) -> None:
        """Evaluate accumulated click count after time window [Spec §10].

        1 click → temp override (single press)
        2 clicks → perm override (double press)
        3+ clicks → ignored (accidental)
        """
        clicks = self._click_count
        self._click_count = 0
        self._click_timer = None

        _LOGGER.info(
            "Click window expired: %d clicks, state=%s, is_on=%s",
            clicks, self._state, self._is_on,
        )

        if clicks == 1:
            _LOGGER.info("Executing single press → temp override")
            self._handle_single_press()
        elif clicks == 2:
            _LOGGER.info("Executing double press → perm override")
            self._handle_double_press()
        else:
            _LOGGER.debug("Ignoring %d clicks (accidental)", clicks)

        self._notify_update()

    @callback
    def _handle_single_press(self) -> None:
        """Handle single press - temporary override [Spec §10].

        Toggles the light and freezes in temp_override state.
        Exits only on: another single click, or timeout (if configured).
        No occupancy cycle detection — override stays until explicit exit.
        """
        if self._state == STATE_TEMP_OVERRIDE:
            # Exit temp override on single press [Spec §10]
            _LOGGER.info("Exiting temp override via single press")
            self._cancel_temp_override_timer()
            self._state = STATE_IDLE
            # Re-evaluate: if motion+lux, reactivate normally
            if self._any_motion_active() and self._is_lux_below_threshold():
                self._activate()
            else:
                self._deactivate()
        elif self._is_on:
            # Light on → turn off in override
            self._state = STATE_TEMP_OVERRIDE
            self._cancel_all_timers()
            self._deactivate()
            self._start_temp_override_timer()
        else:
            # Light off → turn on in override
            self._state = STATE_TEMP_OVERRIDE
            self._cancel_all_timers()
            self._is_on = True
            self._brightness = self._get_current_brightness()
            self._actuate_on()
            self._start_temp_override_timer()

        self._notify_update()

    @callback
    def _handle_double_press(self) -> None:
        """Handle double press - permanent override toggle [Spec §10]."""
        if self._state == STATE_PERM_OVERRIDE:
            self._cancel_perm_override_timer()
            self._state = STATE_IDLE
            if self._any_motion_active() and self._is_lux_below_threshold():
                self._activate()
            else:
                self._deactivate()
        else:
            self._cancel_all_timers()
            if self._is_on:
                self._state = STATE_PERM_OVERRIDE
                self._deactivate()
            else:
                # Light is off, turn on in perm override mode
                self._state = STATE_PERM_OVERRIDE
                self._is_on = True
                self._brightness = self._get_current_brightness()
                self._actuate_on()

            # Perm override auto-expires using dedicated timeout [Spec §11]
            timeout = self._runtime_perm_override_timeout
            self._perm_override_timer_end = (
                self.hass.loop.time() + timeout
            )
            self._perm_override_timer = self.hass.loop.call_later(
                timeout,
                lambda: self.hass.async_create_task(
                    self._async_perm_override_timeout()
                ),
            )
            _LOGGER.info(
                "Perm override started: timeout=%.0fs, timer_end=%.1f",
                timeout, self._perm_override_timer_end,
            )

        self._notify_update()

    async def _async_perm_override_timeout(self) -> None:
        """Handle permanent override timeout [Spec §11]."""
        _LOGGER.debug("Permanent override timeout reached")
        self._perm_override_timer = None
        self._perm_override_timer_end = None
        self._state = STATE_IDLE
        self._deactivate()
        self._notify_update()
        await self._async_save_persisted()

    # ── Activation / Deactivation [Spec §3, §4] ─────────────────

    @callback
    def _activate(self) -> None:
        """Activate the light [Spec §3].

        Records activation timestamp for adaptive timeout tracking.
        Updates adaptive factor based on recent activation frequency.
        """
        # Track activation for adaptive timeout
        now = self.hass.loop.time()
        self._activation_timestamps.append(now)
        self._last_motion_time = now
        self._update_adaptive_factor()

        self._state = STATE_ACTIVE
        self._is_on = True
        self._brightness = self._get_current_brightness()
        self._actuate_on()
        self._notify_update()

    @callback
    def _deactivate(self) -> None:
        """Deactivate the light [Spec §3]."""
        if self._state not in (STATE_TEMP_OVERRIDE, STATE_PERM_OVERRIDE):
            self._state = STATE_IDLE
        self._is_on = False
        self._brightness = 0
        self._actuate_off()
        self._cancel_occupancy_timer()
        self._cancel_failsafe_timer()
        self._cancel_no_motion_timer()
        self._lux_high_since = None
        self._notify_update()

    # ── Actuation Rules [Spec §4] ────────────────────────────────

    @staticmethod
    def _to_list(val) -> list[str]:
        """Normalize config value to a list of entity IDs.

        Handles string (single entity, backward compat) and list.
        """
        if val is None:
            return []
        if isinstance(val, list):
            return [v for v in val if v]
        if isinstance(val, str) and val:
            return [val]
        return []

    @callback
    def _get_active_actuators(self) -> tuple[list[str], str | None]:
        """Return the active bulb list and relay entity.

        If soft profile is active and soft actuators are configured,
        uses those instead of the primary actuators [Spec §4, §12].
        Returns (bulbs_list, relay_entity_or_None).
        """
        if self._is_soft_profile_active():
            soft_bulbs = self._to_list(self.config.get(CONF_SOFT_BULB_ENTITY))
            soft_relay = self.config.get(CONF_SOFT_RELAY_ENTITY)
            if soft_bulbs or soft_relay:
                return soft_bulbs, soft_relay

        return (
            self._to_list(self.config.get(CONF_BULB_ENTITY)),
            self.config.get(CONF_RELAY_ENTITY),
        )

    @callback
    def _actuate_on(self) -> None:
        """Turn on actuators [Spec §4].

        Supports multiple bulb entities. All bulbs receive the
        same brightness command simultaneously.
        """
        bulbs, relay = self._get_active_actuators()

        for bulb in bulbs:
            self.hass.async_create_task(
                self.hass.services.async_call(
                    "light",
                    "turn_on",
                    {"entity_id": bulb, "brightness": self._brightness},
                )
            )

        if relay:
            self.hass.async_create_task(
                self.hass.services.async_call(
                    "switch", "turn_on", {"entity_id": relay}
                )
            )

    @callback
    def _actuate_off(self) -> None:
        """Turn off actuators [Spec §4].

        bulbs+relay: bulbs OFF, relay stays ON.
        only bulbs: OFF. only relay: OFF.
        Also turns off soft actuators if they were active.
        """
        bulbs, relay = self._get_active_actuators()
        primary_bulbs = self._to_list(self.config.get(CONF_BULB_ENTITY))
        primary_relay = self.config.get(CONF_RELAY_ENTITY)

        # Turn off all relevant bulbs (active + primary for profile switch)
        all_bulbs = set(bulbs + primary_bulbs)
        for b in all_bulbs:
            self.hass.async_create_task(
                self.hass.services.async_call(
                    "light", "turn_off", {"entity_id": b}
                )
            )

        # Turn off relay only if no bulbs configured for that pair
        if relay and not bulbs:
            self.hass.async_create_task(
                self.hass.services.async_call(
                    "switch", "turn_off", {"entity_id": relay}
                )
            )
        if primary_relay and not primary_bulbs:
            self.hass.async_create_task(
                self.hass.services.async_call(
                    "switch", "turn_off", {"entity_id": primary_relay}
                )
            )

    # ── Pre-Off Warning Dim [Spec §6] ────────────────────────────

    @callback
    def _start_warning(self) -> None:
        """Start warning dim sequence [Spec §6].

        Dims the light to warning_dim_pct % of current brightness.
        After warning_dim_duration seconds, deactivates.
        """
        if self._warning_task is not None:
            return

        self._state = STATE_WARNING
        self._warning_start = self.hass.loop.time()
        self._warning_task = self.hass.async_create_task(
            self._async_warning_dim()
        )
        self._notify_update()

    async def _async_warning_dim(self) -> None:
        """Execute warning dim sequence [Spec §6].

        Dims all active bulbs to a percentage of current brightness,
        waits for the configured duration, then deactivates.
        """
        dim_pct = self._runtime_warning_dim_pct
        duration = self._runtime_warning_dim_duration
        bulbs, relay = self._get_active_actuators()

        try:
            # Dim all bulbs to warning level
            dim_brightness = max(1, int(self._brightness * dim_pct / 100))
            for bulb in bulbs:
                await self.hass.services.async_call(
                    "light",
                    "turn_on",
                    {"entity_id": bulb, "brightness": dim_brightness},
                )

            # Wait for dim duration
            await asyncio.sleep(duration)

            # If still in warning state, deactivate
            if self._state == STATE_WARNING:
                self._deactivate()

        except asyncio.CancelledError:
            pass
        finally:
            self._warning_task = None
            self._warning_start = None

    @callback
    def _cancel_warning(self) -> None:
        """Cancel warning dim and restore brightness [Spec §6]."""
        if self._warning_task is not None:
            self._warning_task.cancel()
            self._warning_task = None

        self._warning_start = None

        # Restore full brightness on all active bulbs if still on
        bulbs, _ = self._get_active_actuators()
        if bulbs and self._is_on:
            for bulb in bulbs:
                self.hass.async_create_task(
                    self.hass.services.async_call(
                        "light",
                        "turn_on",
                        {"entity_id": bulb, "brightness": self._brightness},
                    )
                )

    # ── Timers ───────────────────────────────────────────────────

    @callback
    def _start_occupancy_timer(self) -> None:
        """Start occupancy timeout [Spec §3].

        Uses the effective timeout (base × adaptive factor)
        to extend timeout in high-traffic situations.
        """
        self._cancel_occupancy_timer()
        timeout = self._runtime_occupancy_timeout * self._adaptive_factor
        self._occupancy_timer_end = self.hass.loop.time() + timeout
        self._occupancy_timer = self.hass.loop.call_later(
            timeout,
            lambda: self.hass.async_create_task(
                self._async_occupancy_timeout()
            ),
        )
        self._notify_update()

    async def _async_occupancy_timeout(self) -> None:
        """Handle occupancy timeout [Spec §3, §6].

        Also decays adaptive factor when timeout fires normally,
        meaning traffic has calmed down.
        """
        self._occupancy_timer = None
        self._occupancy_timer_end = None
        # Decay adaptive factor on normal timeout expiry
        self._decay_adaptive_factor()
        if self._state == STATE_ACTIVE:
            _LOGGER.debug("Occupancy timeout, starting warning")
            self._start_warning()

    @callback
    def _cancel_occupancy_timer(self) -> None:
        """Cancel occupancy timer."""
        if self._occupancy_timer is not None:
            self._occupancy_timer.cancel()
            self._occupancy_timer = None
        self._occupancy_timer_end = None

    @callback
    def _start_failsafe_timer(self) -> None:
        """Start failsafe timer [Spec §8]."""
        self._cancel_failsafe_timer()
        timeout = self._runtime_failsafe_timeout
        self._failsafe_timer_end = self.hass.loop.time() + timeout
        self._failsafe_timer = self.hass.loop.call_later(
            timeout,
            lambda: self.hass.async_create_task(
                self._async_failsafe_timeout()
            ),
        )

    async def _async_failsafe_timeout(self) -> None:
        """Handle failsafe timeout [Spec §8].

        No motion detected for a long time. Forces OFF unless
        the system is in permanent override state.
        """
        self._failsafe_timer = None
        self._failsafe_timer_end = None

        # Perm override is immune to failsafe [Spec §8, §11]
        if self._state == STATE_PERM_OVERRIDE:
            _LOGGER.debug(
                "Failsafe timeout reached but perm_override active, ignoring"
            )
            return

        _LOGGER.debug("Failsafe timeout reached, forcing OFF")
        self._cancel_all_timers()
        self._state = STATE_IDLE
        self._is_on = False
        self._brightness = 0
        self._actuate_off()

        relay = self.config.get(CONF_RELAY_ENTITY)
        if relay:
            self.hass.async_create_task(
                self.hass.services.async_call(
                    "switch", "turn_off", {"entity_id": relay}
                )
            )

        self._notify_update()

    @callback
    def _cancel_failsafe_timer(self) -> None:
        """Cancel failsafe timer."""
        if self._failsafe_timer is not None:
            self._failsafe_timer.cancel()
            self._failsafe_timer = None
        self._failsafe_timer_end = None

    @callback
    def _cancel_perm_override_timer(self) -> None:
        """Cancel permanent override timer [Spec §11]."""
        if self._perm_override_timer is not None:
            self._perm_override_timer.cancel()
            self._perm_override_timer = None
        self._perm_override_timer_end = None

    @callback
    def _start_temp_override_timer(self) -> None:
        """Start temp override auto-expiry timer [Spec §10].

        If timeout is 0, no timer is started (override stays
        until next click). Otherwise starts a timer that will
        exit temp_override and re-evaluate conditions.
        """
        self._cancel_temp_override_timer()
        timeout = self._runtime_temp_override_timeout
        if timeout <= 0:
            _LOGGER.debug("Temp override: no timeout configured")
            return

        self._temp_override_timer_end = self.hass.loop.time() + timeout
        self._temp_override_timer = self.hass.loop.call_later(
            timeout,
            lambda: self.hass.async_create_task(
                self._async_temp_override_timeout()
            ),
        )
        _LOGGER.info("Temp override timer started: %.0fs", timeout)

    async def _async_temp_override_timeout(self) -> None:
        """Handle temp override timeout [Spec §10]."""
        _LOGGER.info("Temp override timeout reached, returning to auto")
        self._temp_override_timer = None
        self._temp_override_timer_end = None
        self._state = STATE_IDLE
        if self._any_motion_active() and self._is_lux_below_threshold():
            self._activate()
        else:
            self._deactivate()
        self._notify_update()

    @callback
    def _cancel_temp_override_timer(self) -> None:
        """Cancel temporary override timer [Spec §10]."""
        if self._temp_override_timer is not None:
            self._temp_override_timer.cancel()
            self._temp_override_timer = None
        self._temp_override_timer_end = None

    @callback
    def _cancel_all_timers(self) -> None:
        """Cancel all active timers."""
        self._cancel_occupancy_timer()
        self._cancel_failsafe_timer()
        self._cancel_warning()
        self._cancel_perm_override_timer()
        self._cancel_temp_override_timer()
        self._cancel_no_motion_timer()
        # Cancel click detection window
        if self._click_timer is not None:
            self._click_timer.cancel()
            self._click_timer = None
        self._click_count = 0
        self._lux_high_since = None

    # ── No-motion fallback [Spec §16] ────────────────────────────

    @callback
    def _start_no_motion_timer(self) -> None:
        """Start no-motion fallback timer [Spec §16].

        If occupancy is ON but no motion for no_motion_timeout
        seconds, trigger warning dim then off. Protects against
        stuck occupancy sensors or static heat sources.
        """
        self._cancel_no_motion_timer()
        timeout = self._runtime_no_motion_timeout
        if timeout <= 0:
            return

        self._no_motion_timer_end = self.hass.loop.time() + timeout
        self._no_motion_timer = self.hass.loop.call_later(
            timeout,
            lambda: self.hass.async_create_task(
                self._async_no_motion_timeout()
            ),
        )
        _LOGGER.debug("No-motion fallback timer started: %.0fs", timeout)

    async def _async_no_motion_timeout(self) -> None:
        """Handle no-motion fallback timeout [Spec §16].

        Occupancy is ON but no motion detected for a long time.
        Start warning dim sequence to turn off.
        """
        self._no_motion_timer = None
        self._no_motion_timer_end = None

        if self._state in (STATE_TEMP_OVERRIDE, STATE_PERM_OVERRIDE):
            _LOGGER.debug("No-motion timeout but in override, ignoring")
            return

        if self._state == STATE_ACTIVE:
            _LOGGER.info(
                "No-motion fallback: occupancy ON but no motion for %.0fs, "
                "starting warning dim [Spec §16]",
                self._runtime_no_motion_timeout,
            )
            self._start_warning()

    @callback
    def _cancel_no_motion_timer(self) -> None:
        """Cancel no-motion fallback timer."""
        if self._no_motion_timer is not None:
            self._no_motion_timer.cancel()
            self._no_motion_timer = None
        self._no_motion_timer_end = None

    # ── Helpers ──────────────────────────────────────────────────

    def _is_lux_below_threshold(self) -> bool:
        """Check if lux is below threshold [Spec §9]."""
        lux_entity = self.config.get(CONF_LUX_SENSOR)
        if not lux_entity:
            return True

        state = self.hass.states.get(lux_entity)
        if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return True

        try:
            lux_value = float(state.state)
        except (ValueError, TypeError):
            return True

        threshold = self.config.get(CONF_LUX_THRESHOLD, DEFAULT_LUX_THRESHOLD)
        return lux_value < threshold

    def _is_occupied(self) -> bool:
        """Check if area is currently occupied [Spec §2]."""
        occ_entity = self.config.get(CONF_OCCUPANCY_SENSOR)
        if not occ_entity:
            return False

        state = self.hass.states.get(occ_entity)
        if state is None:
            return False

        return state.state == STATE_ON

    def _any_motion_active(self) -> bool:
        """Check if any motion sensor is active (OR logic) [Spec §2, §7]."""
        motion_sensors = self.config.get(CONF_MOTION_SENSORS, [])
        for sensor_id in motion_sensors:
            state = self.hass.states.get(sensor_id)
            if state is not None and state.state == STATE_ON:
                return True
        return False

    def _get_current_brightness(self) -> int:
        """Get brightness based on current profile [Spec §5, §12]."""
        if self._is_soft_profile_active():
            return int(
                self.config.get(CONF_BRIGHTNESS_SOFT, DEFAULT_BRIGHTNESS_SOFT)
            )
        return int(
            self.config.get(CONF_BRIGHTNESS_NORMAL, DEFAULT_BRIGHTNESS_NORMAL)
        )

    def _is_soft_profile_active(self) -> bool:
        """Determine if soft profile should be active [Spec §12]."""
        mode = self.config.get(CONF_PROFILE_MODE, PROFILE_MODE_TIME)

        if mode == PROFILE_MODE_ENTITY:
            entity_id = self.config.get(CONF_SOFT_ENTITY)
            if entity_id:
                state = self.hass.states.get(entity_id)
                if state is not None:
                    return state.state == STATE_ON
            return False

        start_str = self.config.get(CONF_SOFT_TIME_START, "20:00")
        end_str = self.config.get(CONF_SOFT_TIME_END, "08:00")

        try:
            sp = start_str.split(":")
            ep = end_str.split(":")
            start_time = time(int(sp[0]), int(sp[1]))
            end_time = time(int(ep[0]), int(ep[1]))
        except (ValueError, IndexError):
            return False

        now = dt_util.now().time()

        if start_time <= end_time:
            return start_time <= now <= end_time
        return now >= start_time or now <= end_time

    # ── Adaptive Timeout Helpers ─────────────────────────────────

    def _prune_activation_timestamps(self) -> None:
        """Remove activation timestamps outside the rolling window."""
        window = float(
            self.config.get(CONF_ADAPTIVE_WINDOW, DEFAULT_ADAPTIVE_WINDOW)
        )
        cutoff = self.hass.loop.time() - window
        self._activation_timestamps = [
            ts for ts in self._activation_timestamps if ts > cutoff
        ]

    def _update_adaptive_factor(self) -> None:
        """Recalculate adaptive factor based on recent activations.

        When activations in the rolling window exceed the threshold,
        the occupancy timeout is progressively extended to prevent
        excessive on/off cycling in high-traffic areas.
        """
        self._prune_activation_timestamps()
        threshold = int(
            self.config.get(
                CONF_ADAPTIVE_THRESHOLD, DEFAULT_ADAPTIVE_THRESHOLD
            )
        )
        multiplier = float(
            self.config.get(
                CONF_ADAPTIVE_MULTIPLIER, DEFAULT_ADAPTIVE_MULTIPLIER
            )
        )
        max_factor = float(
            self.config.get(
                CONF_ADAPTIVE_MAX_FACTOR, DEFAULT_ADAPTIVE_MAX_FACTOR
            )
        )

        count = len(self._activation_timestamps)
        excess = max(0, count - threshold)

        if excess > 0:
            # Progressive: multiply for each activation over threshold
            self._adaptive_factor = min(
                multiplier ** excess, max_factor
            )
            _LOGGER.debug(
                "Adaptive factor updated: %.2f (count=%d, excess=%d)",
                self._adaptive_factor, count, excess,
            )
        # Factor is NOT reset here; it decays on timeout expiry

    def _decay_adaptive_factor(self) -> None:
        """Decay adaptive factor toward 1.0.

        Called when occupancy timeout fires normally (traffic calmed).
        Halves the excess above 1.0 each time.
        """
        if self._adaptive_factor > 1.0:
            self._adaptive_factor = max(
                1.0, 1.0 + (self._adaptive_factor - 1.0) / 2.0
            )
            # Snap to 1.0 if close enough
            if self._adaptive_factor < 1.05:
                self._adaptive_factor = 1.0
            _LOGGER.debug(
                "Adaptive factor decayed to: %.2f",
                self._adaptive_factor,
            )

    @callback
    def _notify_update(self) -> None:
        """Notify all entities of state changes and persist [Spec §14]."""
        for cb in self._update_callbacks:
            cb()
        self.hass.async_create_task(self._async_save_persisted())
