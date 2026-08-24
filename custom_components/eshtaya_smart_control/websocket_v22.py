"""Core WebSocket API for Eshtaya Smart Control v2.2+."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN, VERSION
from .documentation_v23 import DOCUMENTATION
from .home_assistant_access import async_snapshot as async_ha_access_snapshot
from .home_assistant_access import async_update_user as async_ha_access_update_user
from .websocket import websocket_migration_report, websocket_system_action, websocket_system_report
from .websocket_v21 import (
    websocket_access_assign_user,
    websocket_access_current,
    websocket_access_delete_role,
    websocket_access_save_role,
    websocket_access_snapshot,
    websocket_overview,
)
from .ws_permissions import permissioned_admin_command


@callback
def async_register_websocket_commands(hass: HomeAssistant) -> None:
    """Register core APIs without duplicating v2.1 command names."""
    commands = (
        websocket_access_current,
        websocket_overview,
        websocket_documentation_get,
        websocket_access_snapshot,
        websocket_access_assign_user,
        websocket_access_save_role,
        websocket_access_delete_role,
        websocket_ha_access_snapshot,
        websocket_ha_access_update_user,
        permissioned_admin_command(websocket_migration_report, "system.reports"),
        permissioned_admin_command(websocket_system_report, "system.reports"),
        permissioned_admin_command(websocket_system_action, "system.actions"),
    )
    for command in commands:
        websocket_api.async_register_command(hass, command)


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/documentation/get",
        vol.Required("slug"): str,
        vol.Optional("language", default="en"): vol.In(["ar", "en"]),
    }
)
@callback
def websocket_documentation_get(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    """Return the detailed packaged documentation after checking current access."""
    from .access_control import get_access_manager

    manager = get_access_manager(hass)
    user = getattr(connection, "user", None)
    if manager is None or not manager.can(user, "docs.view"):
        connection.send_error(msg["id"], "unauthorized", "Missing permission: docs.view")
        return
    language = msg["language"]
    slug = str(msg["slug"]).strip().upper()
    document = DOCUMENTATION.get(language, {}).get(slug)
    if document is None:
        connection.send_error(msg["id"], "documentation_not_found", f"Unknown documentation page: {slug}")
        return
    connection.send_result(
        msg["id"],
        {"slug": slug, "language": language, "content": document, "version": VERSION},
    )


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/ha_access/snapshot"})
@websocket_api.async_response
async def websocket_ha_access_snapshot(
    hass: HomeAssistant, connection, msg: dict[str, Any]
) -> None:
    """Return the real Home Assistant system-wide access state to HA admins."""
    connection.send_result(msg["id"], await async_ha_access_snapshot(hass))


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/ha_access/update_user",
        vol.Required("user_id"): str,
        vol.Optional("role", default=None): vol.Any(
            None, vol.In(["administrator", "user", "read_only"])
        ),
        vol.Optional("is_active", default=None): vol.Any(None, bool),
        vol.Optional("local_only", default=None): vol.Any(None, bool),
    }
)
@websocket_api.async_response
async def websocket_ha_access_update_user(
    hass: HomeAssistant, connection, msg: dict[str, Any]
) -> None:
    """Apply a supported Home Assistant Core role/account change."""
    try:
        updated = await async_ha_access_update_user(
            hass,
            actor=getattr(connection, "user", None),
            user_id=msg["user_id"],
            role=msg.get("role"),
            is_active=msg.get("is_active"),
            local_only=msg.get("local_only"),
        )
    except (ValueError, RuntimeError) as err:
        connection.send_error(msg["id"], "ha_access_update_failed", str(err))
        return
    connection.send_result(msg["id"], {"ok": True, "user": updated})
