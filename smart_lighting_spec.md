# Smart Lighting Automation -- Specification (v4.6)

## 1. Scope

Area-based smart lighting automation for Home Assistant.
Zero Python dependencies. Physical click detection is delegated to the
`dvbit/whodidit` integration (optional).

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
- Physical interaction sensor (optional) — whodidit binary_sensor

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

## 10. Manual Override (whodidit)

Detection (delegated to `dvbit/whodidit`):
- physical_interaction_sensor = whodidit binary_sensor, ON during the click window
- On the ON → OFF transition the `click_count` attribute is read
- 1 click = temp override, 2 = perm override toggle, 3+ = ignored

## 11. Override Behavior

Temporary override (1 click):
- Toggles light state, freezes in temp_override
- Every further single click toggles again and restarts temp_override_timeout
- Exit: only temp_override_timeout (0 = never expires by itself, default)
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
- 9 sensors (4 timers, state, profile, adaptive factor, activation count, lux)
- 13 numbers (all runtime-adjustable parameters)
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

## 16. No-Motion Fallback (removed in v4.3.0)

- Removed: the failsafe timeout (§8) covers stuck occupancy sensors.

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

## 19. Localization and parameter documentation (v4.5)

- Config flow, options flow, selector options and entity names translated in
  EN, IT, FR, ES, DE (`translations/*.json`, `strings.json` = EN).
- Every config field has a short label (`data`) and a detailed explanation
  (`data_description`): purpose, effect, unit, special values.
- Entity names use `translation_key`. English names must slugify to the key,
  because HA generates entity_ids from English names and the card looks
  entities up by `smart_lighting_<area>_<key>`.
- README EN and IT contain a full parameter reference (default, range, meaning).
- (v4.6) Runtime parameters carry the same help text:
  - number entities expose a `description` attribute = config flow
    `data_description` in the HA language (English fallback), refreshed on
    core config update, excluded from the recorder (`_unrecorded_attributes`);
  - card v12 settings popup: (i) icon next to each parameter toggles its help
    text; the *Set lux threshold* button shows a short explanation. Card
    labels/help are generated from the same source as the translations.
