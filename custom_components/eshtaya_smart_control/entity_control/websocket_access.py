"""Permission-aware Entity Control WebSocket registration for v2.1."""
from __future__ import annotations

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from ..ws_permissions import permissioned_admin_command
from .websocket import (
    websocket_bulk_rule,
    websocket_get,
    websocket_regenerate,
    websocket_rename,
    websocket_set_defaults,
    websocket_set_domain,
    websocket_set_entity_rule,
)
from .websocket_v11 import websocket_export_rules, websocket_import_rules
from .websocket_v12 import (
    websocket_cleanup_orphans,
    websocket_repair_sync,
    websocket_set_many_rules,
)


_VIEW_COMMANDS = (
    websocket_get,
    websocket_export_rules,
)

_MANAGE_COMMANDS = (
    websocket_set_entity_rule,
    websocket_set_domain,
    websocket_set_defaults,
    websocket_bulk_rule,
    websocket_rename,
    websocket_regenerate,
    websocket_import_rules,
    websocket_set_many_rules,
    websocket_repair_sync,
    websocket_cleanup_orphans,
)


@callback
def async_register_websocket_commands(hass: HomeAssistant) -> None:
    for command in _VIEW_COMMANDS:
        websocket_api.async_register_command(
            hass, permissioned_admin_command(command, "entity.view")
        )
    for command in _MANAGE_COMMANDS:
        websocket_api.async_register_command(
            hass, permissioned_admin_command(command, "entity.manage")
        )
