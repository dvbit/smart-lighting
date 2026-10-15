# Smart Lighting

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Area-based smart lighting automation for Home Assistant: motion, occupancy and ambient light switch the lights, with pre-off warning, manual overrides, adaptive timeout and natural-light auto-off.

🇮🇹 [Leggi in italiano](README_IT.md) · 📄 [Specification](smart_lighting_spec.md)

## Features

- **Area-based configuration** — HA area picker, entity pickers filtered by area
- **Motion + occupancy** — motion switches on (OR logic across sensors), occupancy keeps the light on
- **Lux-aware** — switches on only below a configurable threshold
- **Two brightness profiles** — normal and soft, chosen by time range or by an entity
- **Multiple bulbs per relay** — the relay stays on so smart bulbs stay reachable
- **Alternate soft actuators** — dedicated bulbs/relay for the soft profile
- **Pre-off warning dim** — dims before switching off
- **Manual override** — single click (temporary) and double click (permanent) via [whodidit](https://github.com/dvbit/whodidit)
- **Failsafe** — no motion for a long time forces everything off
- **Natural-light auto-off** — switches off when daylight comes in (e.g. shutters opened)
- **Adaptive timeout** — longer timeout in high-traffic areas, decays back to normal
- **Suspend mode** — an external entity pauses the automation (e.g. movie mode)
- **Runtime-adjustable** — every timing is also a number entity; values persist across restarts
- **Virtual device** — all entities grouped under one device per area
- **Custom Lovelace card** — auto-registered, timer bar, mode indicator, settings popup
- **Localized** — EN, IT, FR, ES, DE (config flow with a description under every field, entity names, card)

## Installation

### HACS (recommended)

1. HACS → Integrations → ⋮ → Custom repositories
2. Add `https://github.com/dvbit/smart-lighting` as **Integration**
3. Search "Smart Lighting" and install
4. Restart Home Assistant

The Lovelace card is auto-registered as a frontend resource.

### Manual

Copy `custom_components/smart_lighting/` to `config/custom_components/` and restart.

## Configuration

**Settings → Devices & services → Add integration → Smart Lighting**. One entry per area.

Every field in the form shows a short name and, below it, a description of what it does. The same text is reported here. All values can be changed later with **Configure** (the integration reloads), and all timings are also exposed as number entities that apply immediately.

### Step 1: Area

Choose the Home Assistant area this controller manages. The next steps only list entities assigned to this area.

| Field | Key | Default | Range | Meaning |
|---|---|---|---|---|
| **Area** | `area_id` | — | — | Home Assistant area managed by this controller. Its name becomes the device name; entity pickers in the next steps are filtered by it. |

> **Example** — Pick `Kitchen`: the device is created as *Smart Lighting Kitchen* and the next pickers show only kitchen entities.

### Step 2: Sensors

Presence and ambient-light sensors that drive the automation. Motion, occupancy and illuminance sensors are required.

| Field | Key | Default | Range | Meaning |
|---|---|---|---|---|
| **Motion sensors** | `motion_sensors` | — | ≥ 1 | One or more binary_sensors (e.g. PIR). Any sensor turning on (OR logic) switches the light on, if ambient light is below the lux threshold. Every motion also restarts the occupancy countdown and the failsafe timer, and cancels the pre-off warning. |
| **Occupancy sensor** | `occupancy_sensor` | — | 1 | Binary_sensor for static presence (e.g. mmWave). While on, the switch-off countdown is held; when it turns off, the occupancy timeout starts. It also decides whether the area is still occupied when a temporary override expires. |
| **Illuminance sensor** | `lux_sensor` | — | 1 | Sensor reporting ambient light in lux. The light switches on only while the reading is below the lux threshold. If unavailable or not numeric, the area is treated as dark. |
| **Lux threshold (lx)** | `lux_threshold` | 50 lx | 0–1000 | Ambient light level below which motion switches the light on. If the light is on, the reading reaches this value and the occupancy sensor is off, the light switches off. Tip: the 'Set lux threshold' button stores the current reading. |

> **Example** — Kitchen with a PIR on the door (`binary_sensor.kitchen_pir`), an mmWave on the table (`binary_sensor.kitchen_presence`) and the mmWave illuminance (`sensor.kitchen_lux`), threshold `40`: the light switches on when someone enters and the room is darker than 40 lx, and stays on while the mmWave sees someone sitting.

### Step 3: Actuators

Entities switched by the controller, plus optional override and suspend inputs. At least one between smart bulbs and relay is required.

| Field | Key | Default | Range | Meaning |
|---|---|---|---|---|
| **Smart bulbs** | `bulb_entity` | — | 0..n | Optional. One or more light entities, all switched on with the brightness of the active profile. If a relay is also set, at switch-off only the bulbs are turned off and the relay stays on, so the bulbs stay reachable. |
| **Relay** | `relay_entity` | — | 0..1 | Optional switch powering the circuit. Without bulbs it is switched on/off directly. With bulbs it is switched on with them and left on at switch-off; only the failsafe turns it off. |
| **Physical interaction sensor** | `physical_interaction_sensor` | — | 0..1 | Optional binary_sensor from the whodidit integration. When its click window closes (on → off), the click_count attribute is read: 1 click = temporary override, 2 clicks = enter/exit permanent override, 3 or more = ignored. |
| **Soft profile bulbs** | `soft_bulb_entity` | — | 0..n | Optional. Light entities used instead of the smart bulbs while the soft profile is active (e.g. a night lamp). If neither soft bulbs nor soft relay are set, the normal actuators are used. |
| **Soft profile relay** | `soft_relay_entity` | — | 0..1 | Optional. Switch used instead of the relay while the soft profile is active. Same rules as the main relay. |
| **Suspend entity** | `suspend_entity` | — | 0..1 | Optional binary_sensor or input_boolean. While on, the automation is paused: timers are cancelled, the light is left as it is and all events are ignored (e.g. movie mode). When it turns off, motion and lux are re-evaluated. |

> **Example** — Ceiling with a Zigbee bulb behind a wall relay: bulbs `light.kitchen_ceiling`, relay `switch.kitchen_relay`. The relay stays on so the bulb never drops off the Zigbee mesh. Add `light.kitchen_underlight` as *soft profile bulbs* to use only the under-cabinet light at night, and `binary_sensor.kitchen_switch_whodidit` as *physical interaction sensor* to enable wall-switch overrides.

### Step 4: Timings

Switch-off timers, pre-off warning, adaptive timeout and natural-light auto-off. Every value can also be changed later from the device's number entities, without reconfiguring.

| Field | Key | Default | Range | Meaning |
|---|---|---|---|---|
| **Occupancy timeout (s)** | `occupancy_timeout` | 300 s | 10–7200 | Countdown before switch-off. It starts when presence ends (occupancy sensor off, or motion off if no occupancy sensor), restarts at every motion and is cancelled when occupancy returns. When it expires the warning dim starts. Multiplied by the adaptive factor in busy areas. |
| **Failsafe timeout (s)** | `failsafe_timeout` | 3600 s | 60–86400 | Safety net: with no motion for this time everything is forced off, relay included (protects against an occupancy sensor stuck on). Restarts at every motion. Ignored during permanent override. |
| **Permanent override timeout (s)** | `perm_override_timeout` | 3600 s | 60–86400 | Maximum duration of the permanent override (double click). When it expires the light switches off and automatic mode resumes. |
| **Temporary override timeout (s)** | `temp_override_timeout` | 0 s | 0–86400 | In temporary override (single click) every click toggles the light and restarts this timer. When it expires automatic mode resumes: light on if the area is occupied and dark, otherwise off. 0 = never expires by itself. |
| **Warning dim (%)** | `warning_dim_pct` | 30 % | 5–80 | Before switching off, the bulbs are dimmed to this percentage of the current brightness to warn whoever is still in the room. Any motion or occupancy cancels the warning and restores brightness. Effective only with smart bulbs. |
| **Warning dim duration (s)** | `warning_dim_duration` | 10 s | 3–60 | How long the light stays dimmed before switching off. |
| **Adaptive window (s)** | `adaptive_window` | 600 s | 60–3600 | Rolling time window in which automatic activations are counted to detect a high-traffic area. |
| **Adaptive threshold** | `adaptive_threshold` | 3 | 2–20 | Number of activations within the window above which the occupancy timeout starts to be extended. |
| **Adaptive multiplier** | `adaptive_multiplier` | 1.5 | 1.1–3.0 | Each activation beyond the threshold multiplies the occupancy timeout by this factor (factor = multiplier ^ extra activations). Example: 1.5 with 2 extra activations → ×2.25. |
| **Adaptive max factor** | `adaptive_max_factor` | 4.0 | 1.5–10.0 | Upper limit of the extension (e.g. 4.0 → at most 4× the occupancy timeout). Each time the timeout expires normally, the extra part of the factor is halved. |
| **Natural light margin (%)** | `lux_hysteresis_pct` | 10 % | 5–100 | Natural-light auto-off: with the light on in the normal profile, if ambient light exceeds threshold × (1 + margin/100) the light switches off even if the area is occupied (e.g. shutters opened). |
| **Natural light delay (s)** | `lux_hysteresis_time` | 5 s | 1–30 | Seconds the reading must stay above the margin before the natural-light auto-off, to ignore short peaks. |

> **Example** — Corridor: occupancy timeout `60`, warning `30 %` for `10 s`. If people walk through more than 3 times in 10 minutes (threshold `3`, window `600`), each extra activation multiplies the 60 s by `1.5`, up to `4.0` → max 240 s. With threshold `50 lx` and margin `10 %`, opening the shutters (lux ≥ 55 for `5 s`) switches the light off.

### Step 5: Brightness profiles

Brightness used when the light switches on automatically: normal profile, or soft profile (e.g. at night) selected by time range or by an entity.

| Field | Key | Default | Range | Meaning |
|---|---|---|---|---|
| **Normal brightness** | `brightness_normal` | 255 | 1–255 | Brightness (1–255) used by the normal profile. 255 = 100%. |
| **Soft brightness** | `brightness_soft` | 100 | 1–255 | Brightness (1–255) used while the soft profile is active, e.g. at night. 100 ≈ 40%. |
| **Soft profile activation** | `profile_mode` | time | time / entity | How the soft profile is chosen: 'Time range' uses start and end time below; 'Entity' follows the soft profile entity. |
| **Soft profile start** | `soft_time_start` | 20:00 | 00:00–23:59 | Time range mode only. Time the soft profile starts. Ranges across midnight are supported (e.g. 20:00–08:00). |
| **Soft profile end** | `soft_time_end` | 08:00 | 00:00–23:59 | Time range mode only. Time the soft profile ends. |
| **Soft profile entity** | `soft_entity` | — | 0..1 | Entity mode only. binary_sensor or input_boolean: while on, the soft profile is active (e.g. a 'night mode' helper). |

> **Example** — Normal `255`, soft `60`, mode *Time range* `22:30`–`06:30`: at night the light switches on at about 25 % (and with the soft bulbs, if set). With mode *Entity* and `input_boolean.night_mode`, the soft profile follows that helper instead.


## Entities

Each area creates a device *Smart Lighting &lt;Area&gt;* with these entities (entity_ids are always in English, names follow the HA language):

### Light

| Entity | Description |
|---|---|
| `light.smart_lighting_<area>` | Main controller. Turn on/off from UI = single click (temporary override) |

### Sensors (diagnostic)

| Entity | Description |
|---|---|
| `sensor.*_state` | State machine: idle, active, warning, temp_override, perm_override, suspended |
| `sensor.*_profile` | Active profile: normal or soft |
| `sensor.*_occupancy_timer` | Occupancy countdown remaining (s) |
| `sensor.*_failsafe_timer` | Failsafe remaining (s) |
| `sensor.*_override_timer` | Active override remaining (s) |
| `sensor.*_warning_timer` | Warning dim remaining (s) |
| `sensor.*_adaptive_factor` | Current adaptive multiplier |
| `sensor.*_activation_count` | Activations in the adaptive window |
| `sensor.*_lux` | Ambient light (lx), mirrors the illuminance sensor |

### Numbers (config, runtime, persistent)

`number.*_<key>` for every timing of step 4 plus `lux_threshold`: `occupancy_timeout`, `failsafe_timeout`, `perm_override_timeout`, `temp_override_timeout`, `warning_dim_pct`, `warning_dim_duration`, `lux_threshold`, `adaptive_window`, `adaptive_threshold`, `adaptive_multiplier`, `adaptive_max_factor`, `lux_hysteresis_pct`, `lux_hysteresis_time`. Same meaning as the table above; changes apply immediately and are saved in the entry. Each number entity also has a `description` attribute with the same help text, in the HA language (Attributes section of the entity dialog; not stored in history).

### Button

| Entity | Description |
|---|---|
| `button.*_set_lux_threshold` | Stores the current illuminance reading as the new lux threshold |

## State machine

![Smart Lighting State Machine](docs/state_machine.svg)

## Core logic

- **Switch-on**: motion + lux below threshold → light on at the active profile brightness.
- **Switch-off**: presence ends → occupancy timeout → warning dim → off.
- **Actuation**: bulbs + relay → on: all bulbs + relay; off: bulbs off, relay stays on. Only bulbs or only relay → plain on/off. Soft actuators replace the normal ones while the soft profile is active.
- **Failsafe**: no motion for `failsafe_timeout` → everything off, relay included. Permanent override is immune.

## Manual override (whodidit)

Set *Physical interaction sensor* to the whodidit `binary_sensor` of the wall switch. When its click window closes, `click_count` is read:

| Clicks | Effect |
|---|---|
| 1 | **Temporary override**: toggles the light; every further click toggles again and restarts `temp_override_timeout`. On expiry: light on if occupied and dark, otherwise off. Motion and occupancy are ignored meanwhile |
| 2 | **Permanent override**: toggles the light and freezes it, immune to failsafe. Another double click or `perm_override_timeout` returns to automatic |
| 3+ | Ignored |

## Natural-light auto-off

With the light on in the normal profile, if ambient light stays above `lux_threshold × (1 + lux_hysteresis_pct/100)` for `lux_hysteresis_time` seconds, the light switches off.

## Adaptive timeout

![Adaptive Timeout Mechanism](docs/adaptive_timeout.svg)

`factor = min(adaptive_multiplier ^ (activations − adaptive_threshold), adaptive_max_factor)`, counted over `adaptive_window`. Each normal expiry of the occupancy timeout halves the extra part of the factor.

## Suspend mode

While `suspend_entity` is on: state `suspended`, timers cancelled, light untouched. When it turns off, motion and lux are re-evaluated.

## Custom card

```yaml
type: custom:smart-lighting-card
area: kitchen                   # area slug used in the entity_ids
name: Kitchen                   # optional display name
icon_main: mdi:ceiling-light    # optional, normal profile icon
icon_soft: mdi:lamp             # optional, soft profile icon
```

Timer bar, large toggle icon, mode indicator, motion/occupancy/lux icons (tap = more-info) and a settings popup with all number entities and the *Set lux threshold* button. Tap ⓘ next to a parameter to show what it does (same text as the configuration form, in the HA language).

## Example automation

Turn on the suspend helper when the TV starts a movie:

```yaml
alias: Living room - movie mode suspends Smart Lighting
triggers:
  - trigger: state
    entity_id: media_player.living_room_tv
    to: playing
actions:
  - action: input_boolean.turn_on
    target:
      entity_id: input_boolean.living_room_movie_mode
mode: single
```

## License

MIT
