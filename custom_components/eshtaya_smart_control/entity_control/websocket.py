"""WebSocket API for Eshtaya Entity Manager."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN, RULE_VALUES, WS_PREFIX
from .manager import EntityManager


def _manager(hass: HomeAssistant) -> EntityManager:
    return hass.data[DOMAIN]["entity_manager"]


@callback
def async_register_websocket_commands(hass: HomeAssistant) -> None:
    websocket_api.async_register_command(hass, websocket_get)
    websocket_api.async_register_command(hass, websocket_set_entity_rule)
    websocket_api.async_register_command(hass, websocket_set_domain)
    websocket_api.async_register_command(hass, websocket_set_defaults)
    websocket_api.async_register_command(hass, websocket_bulk_rule)
    websocket_api.async_register_command(hass, websocket_rename)
    websocket_api.async_register_command(hass, websocket_regenerate)


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{WS_PREFIX}/get",
        vol.Optional("include_file", default=False): bool,
    }
)
@websocket_api.async_response
async def websocket_get(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    connection.send_result(
        msg["id"],
        await _manager(hass).async_get_snapshot(include_file=msg["include_file"]),
    )


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{WS_PREFIX}/set_entity_rule",
        vol.Required("entity_id"): str,
        vol.Required("mode"): vol.In(RULE_VALUES),
    }
)
@websocket_api.async_response
async def websocket_set_entity_rule(hass, connection, msg) -> None:
    try:
        await _manager(hass).async_set_entity_rule(msg["entity_id"], msg["mode"])
    except ValueError as err:
        connection.send_error(msg["id"], "invalid_entity_rule", str(err))
        return
    connection.send_result(msg["id"], {"ok": True})


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{WS_PREFIX}/set_domain",
        vol.Required("domain"): str,
        vol.Required("enabled"): bool,
    }
)
@websocket_api.async_response
async def websocket_set_domain(hass, connection, msg) -> None:
    try:
        await _manager(hass).async_set_domain(msg["domain"], msg["enabled"])
    except ValueError as err:
        connection.send_error(msg["id"], "invalid_domain", str(err))
        return
    connection.send_result(msg["id"], {"ok": True})


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{WS_PREFIX}/set_defaults",
        vol.Required("categories"): [str],
        vol.Required("keywords"): [str],
    }
)
@websocket_api.async_response
async def websocket_set_defaults(hass, connection, msg) -> None:
    await _manager(hass).async_set_defaults(msg["categories"], msg["keywords"])
    connection.send_result(msg["id"], {"ok": True})


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{WS_PREFIX}/bulk_rule",
        vol.Required("keyword"): str,
        vol.Required("where"): vol.In({"name", "id", "both"}),
        vol.Required("mode"): vol.In(RULE_VALUES),
        vol.Optional("domain"): vol.Any(str, None),
    }
)
@websocket_api.async_response
async def websocket_bulk_rule(hass, connection, msg) -> None:
    try:
        changed = await _manager(hass).async_bulk_rule(
            keyword=msg["keyword"],
            where=msg["where"],
            mode=msg["mode"],
            domain=msg.get("domain"),
        )
    except ValueError as err:
        connection.send_error(msg["id"], "invalid_bulk_rule", str(err))
        return
    connection.send_result(msg["id"], {"ok": True, "changed": changed})


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{WS_PREFIX}/rename",
        vol.Required("entity_id"): str,
        vol.Optional("name"): vol.Any(str, None),
    }
)
@websocket_api.async_response
async def websocket_rename(hass, connection, msg) -> None:
    try:
        await _manager(hass).async_rename_entity(msg["entity_id"], msg.get("name"))
    except ValueError as err:
        connection.send_error(msg["id"], "rename_failed", str(err))
        return
    connection.send_result(msg["id"], {"ok": True})


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{WS_PREFIX}/regenerate"})
@websocket_api.async_response
async def websocket_regenerate(hass, connection, msg) -> None:
    await _manager(hass).async_regenerate_hidden_file(save_store=True)
    connection.send_result(msg["id"], {"ok": True})
