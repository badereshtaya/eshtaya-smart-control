"""Permission-aware core WebSocket API for Eshtaya Smart Control v2.1."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .access_control import get_access_manager, require_permission
from .const import DATA_MIGRATION, DOMAIN, VERSION
from .documentation import DOCUMENTATION
from .websocket import (
    _snapshot,
    websocket_migration_report,
    websocket_system_action,
    websocket_system_report,
)
from .ws_permissions import permissioned_admin_command


def _access(hass: HomeAssistant):
    manager = get_access_manager(hass)
    if manager is None:
        raise RuntimeError("Access Control is not initialized")
    return manager


def _sanitize_overview(snapshot: dict[str, Any], permissions: set[str]) -> dict[str, Any]:
    """Remove module data the current user is not allowed to view."""
    result = deepcopy(snapshot)
    allowed_targets = {"dashboard"}

    if "entity.view" in permissions:
        allowed_targets.add("entity")
    else:
        result["entity"] = {"stats": {}, "file_sync": None, "maintenance": {}}

    if "tuya.view" in permissions:
        allowed_targets.add("tuya")
    else:
        result["tuya"] = {"configured": None, "activated": None, "restricted": True}

    if "multi.view" in permissions:
        allowed_targets.add("multi")
    else:
        result["multiway"] = {"groups": 0, "healthy": 0, "degraded": 0, "ready": None, "restricted": True}
        result["smart_groups"] = {"groups": 0, "healthy": 0, "degraded": 0, "restricted": True}

    if "system.view" in permissions:
        allowed_targets.add("system")
    else:
        result["legacy"] = {"restricted": True}
        result["migration"] = {"restricted": True}

    result["recommendations"] = [
        item
        for item in result.get("recommendations", [])
        if str(item.get("target") or "dashboard") in allowed_targets
    ]
    return result


@callback
def async_register_websocket_commands(hass: HomeAssistant) -> None:
    """Register v2.1 permission-aware core commands."""
    commands = (
        websocket_access_current,
        websocket_overview,
        websocket_documentation_get,
        websocket_access_snapshot,
        websocket_access_assign_user,
        websocket_access_save_role,
        websocket_access_delete_role,
        permissioned_admin_command(websocket_migration_report, "system.reports"),
        permissioned_admin_command(websocket_system_report, "system.reports"),
        permissioned_admin_command(websocket_system_action, "system.actions"),
    )
    for command in commands:
        websocket_api.async_register_command(hass, command)


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/access/current"})
@callback
def websocket_access_current(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    """Return only the current authenticated user's Eshtaya permissions."""
    manager = get_access_manager(hass)
    user = getattr(connection, "user", None)
    if manager is None:
        connection.send_result(
            msg["id"],
            {"is_admin": bool(user and getattr(user, "is_admin", False)), "permissions": [], "modules": {}},
        )
        return
    connection.send_result(msg["id"], manager.public_access(user))


@require_permission("dashboard.view")
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/overview"})
@websocket_api.async_response
async def websocket_overview(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    manager = _access(hass)
    user = getattr(connection, "user", None)
    snapshot = await _snapshot(hass)
    snapshot["access"] = manager.public_access(user)
    connection.send_result(msg["id"], _sanitize_overview(snapshot, manager.permissions_for(user)))


@require_permission("docs.view")
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/documentation/get",
        vol.Required("slug"): str,
        vol.Optional("language", default="en"): vol.In(["ar", "en"]),
    }
)
@callback
def websocket_documentation_get(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    language = msg["language"]
    slug = str(msg["slug"]).strip().upper()
    document = DOCUMENTATION.get(language, {}).get(slug)
    if document is None:
        connection.send_error(msg["id"], "documentation_not_found", f"Unknown documentation page: {slug}")
        return
    connection.send_result(msg["id"], {"slug": slug, "language": language, "content": document, "version": VERSION})


@require_permission("access.manage")
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/access/snapshot"})
@websocket_api.async_response
async def websocket_access_snapshot(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    connection.send_result(msg["id"], await _access(hass).async_admin_snapshot())


@require_permission("access.manage")
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/access/assign_user",
        vol.Required("user_id"): str,
        vol.Required("role"): str,
        vol.Optional("allow", default=[]): [str],
        vol.Optional("deny", default=[]): [str],
        vol.Optional("expires_at", default=None): vol.Any(None, str),
    }
)
@websocket_api.async_response
async def websocket_access_assign_user(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    try:
        await _access(hass).async_assign_user(
            getattr(connection, "user", None),
            msg["user_id"],
            msg["role"],
            msg["allow"],
            msg["deny"],
            msg.get("expires_at"),
        )
    except ValueError as err:
        connection.send_error(msg["id"], "invalid_access_assignment", str(err))
        return
    connection.send_result(msg["id"], {"ok": True})


@require_permission("access.manage")
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/access/save_role",
        vol.Required("role_id"): str,
        vol.Required("name"): str,
        vol.Required("permissions"): [str],
    }
)
@websocket_api.async_response
async def websocket_access_save_role(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    try:
        await _access(hass).async_save_role(
            getattr(connection, "user", None), msg["role_id"], msg["name"], msg["permissions"]
        )
    except ValueError as err:
        connection.send_error(msg["id"], "invalid_access_role", str(err))
        return
    connection.send_result(msg["id"], {"ok": True})


@require_permission("access.manage")
@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/access/delete_role", vol.Required("role_id"): str}
)
@websocket_api.async_response
async def websocket_access_delete_role(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    try:
        await _access(hass).async_delete_role(getattr(connection, "user", None), msg["role_id"])
    except ValueError as err:
        connection.send_error(msg["id"], "invalid_access_role", str(err))
        return
    connection.send_result(msg["id"], {"ok": True})
