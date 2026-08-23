"""WebSocket extensions for rules import/export."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN, WS_PREFIX
from .manager_v11 import EntityManagerV11
from .websocket import async_register_websocket_commands as async_register_base_commands


def _manager(hass: HomeAssistant) -> EntityManagerV11:
    return hass.data[DOMAIN]["entity_manager"]


@callback
def async_register_websocket_commands(hass: HomeAssistant) -> None:
    async_register_base_commands(hass)
    websocket_api.async_register_command(hass, websocket_import_rules)
    websocket_api.async_register_command(hass, websocket_export_rules)


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{WS_PREFIX}/import_rules",
        vol.Required("rules"): dict,
    }
)
@websocket_api.async_response
async def websocket_import_rules(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    try:
        result = await _manager(hass).async_import_legacy_rules(msg["rules"])
    except ValueError as err:
        connection.send_error(msg["id"], "invalid_rules_file", str(err))
        return
    connection.send_result(msg["id"], {"ok": True, **result})


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{WS_PREFIX}/export_rules"})
@websocket_api.async_response
async def websocket_export_rules(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    connection.send_result(msg["id"], _manager(hass).export_legacy_rules())
