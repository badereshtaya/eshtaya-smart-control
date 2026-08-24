"""Permission-aware Tuya WebSocket registration for v2.1."""
from __future__ import annotations

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from ..ws_permissions import permissioned_admin_command
from .websocket import (
    websocket_bulk_details,
    websocket_bulk_save,
    websocket_clear_config,
    websocket_device_details,
    websocket_list_devices,
    websocket_save_config,
    websocket_shadow_props,
    websocket_status,
    websocket_test_config,
    websocket_update_device_name,
    websocket_update_prop_name,
)


_VIEW_COMMANDS = (
    websocket_status,
    websocket_list_devices,
    websocket_device_details,
    websocket_shadow_props,
    websocket_bulk_details,
)

_CONTROL_COMMANDS = (
    websocket_update_device_name,
    websocket_update_prop_name,
    websocket_bulk_save,
)

_CONFIGURE_COMMANDS = (
    websocket_test_config,
    websocket_save_config,
    websocket_clear_config,
)


@callback
def async_register_websocket_commands(hass: HomeAssistant) -> None:
    for command in _VIEW_COMMANDS:
        websocket_api.async_register_command(hass, permissioned_admin_command(command, "tuya.view"))
    for command in _CONTROL_COMMANDS:
        websocket_api.async_register_command(hass, permissioned_admin_command(command, "tuya.control"))
    for command in _CONFIGURE_COMMANDS:
        websocket_api.async_register_command(hass, permissioned_admin_command(command, "tuya.configure"))
