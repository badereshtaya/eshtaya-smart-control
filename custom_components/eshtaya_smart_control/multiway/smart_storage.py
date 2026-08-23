"""Persistent Smart Groups, templates, snapshots and installer settings."""
from __future__ import annotations

import asyncio
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import (
    CONTROLLER_MODES,
    MODE_EVENT,
    MODE_MIRROR,
    PERFORMANCE_MODES,
    SMART_ACTION_TYPES,
    SMART_CONTROLLER_DOMAINS,
    SMART_DEFAULT_BEHAVIOR,
    SMART_DIRECTIONS,
    SMART_FAILURE_POLICIES,
    SMART_KIND_PHYSICAL,
    SMART_KIND_VIRTUAL,
    SMART_KINDS,
    SMART_GROUP_TYPES,
    SMART_COMMANDABLE_TYPES,
    SMART_MEMBER_DOMAINS,
    SMART_SENSOR_CALC_TYPES,
    SMART_SCHEMA_VERSION,
    SMART_STATE_POLICIES,
    SMART_STORAGE_KEY,
    SMART_STORAGE_VERSION,
    VIRTUAL_LIGHT,
)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class SmartGroupStore:
    """Versioned configuration store for high-level Smart Groups."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._store: Store[dict[str, Any]] = Store(
            hass, SMART_STORAGE_VERSION, SMART_STORAGE_KEY, atomic_writes=True
        )
        self._data = self._empty()
        self._lock = asyncio.Lock()

    @staticmethod
    def _empty() -> dict[str, Any]:
        return {
            "schema_version": SMART_SCHEMA_VERSION,
            "settings": {
                "project_name": "",
                "installer_mode": True,
                "config_locked": False,
                "snapshot_limit": 25,
                "hidden_members_owned": [],
            },
            "groups": [],
            "templates": [],
            "snapshots": [],
        }

    async def async_load(self) -> None:
        loaded = await self._store.async_load()
        if not isinstance(loaded, dict):
            self._data = self._empty()
            return
        schema = loaded.get("schema_version", SMART_SCHEMA_VERSION)
        if isinstance(schema, int) and schema > SMART_SCHEMA_VERSION:
            raise ValueError(
                f"Smart Groups storage schema {schema} is newer than supported {SMART_SCHEMA_VERSION}"
            )
        data = self._empty()
        data["settings"].update(loaded.get("settings") or {})
        data["settings"]["snapshot_limit"] = max(
            5, min(100, int(data["settings"].get("snapshot_limit", 25)))
        )
        data["settings"]["hidden_members_owned"] = list(
            dict.fromkeys(data["settings"].get("hidden_members_owned") or [])
        )
        data["templates"] = list(loaded.get("templates") or [])
        data["snapshots"] = list(loaded.get("snapshots") or [])[-50:]
        for raw in loaded.get("groups") or []:
            group = self._normalize(raw, keep_id=True)
            self._validate(group)
            data["groups"].append(group)
        self._validate_controller_uniqueness(data["groups"])
        self._data = data
        await self._store.async_save(self._data)

    def groups(self) -> list[dict[str, Any]]:
        return deepcopy(self._data["groups"])

    def get(self, group_id: str) -> dict[str, Any] | None:
        for group in self._data["groups"]:
            if group["id"] == group_id:
                return deepcopy(group)
        return None

    def settings(self) -> dict[str, Any]:
        return deepcopy(self._data["settings"])

    def templates(self) -> list[dict[str, Any]]:
        return deepcopy(self._data["templates"])

    def snapshots(self) -> list[dict[str, Any]]:
        return deepcopy(self._data["snapshots"])

    async def async_create(self, payload: dict[str, Any]) -> dict[str, Any]:
        async with self._lock:
            self._assert_unlocked()
            group = self._normalize(payload, keep_id=False)
            self._validate(group)
            self._validate_controller_unique(group, None)
            self._snapshot("before_create", None)
            self._data["groups"].append(group)
            await self._save()
            return deepcopy(group)

    async def async_update(self, group_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        async with self._lock:
            self._assert_unlocked()
            existing = self.get(group_id)
            if not existing:
                raise ValueError("Smart Group not found")
            if existing.get("locked") and payload.get("locked") is not False:
                raise ValueError("This Smart Group is locked")
            merged = {**existing, **payload, "id": group_id, "updated_at": _utcnow()}
            group = self._normalize(merged, keep_id=True)
            self._validate(group)
            self._validate_controller_unique(group, group_id)
            self._snapshot("before_update", existing)
            for idx, current in enumerate(self._data["groups"]):
                if current["id"] == group_id:
                    self._data["groups"][idx] = group
                    break
            await self._save()
            return deepcopy(group)

    async def async_delete(self, group_id: str) -> None:
        async with self._lock:
            self._assert_unlocked()
            existing = self.get(group_id)
            if not existing:
                raise ValueError("Smart Group not found")
            if existing.get("locked"):
                raise ValueError("Unlock this Smart Group before deleting it")
            self._snapshot("before_delete", existing)
            self._data["groups"] = [g for g in self._data["groups"] if g["id"] != group_id]
            await self._save()

    async def async_set_enabled(self, group_id: str, enabled: bool) -> dict[str, Any]:
        """Persist the operational enable state without treating it as config editing.

        Enable/disable is a runtime safety control, so it remains available even when
        the project or group configuration is locked.
        """
        async with self._lock:
            for index, current in enumerate(self._data["groups"]):
                if current["id"] != group_id:
                    continue
                updated = deepcopy(current)
                updated["enabled"] = bool(enabled)
                updated["updated_at"] = _utcnow()
                self._data["groups"][index] = updated
                await self._save()
                return deepcopy(updated)
        raise ValueError("Smart Group not found")

    async def async_clone(self, group_id: str, name: str | None = None) -> dict[str, Any]:
        source = self.get(group_id)
        if not source:
            raise ValueError("Smart Group not found")
        if source["kind"] == SMART_KIND_PHYSICAL:
            raise ValueError(
                "Physical Smart Groups must be cloned from the Control Center so a new "
                "physical controller can be selected"
            )
        source.pop("id", None)
        source["name"] = name or f"{source['name']} Copy"
        source["locked"] = False
        return await self.async_create(source)

    async def async_set_settings(self, settings: dict[str, Any]) -> dict[str, Any]:
        async with self._lock:
            merged = {**self._data["settings"], **settings}
            merged["snapshot_limit"] = max(5, min(100, int(merged.get("snapshot_limit", 25))))
            merged["hidden_members_owned"] = list(
                dict.fromkeys(merged.get("hidden_members_owned") or [])
            )
            self._data["settings"] = merged
            await self._save()
            return deepcopy(merged)

    def hidden_members_owned(self) -> set[str]:
        """Return members whose hidden state is owned by this integration."""
        return set(self._data["settings"].get("hidden_members_owned") or [])

    async def async_set_hidden_members_owned(self, entity_ids: set[str]) -> None:
        """Persist hidden-member ownership without creating a user snapshot."""
        async with self._lock:
            self._data["settings"]["hidden_members_owned"] = sorted(entity_ids)
            await self._save()

    async def async_save_template(self, name: str, group_id: str) -> dict[str, Any]:
        group = self.get(group_id)
        if not group:
            raise ValueError("Smart Group not found")
        template = {
            "id": uuid4().hex,
            "name": name.strip() or f"{group['name']} Template",
            "created_at": _utcnow(),
            "payload": {
                "kind": group["kind"],
                "group_type": group["group_type"],
                "virtual_type": group["virtual_type"],
                "behavior": deepcopy(group["behavior"]),
                "area_id": group.get("area_id"),
            },
        }
        self._data["templates"].append(template)
        await self._save()
        return deepcopy(template)

    async def async_delete_template(self, template_id: str) -> None:
        async with self._lock:
            self._assert_unlocked()
            before = len(self._data["templates"])
            self._data["templates"] = [t for t in self._data["templates"] if t.get("id") != template_id]
            if len(self._data["templates"]) == before:
                raise ValueError("Template not found")
            await self._save()

    async def async_undo_last(self) -> dict[str, Any]:
        async with self._lock:
            self._assert_unlocked()
            if not self._data["snapshots"]:
                raise ValueError("No snapshot is available")
            snap = self._data["snapshots"][-1]
            snapshot_group_ids = {group["id"] for group in snap["groups"]}
            protected_takeovers = [
                group
                for group in self._data["groups"]
                if (group.get("migration") or {}).get("takeover")
                and group["id"] not in snapshot_group_ids
            ]
            if protected_takeovers:
                names = ", ".join(group["name"] for group in protected_takeovers[:3])
                raise ValueError(
                    "Undo cannot roll back a completed Home Assistant Group takeover "
                    f"({names}). The original helper was intentionally removed; edit or "
                    "delete the Eshtaya group explicitly instead."
                )
            snap = self._data["snapshots"].pop()
            self._data["groups"] = deepcopy(snap["groups"])
            await self._save()
            return {"restored": snap["created_at"], "reason": snap["reason"]}

    def export_data(self) -> dict[str, Any]:
        return deepcopy(self._data)

    async def async_import(self, payload: dict[str, Any], replace: bool = False) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise ValueError("Import payload must be an object")
        imported: list[dict[str, Any]] = []
        for raw in payload.get("groups") or []:
            group = self._normalize(raw, keep_id=True)
            self._validate(group)
            imported.append(group)

        imported_settings = deepcopy(self._data["settings"])
        if isinstance(payload.get("settings"), dict):
            imported_settings.update(payload["settings"])
        imported_settings["snapshot_limit"] = max(
            5, min(100, int(imported_settings.get("snapshot_limit", 25)))
        )
        imported_templates = list(payload.get("templates") or [])
        imported_snapshots = list(payload.get("snapshots") or [])[-50:]

        async with self._lock:
            self._assert_unlocked()
            if replace:
                candidate_groups = imported
                candidate_templates = imported_templates
            else:
                candidate_groups = deepcopy(self._data["groups"])
                ids = {g["id"] for g in candidate_groups}
                for group in imported:
                    group = deepcopy(group)
                    if group["id"] in ids:
                        group["id"] = uuid4().hex
                    candidate_groups.append(group)
                    ids.add(group["id"])
                candidate_templates = deepcopy(self._data["templates"])
                template_ids = {t.get("id") for t in candidate_templates}
                for template in imported_templates:
                    item = deepcopy(template)
                    if not item.get("id") or item.get("id") in template_ids:
                        item["id"] = uuid4().hex
                    candidate_templates.append(item)
                    template_ids.add(item["id"])

            protected_takeovers = [
                group
                for group in self._data["groups"]
                if (group.get("migration") or {}).get("takeover")
            ]
            candidate_ids = {group["id"] for group in candidate_groups}
            missing_takeovers = [
                group for group in protected_takeovers if group["id"] not in candidate_ids
            ]
            if missing_takeovers:
                names = ", ".join(group["name"] for group in missing_takeovers[:3])
                raise ValueError(
                    "Restore would remove a completed Home Assistant Group takeover "
                    f"({names}) whose original helper no longer exists. Include the "
                    "taken-over group in the backup or delete it explicitly first."
                )

            self._validate_controller_uniqueness(candidate_groups)
            self._snapshot("before_import", None)
            self._data["groups"] = candidate_groups
            self._data["settings"] = imported_settings
            self._data["templates"] = candidate_templates
            if replace and imported_snapshots:
                self._data["snapshots"] = imported_snapshots[-50:]
            await self._save()
        return self.export_data()

    async def async_remap_entities(self, mapping: dict[str, str]) -> dict[str, Any]:
        clean = {
            str(old).strip(): str(new).strip()
            for old, new in mapping.items()
            if str(old).strip() and str(new).strip()
        }
        if not clean:
            return self.export_data()
        async with self._lock:
            self._assert_unlocked()
            candidate = deepcopy(self._data["groups"])
            for group in candidate:
                controller = group.get("controller_entity")
                if controller in clean:
                    group["controller_entity"] = clean[controller]
                for member in group["members"]:
                    if member["entity_id"] in clean:
                        member["entity_id"] = clean[member["entity_id"]]
                group["updated_at"] = _utcnow()
                self._validate(group)
            self._validate_controller_uniqueness(candidate)
            self._snapshot("before_entity_remap", None)
            self._data["groups"] = candidate
            await self._save()
            return self.export_data()

    async def async_remove(self) -> None:
        await self._store.async_remove()
        self._data = self._empty()

    def _snapshot(self, reason: str, target: dict[str, Any] | None) -> None:
        limit = int(self._data["settings"].get("snapshot_limit", 25))
        self._data["snapshots"].append(
            {
                "id": uuid4().hex,
                "created_at": _utcnow(),
                "reason": reason,
                "target": deepcopy(target),
                "groups": deepcopy(self._data["groups"]),
            }
        )
        self._data["snapshots"] = self._data["snapshots"][-limit:]

    def _assert_unlocked(self) -> None:
        if self._data["settings"].get("config_locked"):
            raise ValueError("Configuration is locked. Unlock it from Settings first.")

    async def _save(self) -> None:
        await self._store.async_save(self._data)

    def _normalize(self, payload: dict[str, Any], *, keep_id: bool) -> dict[str, Any]:
        now = _utcnow()
        kind = payload.get("kind", SMART_KIND_VIRTUAL)
        behavior = deepcopy(SMART_DEFAULT_BEHAVIOR)
        behavior.update(payload.get("behavior") or {})
        controller = payload.get("controller_entity") or None
        controller_mode = behavior.get("controller_mode", MODE_MIRROR)
        if (
            controller
            and self._domain(controller) in {"button", "input_button", "event"}
            and controller_mode == MODE_MIRROR
        ):
            behavior["controller_mode"] = MODE_EVENT
        members = []
        seen = set()
        for item in payload.get("members") or []:
            entity_id = str(item.get("entity_id") if isinstance(item, dict) else item).strip()
            if entity_id and entity_id not in seen:
                seen.add(entity_id)
                members.append(
                    {
                        "entity_id": entity_id,
                        "enabled": bool(item.get("enabled", True)) if isinstance(item, dict) else True,
                    }
                )
        explicit_group_type = payload.get("group_type") or payload.get("virtual_type")
        inferred_group_type = (
            self._domain(members[0]["entity_id"])
            if members
            else None
        )
        group_type = str(explicit_group_type or inferred_group_type or VIRTUAL_LIGHT).strip()
        if controller and group_type in SMART_ACTION_TYPES and behavior.get("controller_mode") == MODE_MIRROR:
            # Stateless Action Groups treat a wall/button transition as a trigger,
            # never as a state to mirror.
            behavior["controller_mode"] = MODE_EVENT

        return {
            "id": payload.get("id") if keep_id else uuid4().hex,
            "name": str(payload.get("name", "")).strip(),
            "kind": kind,
            "controller_entity": str(controller).strip() if controller else None,
            "members": members,
            "group_type": group_type,
            # Kept as a compatibility alias for V2/V3 backups and old UI caches.
            "virtual_type": group_type,
            "area_id": payload.get("area_id") or None,
            "enabled": bool(payload.get("enabled", True)),
            "maintenance": bool(payload.get("maintenance", False)),
            "locked": bool(payload.get("locked", False)),
            "favorite": bool(payload.get("favorite", False)),
            "source_group_entity": (
                str(payload.get("source_group_entity")).strip()
                if payload.get("source_group_entity")
                else None
            ),
            "preferred_entity_id": (
                str(payload.get("preferred_entity_id")).strip()
                if payload.get("preferred_entity_id")
                else None
            ),
            "hide_members": bool(payload.get("hide_members", False)),
            "migration": deepcopy(payload.get("migration")) if isinstance(payload.get("migration"), dict) else None,
            "behavior": behavior,
            "created_at": payload.get("created_at") or now,
            "updated_at": payload.get("updated_at") or now,
        }

    def _validate(self, group: dict[str, Any]) -> None:
        if not group.get("id") or not group.get("name"):
            raise ValueError("Smart Group name is required")
        if group["kind"] not in SMART_KINDS:
            raise ValueError("Unsupported Smart Group kind")
        group_type = group.get("group_type") or group.get("virtual_type")
        if group_type not in SMART_GROUP_TYPES:
            raise ValueError(f"Unsupported Smart Group type: {group_type}")
        if not group["members"]:
            raise ValueError("At least one member is required")
        ids = [m["entity_id"] for m in group["members"]]
        if len(ids) != len(set(ids)):
            raise ValueError("A member cannot appear twice")
        for entity_id in ids:
            domain = self._domain(entity_id)
            if domain not in SMART_MEMBER_DOMAINS:
                raise ValueError(f"Unsupported Smart Group member: {entity_id}")
            if domain != group_type:
                raise ValueError(
                    f"{entity_id} is a {domain} entity, but this is a {group_type} group"
                )
        self._validate_member_compatibility(group)
        if group["kind"] == SMART_KIND_PHYSICAL:
            if group_type not in SMART_COMMANDABLE_TYPES or group_type == "notify":
                raise ValueError(
                    f"Physical-controller mode is not supported for {group_type} groups"
                )
            controller = group.get("controller_entity")
            if not controller or self._domain(controller) not in SMART_CONTROLLER_DOMAINS:
                raise ValueError("Physical Smart Group requires a supported controller entity")
            if controller in ids:
                raise ValueError("The physical controller cannot also be a member")
        behavior = group["behavior"]
        if behavior.get("state_policy") not in SMART_STATE_POLICIES:
            raise ValueError("Unsupported state policy")
        if behavior.get("direction") not in SMART_DIRECTIONS:
            raise ValueError("Unsupported direction")
        if behavior.get("controller_mode") not in CONTROLLER_MODES:
            raise ValueError("Unsupported controller mode")
        if behavior.get("performance_mode") not in PERFORMANCE_MODES:
            raise ValueError("Unsupported performance mode")
        if behavior.get("failure_policy") not in SMART_FAILURE_POLICIES:
            raise ValueError("Unsupported failure policy")
        if behavior.get("sensor_calc_type", "mean") not in SMART_SENSOR_CALC_TYPES:
            raise ValueError("Unsupported sensor calculation type")
        for key, low, high in (
            ("command_timeout", 0.25, 30),
            ("max_retries", 0, 5),
            ("member_delay_ms", 0, 5000),
            ("manual_priority_ms", 0, 10000),
            ("source_stable_ms", 50, 2000),
            ("scene_guard_ms", 0, 10000),
            ("flap_threshold", 3, 50),
            ("flap_window_sec", 1, 120),
            ("quarantine_sec", 5, 3600),
            ("command_echo_ms", 250, 15000),
            ("action_cooldown_ms", 0, 5000),
            ("scene_transition", 0, 300),
        ):
            value = float(behavior.get(key, SMART_DEFAULT_BEHAVIOR[key]))
            if not low <= value <= high:
                raise ValueError(f"{key} is outside the supported range")

        if behavior.get("action_execution", "parallel") not in {"parallel", "sequential"}:
            raise ValueError("Unsupported Action Group execution mode")
        if not isinstance(behavior.get("action_data", {}), dict):
            raise ValueError("Action Group data must be a JSON object")

    def _compatibility_signature(self, entity_id: str, group_type: str) -> tuple[Any, ...] | None:
        """Return the strict compatibility signature for a Smart Group member.

        Domain equality is always mandatory. Strict mode additionally keeps
        device sub-types together when Home Assistant exposes a device class.
        Numeric sensor groups also require matching measurement semantics.
        """
        hass = getattr(self, "hass", None)
        if hass is None:
            return None
        state = hass.states.get(entity_id)
        if state is None:
            return None
        attrs = state.attributes
        device_class = attrs.get("device_class")
        if group_type == "sensor":
            # Same sensor type/state semantics are required. When Home Assistant
            # exposes a device class, its native SensorGroup can convert compatible
            # units (for example °C/°F), so unit is only a strict discriminator when
            # there is no device class to describe the measurement family.
            return (
                device_class or "",
                attrs.get("state_class") or "",
                "" if device_class else attrs.get("unit_of_measurement") or "",
            )
        if group_type in {
            "binary_sensor",
            "button",
            "cover",
            "event",
            "lock",
            "media_player",
            "switch",
            "valve",
        }:
            return (device_class or "",)
        return None

    def _validate_member_compatibility(self, group: dict[str, Any]) -> None:
        """Reject strict groups whose members have incompatible sub-types."""
        behavior = group.get("behavior") or {}
        if behavior.get("compatibility_mode", "strict") != "strict":
            return
        group_type = group.get("group_type") or group.get("virtual_type")
        baseline: tuple[Any, ...] | None = None
        baseline_entity: str | None = None
        for member in group.get("members", []):
            if not member.get("enabled", True):
                continue
            entity_id = member["entity_id"]
            signature = self._compatibility_signature(entity_id, group_type)
            if signature is None:
                continue
            if baseline is None:
                baseline = signature
                baseline_entity = entity_id
                continue
            if signature != baseline:
                raise ValueError(
                    f"{entity_id} is not the same {group_type} type as "
                    f"{baseline_entity}. Use Domain-only compatibility in Advanced "
                    "settings only when this mix is intentional."
                )

    def _validate_controller_unique(self, group: dict[str, Any], ignore_id: str | None) -> None:
        controller = group.get("controller_entity")
        if not controller:
            return
        for existing in self._data["groups"]:
            if existing["id"] == ignore_id:
                continue
            if existing.get("controller_entity") == controller:
                raise ValueError(
                    f"Controller {controller} is already assigned to {existing['name']}"
                )

    @staticmethod
    def _validate_controller_uniqueness(groups: list[dict[str, Any]]) -> None:
        used: dict[str, str] = {}
        for group in groups:
            controller = group.get("controller_entity")
            if not controller:
                continue
            if controller in used:
                raise ValueError(f"Controller {controller} is already assigned to {used[controller]}")
            used[controller] = group["name"]

    @staticmethod
    def _domain(entity_id: str) -> str:
        return entity_id.split(".", 1)[0] if isinstance(entity_id, str) and "." in entity_id else ""
