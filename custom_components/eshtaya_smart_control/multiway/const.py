"""Constants for Eshtaya Multi-Way Control."""
from __future__ import annotations

from typing import Final

DOMAIN: Final = "eshtaya_smart_control"
NAME: Final = "Eshtaya Smart Control · Multi-Way"
VERSION: Final = "3.3.1"
MANUFACTURER: Final = "Eshtaya Smart"
MODEL: Final = "Virtual Multi-Way Group"
SMART_MODEL: Final = "Smart Group"

DATA_RUNTIME: Final = "multiway_runtime"
STORAGE_KEY: Final = f"{DOMAIN}.multiway.groups"
STORAGE_VERSION: Final = 1
SCHEMA_VERSION: Final = 2
SMART_STORAGE_KEY: Final = f"{DOMAIN}.multiway.smart_groups"
SMART_STORAGE_VERSION: Final = 1
SMART_SCHEMA_VERSION: Final = 2

PANEL_URL: Final = "eshtaya-smart-control"
PANEL_ELEMENT: Final = "eshtaya-smart-control-panel"
PANEL_TITLE: Final = "Eshtaya Smart Control"
PANEL_ICON: Final = "mdi:home-automation"
STATIC_URL: Final = f"/{DOMAIN}_static"

SIGNAL_GROUPS_UPDATED: Final = f"{DOMAIN}_groups_updated"
SIGNAL_RUNTIME_UPDATED: Final = f"{DOMAIN}_runtime_updated"
SIGNAL_SMART_GROUPS_UPDATED: Final = f"{DOMAIN}_smart_groups_updated"
SIGNAL_SMART_RUNTIME_UPDATED: Final = f"{DOMAIN}_smart_runtime_updated"
EVENT_TYPE: Final = f"{DOMAIN}_event"

VALID_STATES: Final = {"on", "off"}
UNAVAILABLE_STATES: Final = {"unavailable", "unknown"}

OUTPUT_DOMAINS: Final = {"switch", "light", "input_boolean", "fan"}
CONTROLLER_DOMAINS: Final = {
    "switch", "light", "input_boolean", "binary_sensor", "button", "input_button", "event"
}
COMMANDABLE_DOMAINS: Final = {"switch", "light", "input_boolean", "fan"}
PRESSABLE_DOMAINS: Final = {"button", "input_button"}

PERFORMANCE_INSTANT: Final = "instant"
PERFORMANCE_BALANCED: Final = "balanced"
PERFORMANCE_SAFE: Final = "safe"
PERFORMANCE_MODES: Final = {PERFORMANCE_INSTANT, PERFORMANCE_BALANCED, PERFORMANCE_SAFE}

SOURCE_POLICY_LATEST: Final = "latest_physical"
SOURCE_POLICY_OUTPUT: Final = "output_authority"
SOURCE_POLICIES: Final = {SOURCE_POLICY_LATEST, SOURCE_POLICY_OUTPUT}

MODE_MIRROR: Final = "mirror"
MODE_TOGGLE: Final = "toggle"
MODE_MOMENTARY_ON: Final = "momentary_on"
MODE_MOMENTARY_OFF: Final = "momentary_off"
MODE_EVENT: Final = "event"
MODE_FOLLOW: Final = "follow_output"
CONTROLLER_MODES: Final = {
    MODE_MIRROR, MODE_TOGGLE, MODE_MOMENTARY_ON, MODE_MOMENTARY_OFF, MODE_EVENT, MODE_FOLLOW
}

VIRTUAL_LIGHT: Final = "light"
VIRTUAL_SWITCH: Final = "switch"
VIRTUAL_TYPES: Final = {VIRTUAL_LIGHT, VIRTUAL_SWITCH}

HEALTH_HEALTHY: Final = "healthy"
HEALTH_DEGRADED: Final = "degraded"
HEALTH_DISABLED: Final = "disabled"
HEALTH_OUTPUT_OFFLINE: Final = "output_offline"
HEALTH_MISSING_OUTPUT: Final = "missing_output"
HEALTH_OUT_OF_SYNC: Final = "out_of_sync"
HEALTH_RECOVERING: Final = "recovering"

DEFAULT_SETTINGS: Final = {
    "startup_delay": 12,
    "watchdog_interval": 30,
    "command_timeout": 4.0,
    "max_retries": 1,
    "history_size": 100,
    "repair_threshold": 3,
    "confirm_output": True,
}

DEFAULT_BEHAVIOR: Final = {
    "debounce_ms": 120,
    "authority_window_ms": 1800,
    "performance_mode": PERFORMANCE_INSTANT,
    "auto_heal": True,
    "output_restore_policy": "adopt",
    "confirm_output": None,
    "command_timeout": None,
    "max_retries": None,
    "fallback_output": None,
    "source_policy": "latest_physical",
    # After rapid physical input, keep re-reading the authoritative source until
    # it settles, then perform one final convergence pass. This handles cloud
    # integrations that publish quick ON/OFF edges late or out of order.
    "rapid_settle_ms": 2600,
    "source_stable_ms": 220,
}

SERVICE_SYNC_GROUP: Final = "sync_group"
SERVICE_SYNC_ALL: Final = "sync_all"
SERVICE_ENABLE_GROUP: Final = "enable_group"
SERVICE_DISABLE_GROUP: Final = "disable_group"
SERVICE_SET_STATE: Final = "set_group_state"
SERVICE_TEST_GROUP: Final = "test_group"

# Smart Groups
SMART_KIND_PHYSICAL: Final = "physical"
SMART_KIND_VIRTUAL: Final = "virtual"
SMART_KINDS: Final = {SMART_KIND_PHYSICAL, SMART_KIND_VIRTUAL}
SMART_STATE_ANY: Final = "any"
SMART_STATE_ALL: Final = "all"
SMART_STATE_POLICIES: Final = {SMART_STATE_ANY, SMART_STATE_ALL}
SMART_DIRECTION_CONTROLLER: Final = "controller_only"
SMART_DIRECTION_BIDIRECTIONAL: Final = "bidirectional"
SMART_DIRECTIONS: Final = {SMART_DIRECTION_CONTROLLER, SMART_DIRECTION_BIDIRECTIONAL}
SMART_FAILURE_CONTINUE: Final = "continue"
SMART_FAILURE_STOP: Final = "stop"
SMART_FAILURE_POLICIES: Final = {SMART_FAILURE_CONTINUE, SMART_FAILURE_STOP}
SMART_NATIVE_GROUP_TYPES: Final = {
    "binary_sensor",
    "button",
    "cover",
    "event",
    "fan",
    "light",
    "lock",
    "media_player",
    "notify",
    "sensor",
    "switch",
    "valve",
}
SMART_ACTION_TYPES: Final = {"scene", "script", "automation"}
SMART_GROUP_TYPES: Final = SMART_NATIVE_GROUP_TYPES | SMART_ACTION_TYPES
SMART_COMMANDABLE_TYPES: Final = {
    "button",
    "cover",
    "fan",
    "light",
    "lock",
    "media_player",
    "switch",
    "valve",
    "scene",
    "script",
    "automation",
}
SMART_STATEFUL_TYPES: Final = {"cover", "fan", "light", "lock", "media_player", "switch", "valve"}
SMART_ON_OFF_TYPES: Final = {"fan", "light", "switch"}
SMART_READ_ONLY_TYPES: Final = {"binary_sensor", "event", "sensor"}
SMART_MEMBER_DOMAINS: Final = set(SMART_GROUP_TYPES)
SMART_SENSOR_CALC_TYPES: Final = {
    "last",
    "first_available",
    "max",
    "mean",
    "median",
    "min",
    "product",
    "range",
    "stdev",
    "sum",
}
SMART_CONTROLLER_DOMAINS: Final = {
    "switch", "light", "input_boolean", "binary_sensor", "button", "input_button", "event"
}
SMART_DEFAULT_BEHAVIOR: Final = {
    "state_policy": SMART_STATE_ANY,
    "sensor_calc_type": "mean",
    "ignore_non_numeric": False,
    "compatibility_mode": "strict",
    "direction": SMART_DIRECTION_CONTROLLER,
    "controller_mode": MODE_MIRROR,
    "invert_controller": False,
    "reflect_controller": True,
    "performance_mode": PERFORMANCE_INSTANT,
    "auto_heal": True,
    # Retry failed members only during the bounded verification window after a command.
    "verify_members": True,
    # Never fight automations/devices forever unless the installer explicitly opts in.
    "continuous_enforcement": False,
    # Cloud integrations may lose HA Context; suppress matching command echoes by state too.
    "command_echo_ms": 5000,
    "command_timeout": 3.0,
    "max_retries": 1,
    "member_delay_ms": 0,
    "failure_policy": SMART_FAILURE_CONTINUE,
    "manual_priority_ms": 2500,
    # Final-source settle for rapid physical/member ON/OFF edges.
    "source_stable_ms": 220,
    "scene_guard_ms": 800,
    "flap_threshold": 8,
    "flap_window_sec": 10,
    "quarantine_sec": 60,
    "notify_on_fault": False,
    # Action Groups (scene/script/automation)
    "action_execution": "parallel",
    "automation_skip_condition": True,
    "action_cooldown_ms": 250,
    "scene_transition": 0.0,
    "action_data": {},
}

SERVICE_SMART_SET_STATE: Final = "set_smart_group_state"
SERVICE_SMART_SYNC: Final = "sync_smart_group"
SERVICE_SMART_TEST: Final = "test_smart_group"
SERVICE_SMART_RUN: Final = "run_smart_group"
