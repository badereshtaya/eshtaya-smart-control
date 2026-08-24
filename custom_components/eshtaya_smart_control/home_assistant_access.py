"""Home Assistant system access management for Eshtaya Smart Control v2.2.

This module intentionally uses only Home Assistant's supported built-in auth groups.
It does not fabricate unsupported custom Core roles or bypass Home Assistant's own
authorization engine.
"""
from __future__ import annotations

from typing import Any

from homeassistant.auth.const import GROUP_ID_ADMIN, GROUP_ID_READ_ONLY, GROUP_ID_USER
from homeassistant.core import HomeAssistant

HA_ROLE_ADMIN = "administrator"
HA_ROLE_USER = "user"
HA_ROLE_READ_ONLY = "read_only"
HA_ROLE_OWNER = "owner"

ROLE_TO_GROUP = {
    HA_ROLE_ADMIN: GROUP_ID_ADMIN,
    HA_ROLE_USER: GROUP_ID_USER,
    HA_ROLE_READ_ONLY: GROUP_ID_READ_ONLY,
}


def _role_for_user(user) -> str:
    if getattr(user, "is_owner", False):
        return HA_ROLE_OWNER
    group_ids = {group.id for group in getattr(user, "groups", [])}
    if GROUP_ID_ADMIN in group_ids:
        return HA_ROLE_ADMIN
    if GROUP_ID_READ_ONLY in group_ids:
        return HA_ROLE_READ_ONLY
    if GROUP_ID_USER in group_ids:
        return HA_ROLE_USER
    return "custom_or_none"


def _public_user(user) -> dict[str, Any]:
    return {
        "id": user.id,
        "name": user.name or user.id,
        "ha_role": _role_for_user(user),
        "is_owner": bool(getattr(user, "is_owner", False)),
        "is_admin": bool(getattr(user, "is_admin", False)),
        "is_active": bool(getattr(user, "is_active", True)),
        "local_only": bool(getattr(user, "local_only", False)),
        "system_generated": bool(getattr(user, "system_generated", False)),
        "group_ids": [group.id for group in getattr(user, "groups", [])],
        "group_names": [group.name or group.id for group in getattr(user, "groups", [])],
    }


async def async_snapshot(hass: HomeAssistant) -> dict[str, Any]:
    """Return Home Assistant-wide supported user access state."""
    users = [_public_user(user) for user in await hass.auth.async_get_users()]
    users.sort(key=lambda item: (not item["is_owner"], str(item["name"]).lower()))
    return {
        "users": users,
        "roles": [
            {
                "id": HA_ROLE_ADMIN,
                "name": "Administrator",
                "description": "Full Home Assistant administration plus entity control.",
            },
            {
                "id": HA_ROLE_USER,
                "name": "User",
                "description": "Normal Home Assistant user. Core currently grants entity access but not administrator-only configuration APIs.",
            },
            {
                "id": HA_ROLE_READ_ONLY,
                "name": "Read Only",
                "description": "Home Assistant Core read-only entity access.",
            },
        ],
        "capabilities": {
            "role_assignment": True,
            "activate_deactivate": True,
            "local_only": True,
            "custom_core_roles": False,
            "core_deny_rules": False,
            "service_level_acl": False,
            "entity_level_custom_policy_editor": False,
        },
        "limitations": [
            "Home Assistant Core currently exposes only Administrator, User and Read Only as supported built-in groups.",
            "Custom Core RBAC roles, deny-overrides-allow and per-service ACL are not supported by the public Home Assistant auth API.",
            "Eshtaya module permissions remain an additional backend-enforced layer and do not replace Home Assistant Core authorization.",
        ],
    }


async def async_update_user(
    hass: HomeAssistant,
    *,
    actor,
    user_id: str,
    role: str | None = None,
    is_active: bool | None = None,
    local_only: bool | None = None,
) -> dict[str, Any]:
    """Update a Home Assistant user's real system-wide supported access."""
    target = await hass.auth.async_get_user(user_id)
    if target is None:
        raise ValueError("Home Assistant user not found")
    if getattr(target, "system_generated", False):
        raise ValueError("System-generated Home Assistant users cannot be modified here")

    actor_id = getattr(actor, "id", None)
    if target.id == actor_id:
        if role is not None and role != _role_for_user(target):
            raise ValueError("You cannot change your own Home Assistant role from this panel")
        if is_active is False:
            raise ValueError("You cannot deactivate your own Home Assistant account")

    if getattr(target, "is_owner", False):
        if role is not None and role != HA_ROLE_OWNER:
            raise ValueError("The Home Assistant owner cannot be demoted")
        if is_active is False:
            raise ValueError("The Home Assistant owner cannot be deactivated")
        role = None

    group_ids = None
    if role is not None:
        if role not in ROLE_TO_GROUP:
            raise ValueError("Unsupported Home Assistant role")
        group_ids = [ROLE_TO_GROUP[role]]

    await hass.auth.async_update_user(
        target,
        group_ids=group_ids,
        is_active=is_active,
        local_only=local_only,
    )
    updated = await hass.auth.async_get_user(user_id)
    if updated is None:
        raise RuntimeError("Updated Home Assistant user disappeared")
    return _public_user(updated)
