# Smart Lighting Automation -- Specification (v3.7)

## 1. Scope

Area-based smart lighting automation for Home Assistant.
Zero external dependencies. All features embedded.

## 2. Area Model

Sensors:
- Motion (>=1, OR logic)
- Occupancy (1)
- Lux (1)

Actuators:
- Smart bulbs (optional, multiple)
- Relay (optional, single)
- At least one actuator required.
- Soft profile bulbs (optional, multiple) — alternate lights for soft mode
- Soft profile relay (optional, single)

Override detection:
- Monitored switch (optional) — entity monitored for physical click detection
- Click time window (default 1.5s) — window for counting clicks

Suspend:
- Suspend entity (optional) — binary_sensor/input_boolean to pause automation

## 3. Core Logic

Light ON when:
- motion_detected == true
- lux < threshold

Light OFF when:
- no occupancy for configured timeout → warning dim → OFF

## 4. Actuation Rules

ON:
- All bulbs ON with same brightness
- Relay ON

OFF:
- bulbs + relay → bulbs OFF, relay stays ON (keeps power to smart bulbs)
- only bulbs → OFF
- only relay → OFF

Soft profile actuators used instead of primary when soft profile is active
and soft actuators are configured. On deactivation, both primary and soft
bulbs are turned off (handles profile switching during active state).

## 5. Brightness Profiles

Profiles: normal / soft
- Normal brightness: configurable (1-255)
- Soft brightness: configurable (1-255)
- Dynamic switching based on time range or entity state

## 6. Pre-Off Warning Dim

- When occupancy timeout expires: dim light to warning_dim_pct % of current brightness
- After warning_dim_duration seconds: deactivate
- Cancel on motion or occupancy: restore full brightness
- Default: 30% brightness, 10 seconds

## 7. Motion Handling

- Resets occupancy timer
- Resets failsafe timer
- Resets no-motion fallback timer
- Cancels warning dim (restores brightness)
- Records last_motion_time

## 8. Failsafe

- Resets on every motion detection (even during override)
- No motion for failsafe_timeout → forces OFF
- Immune to: permanent override (perm_override state is not affected)
- Forces off relay as well

## 9. Lux Behavior

- ON: only activates if lux < lux_threshold
- OFF: if active and lux >= threshold and not occupied → deactivate

## 9b. Natural Light Auto-Off

- Condition: state=active AND profile=normal AND not in override
- Trigger: lux exceeds lux_threshold × (1 + lux_hysteresis_pct/100)
  for at least lux_hysteresis_time consecutive seconds
- Action: deactivate
- Default: 10% above threshold, 5 seconds hysteresis
- Excluded from: override states, soft profile

## 10. Manual Override (Embedded Click Detection)

Detection:
- Monitors a configured switch/light entity (monitored_switch)
- Analyzes event context.user_id:
  - None → Physical (wall switch press)
  - user_id + parent_id → Automation → ignored
  - user_id without parent_id → UI → ignored
- Only Physical interactions counted for override

Click counting:
- Accumulates clicks within click_time_window (default 1.5s)
- After window expires: 1 click = temp override, 2 = perm override, 3+ = ignored

Exposed sensors:
- click_count, interaction_type, acting_user, click_time_window

## 11. Override Behavior

Temporary override (1 click):
- Toggles light state, freezes in temp_override
- Exit: another single click OR temp_override_timeout (0=never, default)
- On exit: re-evaluate motion+lux conditions
- Occupancy and motion ignored during temp_override

Permanent override (2 clicks):
- Toggles light state, freezes in perm_override
- Exit: another double click OR perm_override_timeout (default 3600s)
- On exit: re-evaluate motion+lux conditions
- Immune to failsafe
- Occupancy and motion ignored during perm_override

## 12. Profiles

- Time-based: soft profile active between soft_time_start and soft_time_end
- Entity-based: soft profile active when soft_entity state == ON
- Profile mode configurable: "time" or "entity"
- When soft profile active and soft actuators configured: uses alternate bulbs/relay

## 13. Architecture

- UI only (config_flow, no YAML)
- Virtual device per area grouping all entities
- Config flow: 5 steps (area, sensors, actuators, timings, profiles)
- OptionsFlow for reconfiguration
- Entity selectors filtered by selected HA area

Entities per area:
- 1 light (main controller)
- 14+ sensors (timers, state, profile, adaptive, click detection, lux)
- 13+ numbers (all runtime-adjustable parameters)
- 1 button (set lux threshold from sensor)

## 14. Persistence

- Override state survives restarts (via Storage)
- Number entity changes persisted to config_entry.data via async_update_entry
- Last manual action timestamp

## 15. Suspend

- Optional suspend_entity (binary_sensor / input_boolean)
- ON: state="suspended", all timers cancelled, light stays as-is, all events ignored
- OFF: re-evaluate motion+lux → activate or deactivate
- Use case: external scene automation (movie mode)

## 16. No-Motion Fallback

- If state=active and occupancy ON but no motion for no_motion_timeout → warning dim → OFF
- Protects against stuck occupancy sensors or static heat sources
- Resets on every motion detection
- Ignored during override states
- Default: 1800s (30 min), 0=disabled

## 17. Adaptive Timeout

- Counts activations (idle→active) in a rolling window (adaptive_window)
- When count exceeds adaptive_threshold: occupancy timeout multiplied by adaptive_multiplier^excess
- Capped at adaptive_max_factor
- Decays toward 1.0 when occupancy timeout fires normally
- Prevents excessive on/off cycling in high-traffic areas

## 18. Custom Lovelace Card

- Auto-registered as frontend resource (no manual copy needed)
- Area name displayed under center icon
- Customizable icons for normal (icon_main) and soft (icon_soft) profiles
- Timer progress bar with type icon (hidden if idle)
- Mode indicator: Idle/Automatic/Warning/Manual/Override/Suspended
- Status icons: motion, occupancy, lux with visual feedback
- Click icons → more-info popup of source entity
- Settings popup with all runtime parameters + set lux threshold button
- Localized: EN, IT, FR, ES, DE
