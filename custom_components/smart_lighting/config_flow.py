"""Config flow for Smart Lighting [Spec §13].

UI-only configuration (no YAML). Multi-step flow:
1. Area selection (HA area registry) [Spec §2]
2. Sensors filtered by selected area [Spec §2]
3. Actuators & interaction entity filtered by area [Spec §2, §4, §10]
4. Timeouts & warning settings [Spec §3, §6, §8]
5. Brightness profiles [Spec §5, §12]

Also provides OptionsFlow for reconfiguration without removing the entry.
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import (
    area_registry as ar,
    device_registry as dr,
    entity_registry as er,
    selector,
)

from .const import (
    CONF_ADAPTIVE_MAX_FACTOR,
    CONF_ADAPTIVE_MULTIPLIER,
    CONF_ADAPTIVE_THRESHOLD,
    CONF_ADAPTIVE_WINDOW,
    CONF_AREA_ID,
    CONF_AREA_NAME,
    CONF_BRIGHTNESS_NORMAL,
    CONF_BRIGHTNESS_SOFT,
    CONF_BULB_ENTITY,
    CONF_FAILSAFE_TIMEOUT,
    CONF_CLICK_TIME_WINDOW,
    CONF_MONITORED_SWITCH,
    CONF_LUX_HYSTERESIS_PCT,
    CONF_LUX_HYSTERESIS_TIME,
    CONF_LUX_SENSOR,
    CONF_LUX_THRESHOLD,
    CONF_MOTION_SENSORS,
    CONF_OCCUPANCY_SENSOR,
    CONF_OCCUPANCY_TIMEOUT,
    CONF_PERM_OVERRIDE_TIMEOUT,
    CONF_TEMP_OVERRIDE_TIMEOUT,
    CONF_PROFILE_MODE,
    CONF_RELAY_ENTITY,
    CONF_SOFT_BULB_ENTITY,
    CONF_SOFT_ENTITY,
    CONF_SOFT_RELAY_ENTITY,
    CONF_SOFT_TIME_END,
    CONF_SOFT_TIME_START,
    CONF_SUSPEND_ENTITY,
    CONF_WARNING_DIM_DURATION,
    CONF_WARNING_DIM_PCT,
    CONF_NO_MOTION_TIMEOUT,
    DEFAULT_ADAPTIVE_MAX_FACTOR,
    DEFAULT_ADAPTIVE_MULTIPLIER,
    DEFAULT_ADAPTIVE_THRESHOLD,
    DEFAULT_ADAPTIVE_WINDOW,
    DEFAULT_BRIGHTNESS_NORMAL,
    DEFAULT_BRIGHTNESS_SOFT,
    DEFAULT_FAILSAFE_TIMEOUT,
    DEFAULT_LUX_HYSTERESIS_PCT,
    DEFAULT_LUX_HYSTERESIS_TIME,
    DEFAULT_CLICK_TIME_WINDOW,
    DEFAULT_LUX_THRESHOLD,
    DEFAULT_OCCUPANCY_TIMEOUT,
    DEFAULT_PERM_OVERRIDE_TIMEOUT,
    DEFAULT_TEMP_OVERRIDE_TIMEOUT,
    DEFAULT_SOFT_TIME_END,
    DEFAULT_SOFT_TIME_START,
    DEFAULT_WARNING_DIM_DURATION,
    DEFAULT_WARNING_DIM_PCT,
    DEFAULT_NO_MOTION_TIMEOUT,
    DOMAIN,
    PROFILE_MODE_ENTITY,
    PROFILE_MODE_TIME,
)


def _get_area_entity_ids(
    hass, area_id: str, domain: str | None = None
) -> list[str]:
    """Return entity_ids assigned to a given HA area.

    Entities can be assigned to an area directly, or inherit
    the area from their parent device.
    """
    ent_reg = er.async_get(hass)
    dev_reg = dr.async_get(hass)

    result: list[str] = []
    for entry in ent_reg.entities.values():
        # Direct area assignment on the entity
        entity_area = entry.area_id
        if entity_area is None and entry.device_id:
            # Inherit area from parent device
            device = dev_reg.async_get(entry.device_id)
            if device:
                entity_area = device.area_id

        if entity_area == area_id:
            if domain is None or entry.domain == domain:
                result.append(entry.entity_id)
    return sorted(result)


class SmartLightingConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Smart Lighting [Spec §13]."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> SmartLightingOptionsFlow:
        """Get the options flow handler."""
        return SmartLightingOptionsFlow(config_entry)

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 1: Select HA area [Spec §2].

        Uses AreaSelector to pick from existing HA areas.
        All subsequent entity selectors will be filtered by this area.
        """
        if user_input is not None:
            area_id = user_input[CONF_AREA_ID]
            # Resolve area name from registry
            area_reg = ar.async_get(self.hass)
            area_entry = area_reg.async_get_area(area_id)
            self._data[CONF_AREA_ID] = area_id
            self._data[CONF_AREA_NAME] = (
                area_entry.name if area_entry else area_id
            )
            return await self.async_step_sensors()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_AREA_ID): selector.AreaSelector(),
                }
            ),
        )

    async def async_step_sensors(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 2: Sensors filtered by selected area [Spec §2].

        Collects:
        - Motion sensors (>=1, OR logic) [Spec §2]
        - Occupancy sensor (1) [Spec §2]
        - Lux sensor (1) [Spec §2, §9]
        - Lux threshold [Spec §9]

        Entity selectors show only entities belonging to the chosen area.
        """
        area_id = self._data[CONF_AREA_ID]

        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_actuators()

        # Build entity lists filtered by area
        binary_sensors = _get_area_entity_ids(
            self.hass, area_id, "binary_sensor"
        )
        sensors = _get_area_entity_ids(self.hass, area_id, "sensor")

        return self.async_show_form(
            step_id="sensors",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_MOTION_SENSORS): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            include_entities=binary_sensors,
                            multiple=True,
                        )
                    ),
                    vol.Required(
                        CONF_OCCUPANCY_SENSOR
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            include_entities=binary_sensors,
                        )
                    ),
                    vol.Required(CONF_LUX_SENSOR): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            include_entities=sensors,
                        )
                    ),
                    vol.Optional(
                        CONF_LUX_THRESHOLD, default=DEFAULT_LUX_THRESHOLD
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0, max=1000, step=1, mode="box"
                        )
                    ),
                }
            ),
        )

    async def async_step_actuators(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 3: Actuators and interaction entity [Spec §2, §4, §10].

        Filtered by area. At least one actuator required [Spec §2].
        """
        errors: dict[str, str] = {}
        area_id = self._data[CONF_AREA_ID]

        if user_input is not None:
            if not user_input.get(CONF_BULB_ENTITY) and not user_input.get(
                CONF_RELAY_ENTITY
            ):
                errors["base"] = "at_least_one_actuator"
            else:
                self._data.update(user_input)
                return await self.async_step_timings()

        lights = _get_area_entity_ids(self.hass, area_id, "light")
        switches = _get_area_entity_ids(self.hass, area_id, "switch")
        sensors = _get_area_entity_ids(self.hass, area_id, "sensor")

        return self.async_show_form(
            step_id="actuators",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_BULB_ENTITY): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            include_entities=lights,
                            multiple=True,
                        )
                    ),
                    vol.Optional(CONF_RELAY_ENTITY): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            include_entities=switches,
                        )
                    ),
                    vol.Optional(
                        CONF_MONITORED_SWITCH
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            include_entities=lights + switches,
                        )
                    ),
                    vol.Optional(
                        CONF_CLICK_TIME_WINDOW,
                        default=DEFAULT_CLICK_TIME_WINDOW,
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0.5, max=5.0, step=0.1,
                            unit_of_measurement="s", mode="box",
                        )
                    ),
                    vol.Optional(
                        CONF_SOFT_BULB_ENTITY
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            include_entities=lights,
                            multiple=True,
                        )
                    ),
                    vol.Optional(
                        CONF_SOFT_RELAY_ENTITY
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            include_entities=switches,
                        )
                    ),
                    vol.Optional(
                        CONF_SUSPEND_ENTITY
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain=["binary_sensor", "input_boolean"],
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_timings(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 4: Timeouts and warning settings [Spec §3, §6, §8]."""
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_profiles()

        return self.async_show_form(
            step_id="timings",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_OCCUPANCY_TIMEOUT,
                        default=DEFAULT_OCCUPANCY_TIMEOUT,
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=10,
                            max=7200,
                            step=10,
                            unit_of_measurement="s",
                            mode="box",
                        )
                    ),
                    vol.Optional(
                        CONF_FAILSAFE_TIMEOUT,
                        default=DEFAULT_FAILSAFE_TIMEOUT,
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=60,
                            max=86400,
                            step=60,
                            unit_of_measurement="s",
                            mode="box",
                        )
                    ),
                    vol.Optional(
                        CONF_PERM_OVERRIDE_TIMEOUT,
    CONF_TEMP_OVERRIDE_TIMEOUT,
                        default=DEFAULT_PERM_OVERRIDE_TIMEOUT,
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=60,
                            max=86400,
                            step=60,
                            unit_of_measurement="s",
                            mode="box",
                        )
                    ),
                    vol.Optional(
                        CONF_WARNING_DIM_PCT,
                        default=DEFAULT_WARNING_DIM_PCT,
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=5, max=80, step=5,
                            unit_of_measurement="%", mode="box",
                        )
                    ),
                    vol.Optional(
                        CONF_WARNING_DIM_DURATION,
                        default=DEFAULT_WARNING_DIM_DURATION,
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=3, max=60, step=1,
                            unit_of_measurement="s", mode="box",
                        )
                    ),
                    vol.Optional(
                        CONF_NO_MOTION_TIMEOUT,
                        default=DEFAULT_NO_MOTION_TIMEOUT,
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0, max=7200, step=60,
                            unit_of_measurement="s", mode="box",
                        )
                    ),
                    vol.Optional(
                        CONF_ADAPTIVE_WINDOW,
                        default=DEFAULT_ADAPTIVE_WINDOW,
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=60,
                            max=3600,
                            step=60,
                            unit_of_measurement="s",
                            mode="box",
                        )
                    ),
                    vol.Optional(
                        CONF_ADAPTIVE_THRESHOLD,
                        default=DEFAULT_ADAPTIVE_THRESHOLD,
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=2, max=20, step=1, mode="box"
                        )
                    ),
                    vol.Optional(
                        CONF_ADAPTIVE_MULTIPLIER,
                        default=DEFAULT_ADAPTIVE_MULTIPLIER,
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=1.1, max=3.0, step=0.1, mode="box"
                        )
                    ),
                    vol.Optional(
                        CONF_ADAPTIVE_MAX_FACTOR,
                        default=DEFAULT_ADAPTIVE_MAX_FACTOR,
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=1.5, max=10.0, step=0.5, mode="box"
                        )
                    ),
                    vol.Optional(
                        CONF_LUX_HYSTERESIS_PCT,
                        default=DEFAULT_LUX_HYSTERESIS_PCT,
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=5, max=100, step=1,
                            unit_of_measurement="%", mode="box",
                        )
                    ),
                    vol.Optional(
                        CONF_LUX_HYSTERESIS_TIME,
                        default=DEFAULT_LUX_HYSTERESIS_TIME,
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=1, max=30, step=1,
                            unit_of_measurement="s", mode="box",
                        )
                    ),
                }
            ),
        )

    async def async_step_profiles(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 5: Brightness profiles [Spec §5, §12]."""
        if user_input is not None:
            self._data.update(user_input)
            return self.async_create_entry(
                title=self._data[CONF_AREA_NAME],
                data=self._data,
            )

        return self.async_show_form(
            step_id="profiles",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_BRIGHTNESS_NORMAL,
                        default=DEFAULT_BRIGHTNESS_NORMAL,
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=1, max=255, step=1, mode="slider"
                        )
                    ),
                    vol.Optional(
                        CONF_BRIGHTNESS_SOFT,
                        default=DEFAULT_BRIGHTNESS_SOFT,
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=1, max=255, step=1, mode="slider"
                        )
                    ),
                    vol.Required(
                        CONF_PROFILE_MODE, default=PROFILE_MODE_TIME
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                selector.SelectOptionDict(
                                    value=PROFILE_MODE_TIME, label="Time range"
                                ),
                                selector.SelectOptionDict(
                                    value=PROFILE_MODE_ENTITY,
                                    label="Entity",
                                ),
                            ],
                            mode="dropdown",
                        )
                    ),
                    vol.Optional(
                        CONF_SOFT_TIME_START,
                        default=DEFAULT_SOFT_TIME_START,
                    ): selector.TimeSelector(),
                    vol.Optional(
                        CONF_SOFT_TIME_END, default=DEFAULT_SOFT_TIME_END
                    ): selector.TimeSelector(),
                    vol.Optional(CONF_SOFT_ENTITY): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain=["binary_sensor", "input_boolean"]
                        )
                    ),
                }
            ),
        )


class SmartLightingOptionsFlow(OptionsFlow):
    """Handle options flow for reconfiguration [Spec §13].

    Presents the same multi-step flow as initial setup,
    pre-filled with current configuration values.
    """

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry
        self._data: dict[str, Any] = dict(config_entry.data)

    def _cur(self, key: str, default: Any = None) -> Any:
        """Get current value from existing config."""
        return self._data.get(key, default)

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Entry point for options flow - area selection."""
        if user_input is not None:
            area_id = user_input[CONF_AREA_ID]
            area_reg = ar.async_get(self.hass)
            area_entry = area_reg.async_get_area(area_id)
            self._data[CONF_AREA_ID] = area_id
            self._data[CONF_AREA_NAME] = (
                area_entry.name if area_entry else area_id
            )
            return await self.async_step_sensors()

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_AREA_ID,
                        default=self._cur(CONF_AREA_ID),
                    ): selector.AreaSelector(),
                }
            ),
        )

    async def async_step_sensors(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Sensors step with current values as defaults."""
        area_id = self._data[CONF_AREA_ID]

        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_actuators()

        binary_sensors = _get_area_entity_ids(
            self.hass, area_id, "binary_sensor"
        )
        sensors = _get_area_entity_ids(self.hass, area_id, "sensor")

        return self.async_show_form(
            step_id="sensors",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_MOTION_SENSORS,
                        default=self._cur(CONF_MOTION_SENSORS, []),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            include_entities=binary_sensors,
                            multiple=True,
                        )
                    ),
                    vol.Required(
                        CONF_OCCUPANCY_SENSOR,
                        default=self._cur(CONF_OCCUPANCY_SENSOR),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            include_entities=binary_sensors,
                        )
                    ),
                    vol.Required(
                        CONF_LUX_SENSOR,
                        default=self._cur(CONF_LUX_SENSOR),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            include_entities=sensors,
                        )
                    ),
                    vol.Optional(
                        CONF_LUX_THRESHOLD,
                        default=self._cur(
                            CONF_LUX_THRESHOLD, DEFAULT_LUX_THRESHOLD
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0, max=1000, step=1, mode="box"
                        )
                    ),
                }
            ),
        )

    async def async_step_actuators(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Actuators step with current values as defaults."""
        errors: dict[str, str] = {}
        area_id = self._data[CONF_AREA_ID]

        if user_input is not None:
            if not user_input.get(CONF_BULB_ENTITY) and not user_input.get(
                CONF_RELAY_ENTITY
            ):
                errors["base"] = "at_least_one_actuator"
            else:
                self._data.update(user_input)
                return await self.async_step_timings()

        lights = _get_area_entity_ids(self.hass, area_id, "light")
        switches = _get_area_entity_ids(self.hass, area_id, "switch")
        sensors = _get_area_entity_ids(self.hass, area_id, "sensor")

        schema_dict: dict = {}
        # Pre-fill optional fields only if they have a current value
        if self._cur(CONF_BULB_ENTITY):
            schema_dict[
                vol.Optional(
                    CONF_BULB_ENTITY,
                    default=self._cur(CONF_BULB_ENTITY),
                )
            ] = selector.EntitySelector(
                selector.EntitySelectorConfig(include_entities=lights, multiple=True)
            )
        else:
            schema_dict[
                vol.Optional(CONF_BULB_ENTITY)
            ] = selector.EntitySelector(
                selector.EntitySelectorConfig(include_entities=lights, multiple=True)
            )

        if self._cur(CONF_RELAY_ENTITY):
            schema_dict[
                vol.Optional(
                    CONF_RELAY_ENTITY,
                    default=self._cur(CONF_RELAY_ENTITY),
                )
            ] = selector.EntitySelector(
                selector.EntitySelectorConfig(include_entities=switches)
            )
        else:
            schema_dict[
                vol.Optional(CONF_RELAY_ENTITY)
            ] = selector.EntitySelector(
                selector.EntitySelectorConfig(include_entities=switches)
            )

        # Monitored switch for click detection [Spec §10]
        if self._cur(CONF_MONITORED_SWITCH):
            schema_dict[
                vol.Optional(
                    CONF_MONITORED_SWITCH,
                    default=self._cur(CONF_MONITORED_SWITCH),
                )
            ] = selector.EntitySelector(
                selector.EntitySelectorConfig(
                    include_entities=lights + switches
                )
            )
        else:
            schema_dict[
                vol.Optional(CONF_MONITORED_SWITCH)
            ] = selector.EntitySelector(
                selector.EntitySelectorConfig(
                    include_entities=lights + switches
                )
            )

        schema_dict[
            vol.Optional(
                CONF_CLICK_TIME_WINDOW,
                default=self._cur(
                    CONF_CLICK_TIME_WINDOW, DEFAULT_CLICK_TIME_WINDOW
                ),
            )
        ] = selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0.5, max=5.0, step=0.1,
                unit_of_measurement="s", mode="box",
            )
        )

        # Soft profile alternate actuators (optional) [Spec §12]
        if self._cur(CONF_SOFT_BULB_ENTITY):
            schema_dict[
                vol.Optional(
                    CONF_SOFT_BULB_ENTITY,
                    default=self._cur(CONF_SOFT_BULB_ENTITY),
                )
            ] = selector.EntitySelector(
                selector.EntitySelectorConfig(include_entities=lights, multiple=True)
            )
        else:
            schema_dict[
                vol.Optional(CONF_SOFT_BULB_ENTITY)
            ] = selector.EntitySelector(
                selector.EntitySelectorConfig(include_entities=lights, multiple=True)
            )

        if self._cur(CONF_SOFT_RELAY_ENTITY):
            schema_dict[
                vol.Optional(
                    CONF_SOFT_RELAY_ENTITY,
                    default=self._cur(CONF_SOFT_RELAY_ENTITY),
                )
            ] = selector.EntitySelector(
                selector.EntitySelectorConfig(include_entities=switches)
            )
        else:
            schema_dict[
                vol.Optional(CONF_SOFT_RELAY_ENTITY)
            ] = selector.EntitySelector(
                selector.EntitySelectorConfig(include_entities=switches)
            )

        # Suspend entity (optional) [Spec §15]
        if self._cur(CONF_SUSPEND_ENTITY):
            schema_dict[
                vol.Optional(
                    CONF_SUSPEND_ENTITY,
                    default=self._cur(CONF_SUSPEND_ENTITY),
                )
            ] = selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain=["binary_sensor", "input_boolean"]
                )
            )
        else:
            schema_dict[
                vol.Optional(CONF_SUSPEND_ENTITY)
            ] = selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain=["binary_sensor", "input_boolean"]
                )
            )

        return self.async_show_form(
            step_id="actuators",
            data_schema=vol.Schema(schema_dict),
            errors=errors,
        )

    async def async_step_timings(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Timings step with current values as defaults."""
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_profiles()

        return self.async_show_form(
            step_id="timings",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_OCCUPANCY_TIMEOUT,
                        default=self._cur(
                            CONF_OCCUPANCY_TIMEOUT, DEFAULT_OCCUPANCY_TIMEOUT
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=10,
                            max=7200,
                            step=10,
                            unit_of_measurement="s",
                            mode="box",
                        )
                    ),
                    vol.Optional(
                        CONF_FAILSAFE_TIMEOUT,
                        default=self._cur(
                            CONF_FAILSAFE_TIMEOUT, DEFAULT_FAILSAFE_TIMEOUT
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=60,
                            max=86400,
                            step=60,
                            unit_of_measurement="s",
                            mode="box",
                        )
                    ),
                    vol.Optional(
                        CONF_PERM_OVERRIDE_TIMEOUT,
    CONF_TEMP_OVERRIDE_TIMEOUT,
                        default=self._cur(
                            CONF_PERM_OVERRIDE_TIMEOUT,
    CONF_TEMP_OVERRIDE_TIMEOUT,
                            DEFAULT_PERM_OVERRIDE_TIMEOUT,
    DEFAULT_TEMP_OVERRIDE_TIMEOUT,
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=60,
                            max=86400,
                            step=60,
                            unit_of_measurement="s",
                            mode="box",
                        )
                    ),
                    vol.Optional(
                        CONF_WARNING_DIM_PCT,
                        default=self._cur(
                            CONF_WARNING_DIM_PCT, DEFAULT_WARNING_DIM_PCT
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=5, max=80, step=5,
                            unit_of_measurement="%", mode="box",
                        )
                    ),
                    vol.Optional(
                        CONF_WARNING_DIM_DURATION,
                        default=self._cur(
                            CONF_WARNING_DIM_DURATION,
                            DEFAULT_WARNING_DIM_DURATION,
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=3, max=60, step=1,
                            unit_of_measurement="s", mode="box",
                        )
                    ),
                    vol.Optional(
                        CONF_NO_MOTION_TIMEOUT,
                        default=self._cur(
                            CONF_NO_MOTION_TIMEOUT,
                            DEFAULT_NO_MOTION_TIMEOUT,
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0, max=7200, step=60,
                            unit_of_measurement="s", mode="box",
                        )
                    ),
                    vol.Optional(
                        CONF_ADAPTIVE_WINDOW,
                        default=self._cur(
                            CONF_ADAPTIVE_WINDOW, DEFAULT_ADAPTIVE_WINDOW
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=60, max=3600, step=60,
                            unit_of_measurement="s", mode="box",
                        )
                    ),
                    vol.Optional(
                        CONF_ADAPTIVE_THRESHOLD,
                        default=self._cur(
                            CONF_ADAPTIVE_THRESHOLD, DEFAULT_ADAPTIVE_THRESHOLD
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=2, max=20, step=1, mode="box"
                        )
                    ),
                    vol.Optional(
                        CONF_ADAPTIVE_MULTIPLIER,
                        default=self._cur(
                            CONF_ADAPTIVE_MULTIPLIER,
                            DEFAULT_ADAPTIVE_MULTIPLIER,
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=1.1, max=3.0, step=0.1, mode="box"
                        )
                    ),
                    vol.Optional(
                        CONF_ADAPTIVE_MAX_FACTOR,
                        default=self._cur(
                            CONF_ADAPTIVE_MAX_FACTOR,
                            DEFAULT_ADAPTIVE_MAX_FACTOR,
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=1.5, max=10.0, step=0.5, mode="box"
                        )
                    ),
                    vol.Optional(
                        CONF_LUX_HYSTERESIS_PCT,
                        default=self._cur(
                            CONF_LUX_HYSTERESIS_PCT,
                            DEFAULT_LUX_HYSTERESIS_PCT,
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=5, max=100, step=1,
                            unit_of_measurement="%", mode="box",
                        )
                    ),
                    vol.Optional(
                        CONF_LUX_HYSTERESIS_TIME,
                        default=self._cur(
                            CONF_LUX_HYSTERESIS_TIME,
                            DEFAULT_LUX_HYSTERESIS_TIME,
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=1, max=30, step=1,
                            unit_of_measurement="s", mode="box",
                        )
                    ),
                }
            ),
        )

    async def async_step_profiles(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Profiles step with current values as defaults."""
        if user_input is not None:
            self._data.update(user_input)
            # Update the config entry data
            self.hass.config_entries.async_update_entry(
                self._config_entry, data=self._data
            )
            return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="profiles",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_BRIGHTNESS_NORMAL,
                        default=self._cur(
                            CONF_BRIGHTNESS_NORMAL, DEFAULT_BRIGHTNESS_NORMAL
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=1, max=255, step=1, mode="slider"
                        )
                    ),
                    vol.Optional(
                        CONF_BRIGHTNESS_SOFT,
                        default=self._cur(
                            CONF_BRIGHTNESS_SOFT, DEFAULT_BRIGHTNESS_SOFT
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=1, max=255, step=1, mode="slider"
                        )
                    ),
                    vol.Required(
                        CONF_PROFILE_MODE,
                        default=self._cur(
                            CONF_PROFILE_MODE, PROFILE_MODE_TIME
                        ),
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                selector.SelectOptionDict(
                                    value=PROFILE_MODE_TIME, label="Time range"
                                ),
                                selector.SelectOptionDict(
                                    value=PROFILE_MODE_ENTITY,
                                    label="Entity",
                                ),
                            ],
                            mode="dropdown",
                        )
                    ),
                    vol.Optional(
                        CONF_SOFT_TIME_START,
                        default=self._cur(
                            CONF_SOFT_TIME_START, DEFAULT_SOFT_TIME_START
                        ),
                    ): selector.TimeSelector(),
                    vol.Optional(
                        CONF_SOFT_TIME_END,
                        default=self._cur(
                            CONF_SOFT_TIME_END, DEFAULT_SOFT_TIME_END
                        ),
                    ): selector.TimeSelector(),
                    vol.Optional(
                        CONF_SOFT_ENTITY,
                        description={
                            "suggested_value": self._cur(CONF_SOFT_ENTITY)
                        },
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain=["binary_sensor", "input_boolean"]
                        )
                    ),
                }
            ),
        )
