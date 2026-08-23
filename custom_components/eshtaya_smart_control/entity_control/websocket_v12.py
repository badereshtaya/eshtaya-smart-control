"""WebSocket extensions for Eshtaya Entity Manager v1.2."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN, RULE_VALUES, WS_PREFIX
from .manager_v12 import EntityManagerV12
from .websocket_v11 import async_register_websocket_commands as async_register_v11_commands


def _manager(hass: HomeAssistant) -> EntityManagerV12:
    return hass.data[DOMAIN]["entity_manager"]


@callback
def async_register_websocket_commands(hass: HomeAssistant) -> None:
    async_register_v11_commands(hass)
    websocket_api.async_register_command(hass, websocket_set_many_rules)
    websocket_api.async_register_command(hass, websocket_repair_sync)
    websocket_api.async_register_command(hass, websocket_cleanup_orphans)


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{WS_PREFIX}/set_many_rules",
        vol.Required("entity_ids"): [str],
        vol.Required("mode"): vol.In(RULE_VALUES),
    }
)
@websocket_api.async_response
async def websocket_set_many_rules(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    changed = await _manager(hass).async_set_many_rules(msg["entity_ids"], msg["mode"])
    connection.send_result(msg["id"], {"ok": True, "changed": changed})


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{WS_PREFIX}/repair_sync"})
@websocket_api.async_response
async def websocket_repair_sync(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    result = await _manager(hass).async_repair_sync()
    connection.send_result(msg["id"], {"ok": True, "sync": result})


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{WS_PREFIX}/cleanup_orphans"})
@websocket_api.async_response
async def websocket_cleanup_orphans(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    changed = await _manager(hass).async_cleanup_orphan_rules()
    connection.send_result(msg["id"], {"ok": True, "changed": changed})
