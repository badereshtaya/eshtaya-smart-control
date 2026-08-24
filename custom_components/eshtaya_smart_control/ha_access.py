"""Native Home Assistant entity access management.

This module deliberately uses Home Assistant's own permission policy engine so
entity read/control/edit checks are enforced by Home Assistant itself. Home
Assistant currently exposes user group assignment publicly but not custom group
CRUD; custom restricted groups are therefore created through the loaded AuthStore
object with strict compatibility checks and an integration-owned rollback record.
The auth storage file is never edited directly.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import re
from typing import Any

from homeassistant.auth.const import GROUP_ID_ADMIN, GROUP_ID_READ_ONLY, GROUP_ID_USER
from homeassistant.auth.models import Group
from homeassistant.auth.permissions import POLICY_SCHEMA
from homeassistant.auth.permissions.const import (
    CAT_ENTITIES,
    POLICY_CONTROL,
    POLICY_EDIT,
    POLICY_READ,
    SUBCAT_ALL,
)
from homeassistant.auth.permissions.entities import (
    ENTITY_AREAS,
    ENTITY_DOMAINS,
    ENTITY_ENTITY_IDS,
)
from homeassistant.helpers import area_registry as ar, entity_registry as er

from .access_control import AccessControlManager

MANAGED_GROUP_PREFIX = "eshtaya_acl_"
LEVELS = {"none", "read", "control", "edit"}


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _level_policy(level: str) -> dict[str, bool] | None:
    if level == "none":
        return None
    if level == "read":
        return {POLICY_READ: True}
    if level == "control":
        return {POLICY_READ: True, POLICY_CONTROL: True}
    if level == "edit":
        return {POLICY_READ: True, POLICY_CONTROL: True, POLICY_EDIT: True}
    raise ValueError(f"Unknown Home Assistant access level: {level}")


def _clean_level(value: Any) -> str:
    value = str(value or "none").lower().strip()
    if value not in LEVELS:
        raise ValueError(f"Invalid access level: {value}")
    return value


def _clean_mapping(raw: Any) -> dict[str, str]:
    if not isinstance(raw, dict):
        return {}
    result: dict[str, str] = {}
    for key, value in raw.items():
        name = str(key or "").strip()
        if not name:
            continue
        level = _clean_level(value)
        if level != "none":
            result[name] = level
    return result


class HomeAssistantAccessManager:
    """Safely manage native HA user groups and restricted entity policies."""

    def __init__(self, hass, metadata: AccessControlManager) -> None:
        self.hass = hass
        self.metadata = metadata

    def _auth_store(self):
        store = getattr(self.hass.auth, "_store", None)
        groups = getattr(store, "_groups", None)
        save = getattr(store, "_async_schedule_save", None)
        if store is None or not isinstance(groups, dict) or not callable(save):
            return None
        return store

    def compatibility(self) -> dict[str, Any]:
        store = self._auth_store()
        return {
            "native_permissions": True,
            "custom_restricted_groups": store is not None,
            "backend_enforced": True,
            "storage_file_direct_edit": False,
            "limitations": [
                "Home Assistant native policies are additive grants; they do not support explicit deny rules.",
                "Native policies cover entity read/control/edit. Home Assistant core does not currently expose general custom per-service/dashboard RBAC.",
            ],
        }

    @staticmethod
    def _managed_group_id(user_id: str) -> str:
        safe = re.sub(r"[^a-zA-Z0-9]+", "", user_id)[:48]
        return f"{MANAGED_GROUP_PREFIX}{safe}"

    def _build_policy(self, rules: dict[str, Any]) -> dict[str, Any]:
        base = _clean_level(rules.get("base", "none"))
        domains = _clean_mapping(rules.get("domains"))
        areas = _clean_mapping(rules.get("areas"))
        entities = _clean_mapping(rules.get("entities"))

        entity_policy: dict[str, Any] = {}
        base_policy = _level_policy(base)
        if base_policy is not None:
            entity_policy[SUBCAT_ALL] = base_policy
        for policy_key, values in (
            (ENTITY_DOMAINS, domains),
            (ENTITY_AREAS, areas),
            (ENTITY_ENTITY_IDS, entities),
        ):
            scoped: dict[str, Any] = {}
            for object_id, level in values.items():
                grant = _level_policy(level)
                if grant is not None:
                    scoped[object_id] = grant
            if scoped:
                entity_policy[policy_key] = scoped

        policy = {CAT_ENTITIES: entity_policy}
        # Validate against the exact schema Home Assistant itself uses.
        POLICY_SCHEMA(policy)
        return policy

    async def _target(self, user_id: str):
        target = await self.hass.auth.async_get_user(user_id)
        if target is None:
            raise ValueError("Home Assistant user not found")
        return target

    @staticmethod
    def _group_ids(user) -> list[str]:
        return [group.id for group in getattr(user, "groups", [])]

    def _guard_change(self, actor, target, mode: str) -> None:
        if actor is None or not getattr(actor, "is_admin", False):
            raise ValueError("Home Assistant administrator required")
        if getattr(target, "is_owner", False):
            raise ValueError("The Home Assistant Owner account cannot be modified")
        if getattr(target, "system_generated", False):
            raise ValueError("System-generated users cannot be modified")
        if getattr(actor, "id", None) == getattr(target, "id", None):
            raise ValueError("You cannot change your own Home Assistant access from this panel")
        if target.is_admin and not getattr(actor, "is_owner", False):
            raise ValueError("Only the Home Assistant Owner can change another administrator")
        if mode == "administrator" and not getattr(actor, "is_owner", False):
            raise ValueError("Only the Home Assistant Owner can grant Administrator access")

    async def _ensure_backup(self, actor, target) -> dict[str, Any]:
        record = self.metadata.ha_access_record(target.id)
        if record.get("original_group_ids") is not None:
            return record
        return await self.metadata.async_update_ha_access_record(
            actor,
            target.id,
            {
                "original_group_ids": self._group_ids(target),
                "original_captured_at": _utcnow(),
            },
            action="ha_access_backup_created",
        )

    def _upsert_managed_group(self, target, policy: dict[str, Any]) -> str:
        store = self._auth_store()
        if store is None:
            raise ValueError(
                "This Home Assistant version does not expose the loaded AuthStore structure required for restricted custom groups"
            )
        group_id = self._managed_group_id(target.id)
        group = store._groups.get(group_id)
        if group is None:
            group = Group(
                id=group_id,
                name=f"Eshtaya Restricted · {target.name or target.id}",
                policy=policy,
                system_generated=False,
            )
            store._groups[group_id] = group
        else:
            if getattr(group, "system_generated", False):
                raise ValueError("Managed group id conflicts with a protected Home Assistant group")
            group.name = f"Eshtaya Restricted · {target.name or target.id}"
            group.policy = policy

        for user in getattr(store, "_users", {}).values():
            if any(item.id == group_id for item in user.groups):
                user.invalidate_cache()
        store._async_schedule_save()
        return group_id

    def _remove_managed_group_if_unused(self, group_id: str) -> None:
        if not group_id.startswith(MANAGED_GROUP_PREFIX):
            return
        store = self._auth_store()
        if store is None or group_id not in store._groups:
            return
        if any(
            any(group.id == group_id for group in user.groups)
            for user in getattr(store, "_users", {}).values()
        ):
            return
        store._groups.pop(group_id, None)
        store._async_schedule_save()

    async def async_apply(
        self,
        actor,
        user_id: str,
        mode: str,
        rules: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        mode = str(mode or "").strip().lower()
        if mode not in {"standard", "read_only", "administrator", "restricted", "no_entity_access"}:
            raise ValueError("Unknown Home Assistant access mode")
        target = await self._target(user_id)
        self._guard_change(actor, target, mode)
        await self._ensure_backup(actor, target)

        old_group_ids = self._group_ids(target)
        managed_group_id: str | None = None
        normalized_rules: dict[str, Any] | None = None

        if mode == "standard":
            group_ids = [GROUP_ID_USER]
        elif mode == "read_only":
            group_ids = [GROUP_ID_READ_ONLY]
        elif mode == "administrator":
            group_ids = [GROUP_ID_ADMIN]
        else:
            normalized_rules = {
                "base": "none" if mode == "no_entity_access" else _clean_level((rules or {}).get("base", "none")),
                "domains": {} if mode == "no_entity_access" else _clean_mapping((rules or {}).get("domains")),
                "areas": {} if mode == "no_entity_access" else _clean_mapping((rules or {}).get("areas")),
                "entities": {} if mode == "no_entity_access" else _clean_mapping((rules or {}).get("entities")),
            }
            policy = self._build_policy(normalized_rules)
            managed_group_id = self._upsert_managed_group(target, policy)
            group_ids = [managed_group_id]

        await self.hass.auth.async_update_user(target, group_ids=group_ids)
        target.invalidate_cache()

        for previous in old_group_ids:
            if previous.startswith(MANAGED_GROUP_PREFIX) and previous != managed_group_id:
                self._remove_managed_group_if_unused(previous)

        await self.metadata.async_update_ha_access_record(
            actor,
            target.id,
            {
                "managed": True,
                "mode": mode,
                "managed_group_id": managed_group_id,
                "rules": normalized_rules,
                "current_group_ids": group_ids,
                "applied_at": _utcnow(),
            },
            action="ha_native_access_applied",
        )
        return await self.async_user_status(target.id)

    async def async_restore(self, actor, user_id: str) -> dict[str, Any]:
        target = await self._target(user_id)
        self._guard_change(actor, target, "restore")
        record = self.metadata.ha_access_record(user_id)
        original = record.get("original_group_ids")
        if original is None:
            raise ValueError("No Home Assistant access backup exists for this user")

        store = self._auth_store()
        known_groups = getattr(store, "_groups", {}) if store is not None else {}
        valid = [group_id for group_id in original if group_id in known_groups]
        if not valid:
            valid = [GROUP_ID_USER]
        if GROUP_ID_ADMIN in valid and not getattr(actor, "is_owner", False):
            raise ValueError("Only the Home Assistant Owner can restore Administrator access")

        old_group_ids = self._group_ids(target)
        await self.hass.auth.async_update_user(target, group_ids=valid)
        target.invalidate_cache()
        for previous in old_group_ids:
            if previous.startswith(MANAGED_GROUP_PREFIX):
                self._remove_managed_group_if_unused(previous)

        await self.metadata.async_update_ha_access_record(
            actor,
            target.id,
            {
                "managed": False,
                "mode": "restored",
                "managed_group_id": None,
                "rules": None,
                "current_group_ids": valid,
                "restored_at": _utcnow(),
            },
            action="ha_native_access_restored",
        )
        return await self.async_user_status(target.id)

    async def async_user_status(self, user_id: str) -> dict[str, Any]:
        user = await self._target(user_id)
        record = self.metadata.ha_access_record(user_id)
        return {
            "id": user.id,
            "name": user.name or user.id,
            "is_owner": bool(getattr(user, "is_owner", False)),
            "is_admin": bool(user.is_admin),
            "is_active": bool(getattr(user, "is_active", True)),
            "system_generated": bool(getattr(user, "system_generated", False)),
            "group_ids": self._group_ids(user),
            "managed": bool(record.get("managed")),
            "mode": record.get("mode"),
            "rules": deepcopy(record.get("rules")),
            "has_backup": record.get("original_group_ids") is not None,
            "original_group_ids": deepcopy(record.get("original_group_ids")),
        }

    async def async_snapshot(self) -> dict[str, Any]:
        users = [
            await self.async_user_status(user.id)
            for user in await self.hass.auth.async_get_users()
            if not getattr(user, "system_generated", False)
        ]
        users.sort(key=lambda item: str(item.get("name") or "").casefold())

        store = self._auth_store()
        groups = []
        if store is not None:
            for group in store._groups.values():
                groups.append(
                    {
                        "id": group.id,
                        "name": group.name or group.id,
                        "system_generated": bool(group.system_generated),
                        "managed": group.id.startswith(MANAGED_GROUP_PREFIX),
                    }
                )
        groups.sort(key=lambda item: str(item["name"]).casefold())

        area_registry = ar.async_get(self.hass)
        areas = [
            {"id": area.id, "name": area.name}
            for area in area_registry.async_list_areas()
        ]
        areas.sort(key=lambda item: item["name"].casefold())

        entity_registry = er.async_get(self.hass)
        entity_ids = set(entity_registry.entities)
        entity_ids.update(self.hass.states.async_entity_ids())
        entities = []
        domains = set()
        for entity_id in sorted(entity_ids):
            domain = entity_id.partition(".")[0]
            domains.add(domain)
            entry = entity_registry.async_get(entity_id)
            state = self.hass.states.get(entity_id)
            attributes = state.attributes if state else {}
            entities.append(
                {
                    "entity_id": entity_id,
                    "domain": domain,
                    "name": (
                        (entry.name if entry else None)
                        or attributes.get("friendly_name")
                        or (entry.original_name if entry else None)
                        or entity_id
                    ),
                    "area_id": (entry.area_id if entry else None),
                }
            )

        return {
            "compatibility": self.compatibility(),
            "levels": ["none", "read", "control", "edit"],
            "users": users,
            "groups": groups,
            "areas": areas,
            "domains": sorted(domains),
            "entities": entities,
        }
