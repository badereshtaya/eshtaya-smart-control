"""Permission-aware runtime and migration settings API."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .access_control import require_permission
from .const import (
    CONF_LEGACY_HACS_CLEANUP,
    CONF_LEGACY_MIGRATION_ENABLED,
    CONF_LEGACY_SERVICE_ALIASES,
    CONF_MIGRATE_ENTITY_MANAGER,
    CONF_MIGRATE_MULTIWAY,
    CONF_MIGRATE_TEMPLATE_MANAGER,
    CONF_REPAIR_CONFIRMATIONS,
    CONF_REPAIR_GRACE_SECONDS,
    CONF_STARTUP_MAX_WAIT_SECONDS,
    CONF_STARTUP_SETTLE_SECONDS,
    CONF_STARTUP_WAIT_HA,
    CONF_STARTUP_WAIT_REFERENCES,
    DATA_ENTRY,
    DOMAIN,
)
from .runtime_options import effective_options

_BOOL_KEYS = (
    CONF_STARTUP_WAIT_HA,
    CONF_STARTUP_WAIT_REFERENCES,
    CONF_LEGACY_MIGRATION_ENABLED,
    CONF_MIGRATE_ENTITY_MANAGER,
    CONF_MIGRATE_MULTIWAY,
    CONF_MIGRATE_TEMPLATE_MANAGER,
    CONF_LEGACY_HACS_CLEANUP,
    CONF_LEGACY_SERVICE_ALIASES,
)
_INT_RANGES = {
    CONF_STARTUP_SETTLE_SECONDS: (0, 120),
    CONF_STARTUP_MAX_WAIT_SECONDS: (30, 900),
    CONF_REPAIR_GRACE_SECONDS: (0, 900),
    CONF_REPAIR_CONFIRMATIONS: (1, 10),
}
_SETTING_KEYS = (*_BOOL_KEYS, *_INT_RANGES.keys())

# Stable public API names. Keep these explicit so frontend/backend contract changes
# are caught during CI instead of silently hiding a control.
PUBLIC_SETTING_NAMES = (
    "startup_wait_home_assistant",
    "startup_wait_referenced_integrations",
    "legacy_migration_enabled",
    "migrate_legacy_entity_manager",
    "migrate_legacy_multiway",
    "migrate_legacy_template_manager",
    "legacy_hacs_cleanup",
    "legacy_service_aliases",
    "startup_settle_seconds",
    "startup_max_wait_seconds",
    "repair_grace_seconds",
    "repair_missing_confirmations",
)
if set(PUBLIC_SETTING_NAMES) != set(_SETTING_KEYS):
    raise RuntimeError("Runtime settings public API is out of sync with constants")


def _entry(hass: HomeAssistant):
    entry = hass.data.get(DOMAIN, {}).get(DATA_ENTRY)
    if entry is None:
        raise RuntimeError("Eshtaya Smart Control config entry is not loaded")
    return entry


def _public_settings(hass: HomeAssistant) -> dict[str, Any]:
    entry = _entry(hass)
    options = effective_options(entry)
    return {
        "settings": {key: options[key] for key in _SETTING_KEYS},
        "groups": {
            "startup": [
                CONF_STARTUP_WAIT_HA,
                CONF_STARTUP_WAIT_REFERENCES,
                CONF_STARTUP_SETTLE_SECONDS,
                CONF_STARTUP_MAX_WAIT_SECONDS,
                CONF_REPAIR_GRACE_SECONDS,
                CONF_REPAIR_CONFIRMATIONS,
            ],
            "migration": [
                CONF_LEGACY_MIGRATION_ENABLED,
                CONF_MIGRATE_ENTITY_MANAGER,
                CONF_MIGRATE_MULTIWAY,
                CONF_MIGRATE_TEMPLATE_MANAGER,
                CONF_LEGACY_HACS_CLEANUP,
                CONF_LEGACY_SERVICE_ALIASES,
            ],
        },
        "reload_on_save": True,
        "native_group_takeover_independent": True,
    }


def _validate_updates(raw: dict[str, Any]) -> dict[str, Any]:
    clean: dict[str, Any] = {}
    for key in _BOOL_KEYS:
        if key in raw:
            value = raw[key]
            if not isinstance(value, bool):
                raise ValueError(f"{key} must be true or false")
            clean[key] = value
    for key, (minimum, maximum) in _INT_RANGES.items():
        if key not in raw:
            continue
        value = raw[key]
        if isinstance(value, bool):
            raise ValueError(f"{key} must be a number")
        try:
            number = int(value)
        except (TypeError, ValueError) as err:
            raise ValueError(f"{key} must be a number") from err
        if number < minimum or number > maximum:
            raise ValueError(f"{key} must be between {minimum} and {maximum}")
        clean[key] = number
    unknown = set(raw) - set(_SETTING_KEYS)
    if unknown:
        raise ValueError("Unknown settings: " + ", ".join(sorted(unknown)))
    if not clean:
        raise ValueError("No settings were provided")
    return clean


@require_permission("system.view")
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/settings/get"})
@callback
def websocket_settings_get(
    hass: HomeAssistant, connection, msg: dict[str, Any]
) -> None:
    """Return effective startup and migration controls."""
    try:
        connection.send_result(msg["id"], _public_settings(hass))
    except RuntimeError as err:
        connection.send_error(msg["id"], "settings_unavailable", str(err))


@require_permission("system.actions")
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/settings/update",
        vol.Required("settings"): dict,
    }
)
@callback
def websocket_settings_update(
    hass: HomeAssistant, connection, msg: dict[str, Any]
) -> None:
    """Persist controls and reload the config entry so every module sees them."""
    try:
        entry = _entry(hass)
        clean = _validate_updates(dict(msg["settings"]))
        updated = dict(entry.options)
        updated.update(clean)
        hass.config_entries.async_update_entry(entry, options=updated)
        result = _public_settings(hass)
        result["saved"] = True
        result["reloading"] = True
        connection.send_result(msg["id"], result)
        hass.async_create_task(
            hass.config_entries.async_reload(entry.entry_id),
            "Reload Eshtaya Smart Control after settings update",
        )
    except (RuntimeError, ValueError) as err:
        connection.send_error(msg["id"], "settings_invalid", str(err))


@callback
def async_register_websocket_commands(hass: HomeAssistant) -> None:
    """Register settings commands."""
    websocket_api.async_register_command(hass, websocket_settings_get)
    websocket_api.async_register_command(hass, websocket_settings_update)
