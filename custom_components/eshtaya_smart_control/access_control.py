"""Role-based access control for Eshtaya Smart Control."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable

from homeassistant.helpers.storage import Store

from .const import DOMAIN

DATA_ACCESS_CONTROL = "access_control"
STORAGE_KEY = f"{DOMAIN}.access_control"
STORAGE_VERSION = 1

PERMISSIONS: tuple[str, ...] = (
    "dashboard.view",
    "entity.view", "entity.manage",
    "tuya.view", "tuya.control", "tuya.configure",
    "multi.view", "multi.control", "multi.manage",
    "docs.view",
    "system.view", "system.actions", "system.reports",
    "access.manage",
)

MODULE_PERMISSION = {
    "dashboard": "dashboard.view",
    "entity": "entity.view",
    "tuya": "tuya.view",
    "multi": "multi.view",
    "docs": "docs.view",
    "system": "system.view",
    "access": "access.manage",
}

BUILTIN_ROLES: dict[str, dict[str, Any]] = {
    "no_access": {"name": "No Access", "permissions": []},
    "viewer": {
        "name": "Viewer",
        "permissions": ["dashboard.view", "entity.view", "tuya.view", "multi.view", "docs.view", "system.view"],
    },
    "operator": {
        "name": "Operator",
        "permissions": ["dashboard.view", "entity.view", "tuya.view", "tuya.control", "multi.view", "multi.control", "docs.view", "system.view"],
    },
    "technician": {
        "name": "Technician",
        "permissions": [
            "dashboard.view", "entity.view", "entity.manage", "tuya.view", "tuya.control",
            "multi.view", "multi.control", "multi.manage", "docs.view", "system.view",
            "system.actions", "system.reports",
        ],
    },
    "platform_manager": {"name": "Platform Manager", "permissions": list(PERMISSIONS)},
}


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class AccessControlManager:
    """Persist roles, user assignments, overrides and an audit log."""

    def __init__(self, hass) -> None:
        self.hass = hass
        self._store = Store(hass, STORAGE_VERSION, STORAGE_KEY, atomic_writes=True)
        self._data: dict[str, Any] = self._empty()

    @staticmethod
    def _empty() -> dict[str, Any]:
        return {
            "roles": {},
            "users": {},
            "audit": [],
            "settings": {"default_role": "no_access"},
        }

    async def async_load(self) -> None:
        loaded = await self._store.async_load()
        if isinstance(loaded, dict):
            data = self._empty()
            data.update(loaded)
            data["roles"] = dict(loaded.get("roles") or {})
            data["users"] = dict(loaded.get("users") or {})
            data["audit"] = list(loaded.get("audit") or [])[-500:]
            data["settings"].update(loaded.get("settings") or {})
            self._data = data
        await self._store.async_save(self._data)

    def _roles(self) -> dict[str, dict[str, Any]]:
        roles = deepcopy(BUILTIN_ROLES)
        for role_id, role in self._data.get("roles", {}).items():
            roles[role_id] = {
                "name": str(role.get("name") or role_id),
                "permissions": sorted(set(role.get("permissions") or []) & set(PERMISSIONS)),
                "custom": True,
            }
        return roles

    def _assignment(self, user_id: str) -> dict[str, Any]:
        return dict(self._data.get("users", {}).get(user_id) or {})

    def permissions_for(self, user) -> set[str]:
        if user is not None and getattr(user, "is_admin", False):
            return set(PERMISSIONS)
        if user is None:
            return set()
        assignment = self._assignment(user.id)
        expires = assignment.get("expires_at")
        if expires:
            try:
                expiry = datetime.fromisoformat(str(expires))
                if expiry.tzinfo is None:
                    expiry = expiry.replace(tzinfo=timezone.utc)
                if expiry <= datetime.now(timezone.utc):
                    assignment = {}
            except (ValueError, TypeError):
                pass
        role_id = str(assignment.get("role") or self._data["settings"].get("default_role") or "no_access")
        role = self._roles().get(role_id, BUILTIN_ROLES["no_access"])
        perms = set(role.get("permissions") or [])
        perms.update(set(assignment.get("allow") or []) & set(PERMISSIONS))
        perms.difference_update(set(assignment.get("deny") or []) & set(PERMISSIONS))
        return perms

    def can(self, user, permission: str) -> bool:
        return permission in self.permissions_for(user)

    def public_access(self, user) -> dict[str, Any]:
        perms = self.permissions_for(user)
        return {
            "is_admin": bool(user and getattr(user, "is_admin", False)),
            "permissions": sorted(perms),
            "modules": {module: perm in perms for module, perm in MODULE_PERMISSION.items()},
        }

    async def async_admin_snapshot(self) -> dict[str, Any]:
        users = []
        for user in await self.hass.auth.async_get_users():
            assignment = self._assignment(user.id)
            users.append({
                "id": user.id,
                "name": user.name or user.id,
                "is_admin": user.is_admin,
                "is_active": user.is_active,
                "system_generated": user.system_generated,
                "assignment": assignment,
                "effective_permissions": sorted(self.permissions_for(user)),
            })
        return {
            "roles": self._roles(),
            "permissions": list(PERMISSIONS),
            "users": users,
            "settings": deepcopy(self._data["settings"]),
            "audit": list(reversed(self._data["audit"][-100:])),
        }

    async def async_assign_user(self, actor, user_id: str, role: str, allow: list[str], deny: list[str], expires_at: str | None) -> None:
        if role not in self._roles():
            raise ValueError("Unknown role")
        target = await self.hass.auth.async_get_user(user_id)
        if target is None:
            raise ValueError("Home Assistant user not found")
        if target.is_admin:
            raise ValueError("Administrator access is always full and cannot be restricted")
        clean_allow = sorted(set(allow) & set(PERMISSIONS))
        clean_deny = sorted(set(deny) & set(PERMISSIONS))
        if expires_at:
            datetime.fromisoformat(expires_at)
        self._data["users"][user_id] = {
            "role": role, "allow": clean_allow, "deny": clean_deny,
            "expires_at": expires_at or None, "updated_at": _utcnow(),
        }
        self._audit(actor, "user_permissions_updated", user_id, {"role": role, "allow": clean_allow, "deny": clean_deny, "expires_at": expires_at})
        await self._store.async_save(self._data)

    async def async_save_role(self, actor, role_id: str, name: str, permissions: list[str]) -> None:
        role_id = role_id.strip().lower().replace(" ", "_")
        if not role_id or role_id in BUILTIN_ROLES:
            raise ValueError("Use a unique custom role id")
        self._data["roles"][role_id] = {"name": name.strip() or role_id, "permissions": sorted(set(permissions) & set(PERMISSIONS))}
        self._audit(actor, "role_saved", role_id, {"permissions": self._data["roles"][role_id]["permissions"]})
        await self._store.async_save(self._data)

    async def async_delete_role(self, actor, role_id: str) -> None:
        if role_id in BUILTIN_ROLES:
            raise ValueError("Built-in roles cannot be deleted")
        self._data["roles"].pop(role_id, None)
        for assignment in self._data["users"].values():
            if assignment.get("role") == role_id:
                assignment["role"] = self._data["settings"].get("default_role", "no_access")
        self._audit(actor, "role_deleted", role_id, {})
        await self._store.async_save(self._data)

    def _audit(self, actor, action: str, target: str, details: dict[str, Any]) -> None:
        self._data["audit"].append({
            "timestamp": _utcnow(),
            "actor_id": getattr(actor, "id", None),
            "actor_name": getattr(actor, "name", None),
            "action": action,
            "target": target,
            "details": details,
        })
        self._data["audit"] = self._data["audit"][-500:]


def get_access_manager(hass) -> AccessControlManager | None:
    return hass.data.get(DOMAIN, {}).get(DATA_ACCESS_CONTROL)


def require_permission(permission: str) -> Callable:
    """WebSocket decorator that enforces one Eshtaya permission at the backend."""
    def decorator(func):
        @wraps(func)
        def wrapper(hass, connection, msg, *args, **kwargs):
            manager = get_access_manager(hass)
            user = getattr(connection, "user", None)
            if manager is None or not manager.can(user, permission):
                connection.send_error(msg["id"], "unauthorized", f"Missing permission: {permission}")
                return None
            return func(hass, connection, msg, *args, **kwargs)
        return wrapper
    return decorator
