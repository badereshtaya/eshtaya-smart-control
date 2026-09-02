"""v2.4.3 WebSocket API for the full Template Manager editor."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from ..access_control import require_permission
from ..const import DOMAIN
from .const import DATA_TEMPLATE_MANAGER


def _manager(hass: HomeAssistant):
    manager = hass.data.get(DOMAIN, {}).get(DATA_TEMPLATE_MANAGER)
    if manager is None:
        raise RuntimeError("Template Manager is not initialized")
    return manager


@callback
def async_register_websocket_commands(hass: HomeAssistant) -> None:
    websocket_api.async_register_command(hass, websocket_editor_get)
    websocket_api.async_register_command(hass, websocket_editor_save)


@require_permission("template.view")
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/template/editor/get",
        vol.Required("managed_entity"): str,
    }
)
@websocket_api.async_response
async def websocket_editor_get(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    try:
        result = await _manager(hass).async_editor_get(msg["managed_entity"])
        connection.send_result(msg["id"], result)
    except ValueError as err:
        connection.send_error(msg["id"], "template_invalid", str(err))


@require_permission("template.manage")
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/template/editor/save",
        vol.Required("managed_entity"): str,
        vol.Required("template_type"): vol.In(["light", "fan"]),
        vol.Required("name"): str,
        vol.Required("entity_id"): str,
        vol.Required("source_entity"): str,
        vol.Optional("unique_id", default=""): str,
        vol.Optional("definition_yaml", default=""): str,
    }
)
@websocket_api.async_response
async def websocket_editor_save(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    try:
        result = await _manager(hass).async_editor_save(
            managed_entity=msg["managed_entity"],
            template_type=msg["template_type"],
            name=msg["name"],
            entity_id=msg["entity_id"],
            source_entity=msg["source_entity"],
            unique_id=msg.get("unique_id", ""),
            definition_yaml=msg.get("definition_yaml", ""),
        )
        connection.send_result(msg["id"], result)
    except ValueError as err:
        connection.send_error(msg["id"], "template_invalid", str(err))
