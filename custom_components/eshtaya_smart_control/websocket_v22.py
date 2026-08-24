"""Eshtaya Smart Control v2.2 WebSocket API extensions."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .const import DATA_HA_ACCESS, DOMAIN
from .websocket_v21 import async_register_websocket_commands as async_register_v21


def _manager(hass: HomeAssistant):
    manager = hass.data.get(DOMAIN, {}).get(DATA_HA_ACCESS)
    if manager is None:
        raise RuntimeError("Home Assistant Access manager is not initialized")
    return manager


@callback
def async_register_websocket_commands(hass: HomeAssistant) -> None:
    """Register v2.1 APIs plus native Home Assistant access endpoints."""
    async_register_v21(hass)
    for command in (
        websocket_ha_access_snapshot,
        websocket_ha_access_apply,
        websocket_ha_access_restore,
    ):
        websocket_api.async_register_command(hass, command)


@websocket_api.require_admin
@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/ha_access/snapshot"}
)
@websocket_api.async_response
async def websocket_ha_access_snapshot(
    hass: HomeAssistant, connection, msg: dict[str, Any]
) -> None:
    """Return current native Home Assistant access state for administration."""
    connection.send_result(msg["id"], await _manager(hass).async_snapshot())


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/ha_access/apply",
        vol.Required("user_id"): str,
        vol.Required("mode"): vol.In(
            [
                "standard",
                "read_only",
                "administrator",
                "restricted",
                "no_entity_access",
            ]
        ),
        vol.Optional("rules", default={}): dict,
    }
)
@websocket_api.async_response
async def websocket_ha_access_apply(
    hass: HomeAssistant, connection, msg: dict[str, Any]
) -> None:
    """Apply a native HA group or a restricted entity policy to one user."""
    try:
        result = await _manager(hass).async_apply(
            getattr(connection, "user", None),
            msg["user_id"],
            msg["mode"],
            msg.get("rules") or {},
        )
    except (ValueError, RuntimeError, vol.Invalid) as err:
        connection.send_error(msg["id"], "ha_access_invalid", str(err))
        return
    connection.send_result(msg["id"], {"ok": True, "user": result})


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/ha_access/restore",
        vol.Required("user_id"): str,
    }
)
@websocket_api.async_response
async def websocket_ha_access_restore(
    hass: HomeAssistant, connection, msg: dict[str, Any]
) -> None:
    """Restore the original HA groups captured before Eshtaya changed them."""
    try:
        result = await _manager(hass).async_restore(
            getattr(connection, "user", None), msg["user_id"]
        )
    except (ValueError, RuntimeError) as err:
        connection.send_error(msg["id"], "ha_access_restore_failed", str(err))
        return
    connection.send_result(msg["id"], {"ok": True, "user": result})
