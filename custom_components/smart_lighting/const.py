"""Constants for Smart Lighting integration.

References to specification sections are noted as [Spec §N].
"""

DOMAIN = "smart_lighting"

# ── Config keys: Area & Sensors [Spec §2] ────────────────────────
CONF_AREA_NAME = "area_name"
CONF_AREA_ID = "area_id"                     # HA area registry ID
CONF_MOTION_SENSORS = "motion_sensors"       # >=1, OR logic [Spec §2]
CONF_OCCUPANCY_SENSOR = "occupancy_sensor"   # exactly 1 [Spec §2]
CONF_LUX_SENSOR = "lux_sensor"              # exactly 1 [Spec §2]
CONF_LUX_THRESHOLD = "lux_threshold"        # [Spec §3, §9]

# ── Config keys: Actuators [Spec §2, §4] ─────────────────────────
CONF_BULB_ENTITY = "bulb_entity"            # optional smart bulb
CONF_RELAY_ENTITY = "relay_entity"          # optional relay switch
# At least one actuator required [Spec §2]
CONF_SOFT_BULB_ENTITY = "soft_bulb_entity"  # optional alt bulb for soft profile
CONF_SOFT_RELAY_ENTITY = "soft_relay_entity"  # optional alt relay for soft profile

# ── Config keys: Manual Override [Spec §10] ──────────────────────
CONF_PHYSICAL_INTERACTION_SENSOR = "physical_interaction_sensor"
# Whodidit binary_sensor: ON during click window, click_count attribute

# ── Config keys: Timeouts [Spec §3, §8] ──────────────────────────
CONF_OCCUPANCY_TIMEOUT = "occupancy_timeout"  # [Spec §3] OFF trigger
CONF_FAILSAFE_TIMEOUT = "failsafe_timeout"   # [Spec §8] forced OFF
CONF_PERM_OVERRIDE_TIMEOUT = "perm_override_timeout"  # [Spec §11] perm override auto-expiry
CONF_TEMP_OVERRIDE_TIMEOUT = "temp_override_timeout"  # [Spec §10] temp override auto-expiry (0=never)

# ── Config keys: Pre-Off Warning Dim [Spec §6] ──────────────────
CONF_WARNING_DIM_PCT = "warning_dim_pct"        # % brightness during warning
CONF_WARNING_DIM_DURATION = "warning_dim_duration"  # seconds to stay dimmed

# ── Config keys: Fallback no-motion [Spec §16 - REMOVED] ────────
# no_motion_timeout removed: failsafe covers this case

# ── Config keys: Adaptive Timeout (anti-flickering) ──────────────
CONF_ADAPTIVE_WINDOW = "adaptive_window"          # window in seconds
CONF_ADAPTIVE_THRESHOLD = "adaptive_threshold"    # activations before extending
CONF_ADAPTIVE_MULTIPLIER = "adaptive_multiplier"  # factor per extra activation
CONF_ADAPTIVE_MAX_FACTOR = "adaptive_max_factor"  # max multiplier cap

# ── Config keys: Natural Light Auto-Off [Spec §9b] ──────────────
CONF_LUX_HYSTERESIS_PCT = "lux_hysteresis_pct"    # % above threshold to trigger
CONF_LUX_HYSTERESIS_TIME = "lux_hysteresis_time"  # seconds lux must stay high

# ── Config keys: Suspend [Spec §15] ─────────────────────────────
CONF_SUSPEND_ENTITY = "suspend_entity"  # binary_sensor/input_boolean

# ── Config keys: Brightness Profiles [Spec §5, §12] ──────────────
CONF_BRIGHTNESS_NORMAL = "brightness_normal"  # normal profile brightness
CONF_BRIGHTNESS_SOFT = "brightness_soft"      # soft profile brightness
CONF_SOFT_TIME_START = "soft_time_start"      # time-based profile [Spec §12]
CONF_SOFT_TIME_END = "soft_time_end"
CONF_SOFT_ENTITY = "soft_entity"              # entity-based profile [Spec §12]
CONF_PROFILE_MODE = "profile_mode"            # 'time' or 'entity' [Spec §12]

# ── Profile modes [Spec §12] ─────────────────────────────────────
PROFILE_MODE_TIME = "time"
PROFILE_MODE_ENTITY = "entity"

# ── State machine states [Spec §3, §6, §10] ──────────────────────
STATE_IDLE = "idle"                    # no activity
STATE_ACTIVE = "active"                # light ON [Spec §3]
STATE_WARNING = "warning"              # pre-off dim [Spec §6]
STATE_TEMP_OVERRIDE = "temp_override"  # single press override [Spec §10]
STATE_PERM_OVERRIDE = "perm_override"  # double press override [Spec §10]
STATE_SUSPENDED = "suspended"          # external suspend active [Spec §15]

# ── Defaults ──────────────────────────────────────────────────────
DEFAULT_LUX_THRESHOLD = 50             # lux [Spec §9]
DEFAULT_OCCUPANCY_TIMEOUT = 300        # 5 min [Spec §3]
DEFAULT_FAILSAFE_TIMEOUT = 3600       # 1 hour [Spec §8]
DEFAULT_PERM_OVERRIDE_TIMEOUT = 3600  # 1 hour [Spec §11]
DEFAULT_TEMP_OVERRIDE_TIMEOUT = 0     # 0 = no timeout [Spec §10]
DEFAULT_WARNING_DIM_PCT = 30           # 30% brightness during warning [Spec §6]
DEFAULT_WARNING_DIM_DURATION = 10     # 10 seconds dimmed [Spec §6]
DEFAULT_BRIGHTNESS_NORMAL = 255        # max [Spec §5]
DEFAULT_BRIGHTNESS_SOFT = 100          # dimmed [Spec §5]
DEFAULT_SOFT_TIME_START = "20:00"      # [Spec §12]
DEFAULT_SOFT_TIME_END = "08:00"        # [Spec §12]

# ── Adaptive timeout defaults ────────────────────────────────────
DEFAULT_ADAPTIVE_WINDOW = 600          # 10 min window
DEFAULT_ADAPTIVE_THRESHOLD = 3         # activations before extending
DEFAULT_ADAPTIVE_MULTIPLIER = 1.5      # factor per extra activation
DEFAULT_ADAPTIVE_MAX_FACTOR = 4.0      # max multiplier cap

# ── Natural Light Auto-Off defaults [Spec §9b] ──────────────────
DEFAULT_LUX_HYSTERESIS_PCT = 10        # 10% above threshold
DEFAULT_LUX_HYSTERESIS_TIME = 5        # 5 seconds

# ── Persistence keys [Spec §14] ──────────────────────────────────
PERSIST_OVERRIDE_STATE = "override_state"
PERSIST_LAST_MANUAL_ACTION = "last_manual_action"
PERSIST_TIMERS = "timers"

# ── Platforms ─────────────────────────────────────────────────────
PLATFORMS_LIST = ["light", "sensor", "number", "button"]
