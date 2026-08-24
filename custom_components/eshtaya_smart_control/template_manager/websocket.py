"""Permission-aware WebSocket API for integrated Template Manager."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from ..access_control import require_permission
from ..const import DOMAIN
from .const import DATA_TEMPLATE_MANAGER, DATA_TEMPLATE_MIGRATION


def _manager(hass: HomeAssistant):
    manager = hass.data.get(DOMAIN, {}).get(DATA_TEMPLATE_MANAGER)
    if manager is None:
        raise RuntimeError("Template Manager is not initialized")
    return manager


@callback
def async_register_websocket_commands(hass: HomeAssistant) -> None:
    for command in (
        websocket_snapshot,
        websocket_scan,
        websocket_create,
        websocket_edit,
        websocket_delete,
        websocket_relink,
        websocket_migration,
    ):
        websocket_api.async_register_command(hass, command)


@require_permission("template.view")
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/template/snapshot"})
@websocket_api.async_response
async def websocket_snapshot(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    connection.send_result(msg["id"], _manager(hass).snapshot())


@require_permission("template.view")
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/template/scan"})
@websocket_api.async_response
async def websocket_scan(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    connection.send_result(msg["id"], await _manager(hass).async_scan())


@require_permission("template.manage")
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/template/create",
        vol.Required("source_entity"): str,
        vol.Required("template_type"): vol.In(["light", "fan"]),
        vol.Required("name"): str,
        vol.Required("entity_id"): str,
    }
)
@websocket_api.async_response
async def websocket_create(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    try:
        result = await _manager(hass).async_create(
            source_entity=msg["source_entity"],
            template_type=msg["template_type"],
            name=msg["name"],
            entity_id=msg["entity_id"],
        )
        connection.send_result(msg["id"], result)
    except ValueError as err:
        connection.send_error(msg["id"], "template_invalid", str(err))


@require_permission("template.manage")
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/template/edit",
        vol.Required("managed_entity"): str,
        vol.Required("name"): str,
        vol.Required("entity_id"): str,
    }
)
@websocket_api.async_response
async def websocket_edit(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    try:
        result = await _manager(hass).async_edit(
            managed_entity=msg["managed_entity"], name=msg["name"], entity_id=msg["entity_id"]
        )
        connection.send_result(msg["id"], result)
    except ValueError as err:
        connection.send_error(msg["id"], "template_invalid", str(err))


@require_permission("template.manage")
@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/template/delete", vol.Required("managed_entity"): str}
)
@websocket_api.async_response
async def websocket_delete(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    try:
        await _manager(hass).async_delete(msg["managed_entity"])
        connection.send_result(msg["id"], {"ok": True})
    except ValueError as err:
        connection.send_error(msg["id"], "template_invalid", str(err))


@require_permission("template.manage")
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/template/relink",
        vol.Required("managed_entity"): str,
        vol.Required("source_entity"): str,
    }
)
@websocket_api.async_response
async def websocket_relink(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    try:
        result = await _manager(hass).async_relink(
            managed_entity=msg["managed_entity"], source_entity=msg["source_entity"]
        )
        connection.send_result(msg["id"], result)
    except ValueError as err:
        connection.send_error(msg["id"], "template_invalid", str(err))


@require_permission("template.view")
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/template/migration"})
@callback
def websocket_migration(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    store = _manager(hass).store
    connection.send_result(msg["id"], store.migration())
