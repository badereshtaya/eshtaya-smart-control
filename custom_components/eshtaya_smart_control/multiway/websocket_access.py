"""Permission-aware Multi-Way WebSocket registration for v2.1."""
from __future__ import annotations

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from ..ws_permissions import permissioned_admin_command
from . import websocket as legacy_ws


_VIEW_COMMANDS = (
    "ws_list",
    "ws_activity",
    "ws_get_settings",
    "ws_export",
    "ws_test",
    "ws_smart_list",
    "ws_smart_test",
    "ws_smart_test_all",
    "ws_smart_diagnostics",
    "ws_smart_ha_groups",
    "ws_full_export",
)

_CONTROL_COMMANDS = (
    "ws_set_enabled",
    "ws_sync",
    "ws_sync_all",
    "ws_test_entity_action",
    "ws_rapid_toggle_test",
    "ws_smart_set_state",
    "ws_smart_action",
    "ws_smart_set_enabled",
    "ws_smart_sync",
)

_MANAGE_COMMANDS = (
    "ws_create",
    "ws_update",
    "ws_delete",
    "ws_update_settings",
    "ws_import",
    "ws_learn_start",
    "ws_learn_status",
    "ws_learn_cancel",
    "ws_smart_create",
    "ws_smart_update",
    "ws_smart_delete",
    "ws_smart_clone",
    "ws_smart_quarantine",
    "ws_smart_settings",
    "ws_smart_template_save",
    "ws_smart_template_delete",
    "ws_smart_undo",
    "ws_smart_import_ha_group",
    "ws_smart_takeover_ha_group",
    "ws_smart_refresh_ha_group",
    "ws_full_import",
    "ws_repair_missing",
    "ws_repair_remap",
    "ws_multiway_undo",
)


def _register_group(hass: HomeAssistant, names: tuple[str, ...], permission: str) -> None:
    for name in names:
        command = getattr(legacy_ws, name)
        websocket_api.async_register_command(
            hass, permissioned_admin_command(command, permission)
        )


@callback
def async_register_websocket_commands(hass: HomeAssistant) -> None:
    _register_group(hass, _VIEW_COMMANDS, "multi.view")
    _register_group(hass, _CONTROL_COMMANDS, "multi.control")
    _register_group(hass, _MANAGE_COMMANDS, "multi.manage")
