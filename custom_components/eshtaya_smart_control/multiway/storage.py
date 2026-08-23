"""Persistent configuration storage for Eshtaya Multi-Way Control."""
from __future__ import annotations

import asyncio
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import (
    COMMANDABLE_DOMAINS,
    CONTROLLER_DOMAINS,
    CONTROLLER_MODES,
    DEFAULT_BEHAVIOR,
    DEFAULT_SETTINGS,
    MODE_FOLLOW,
    MODE_MIRROR,
    OUTPUT_DOMAINS,
    PERFORMANCE_MODES,
    SOURCE_POLICIES,
    SCHEMA_VERSION,
    STORAGE_KEY,
    STORAGE_VERSION,
    VALID_STATES,
    VIRTUAL_LIGHT,
    VIRTUAL_TYPES,
)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class MultiWayStore:
    """Persist groups and global settings with versioned schema migration."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._store: Store[dict[str, Any]] = Store(
            hass, STORAGE_VERSION, STORAGE_KEY, atomic_writes=True
        )
        self._data: dict[str, Any] = self._empty_data()
        self._lock = asyncio.Lock()
        self._delayed_save_task: asyncio.Task | None = None

    @staticmethod
    def _empty_data() -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "settings": deepcopy(DEFAULT_SETTINGS),
            "groups": [],
            "snapshots": [],
        }

    async def async_load(self) -> None:
        """Load and migrate persisted data."""
        loaded = await self._store.async_load()
        if not isinstance(loaded, dict):
            self._data = self._empty_data()
            return

        self._data = self._migrate(loaded)
        await self._store.async_save(self._data)

    def _migrate(self, data: dict[str, Any]) -> dict[str, Any]:
        """Normalize legacy-schema groups into the current schema without data loss."""
        schema_version = data.get("schema_version")
        if isinstance(schema_version, int) and schema_version > SCHEMA_VERSION:
            raise ValueError(
                f"Storage schema {schema_version} is newer than supported schema {SCHEMA_VERSION}"
            )
        if schema_version == SCHEMA_VERSION:
            result = self._empty_data()
            result["settings"].update(data.get("settings") or {})
            self._validate_settings(result["settings"])
            for group in data.get("groups") or []:
                # Never silently discard a current-schema group. If persisted V2
                # data is invalid, fail loading so the user can repair/restore it.
                normalized = self._normalize_group(group, keep_id=True)
                self._validate_group(normalized)
                result["groups"].append(normalized)
            result["snapshots"] = list(data.get("snapshots") or [])[-25:]
            return result

        # Legacy structure: {groups:[{id,name,main,secondaries,enabled}]}
        result = self._empty_data()
        for old in data.get("groups") or []:
            if not isinstance(old, dict):
                continue
            main = old.get("main")
            secondaries = old.get("secondaries") or []
            if not main or not secondaries:
                continue
            group = {
                "id": old.get("id") or uuid4().hex,
                "name": old.get("name") or "Migrated Multi-Way Group",
                "output": main,
                "controllers": [
                    {
                        "entity_id": entity_id,
                        "mode": MODE_MIRROR,
                        "invert": False,
                        "reflect_state": True,
                    }
                    for entity_id in secondaries
                ],
                "enabled": bool(old.get("enabled", True)),
                "virtual_type": VIRTUAL_LIGHT,
                "area_id": None,
                "behavior": deepcopy(DEFAULT_BEHAVIOR),
                "last_state": None,
                "created_at": old.get("created_at") or _utcnow(),
                "updated_at": _utcnow(),
            }
            try:
                self._validate_group(group)
            except ValueError:
                continue
            result["groups"].append(group)
        return result

    def groups(self) -> list[dict[str, Any]]:
        """Return all configured groups."""
        return deepcopy(self._data["groups"])

    def settings(self) -> dict[str, Any]:
        """Return effective global settings."""
        settings = deepcopy(DEFAULT_SETTINGS)
        settings.update(self._data.get("settings") or {})
        return settings

    def snapshots(self) -> list[dict[str, Any]]:
        """Return recent automatic configuration snapshots."""
        return deepcopy(self._data.get("snapshots") or [])

    def get(self, group_id: str) -> dict[str, Any] | None:
        """Return one group."""
        for group in self._data["groups"]:
            if group["id"] == group_id:
                return deepcopy(group)
        return None

    async def async_create(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a group."""
        async with self._lock:
            group = self._normalize_group(payload, keep_id=False)
            self._validate_group(group)
            self._validate_no_overlap(group, ignore_id=None)
            self._snapshot("before_create")
            self._data["groups"].append(group)
            await self._store.async_save(self._data)
            return deepcopy(group)

    async def async_update(self, group_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Update a group."""
        async with self._lock:
            existing = self.get(group_id)
            if existing is None:
                raise ValueError("Group not found")
            merged = {**existing, **payload, "id": group_id, "updated_at": _utcnow()}
            group = self._normalize_group(merged, keep_id=True)
            self._validate_group(group)
            self._validate_no_overlap(group, ignore_id=group_id)
            self._snapshot("before_update")
            for index, current in enumerate(self._data["groups"]):
                if current["id"] == group_id:
                    self._data["groups"][index] = group
                    break
            await self._store.async_save(self._data)
            return deepcopy(group)

    async def async_delete(self, group_id: str) -> None:
        """Delete a group."""
        async with self._lock:
            before = len(self._data["groups"])
            self._snapshot("before_delete")
            self._data["groups"] = [
                group for group in self._data["groups"] if group["id"] != group_id
            ]
            if len(self._data["groups"]) == before:
                raise ValueError("Group not found")
            await self._store.async_save(self._data)

    async def async_set_enabled(self, group_id: str, enabled: bool) -> dict[str, Any]:
        """Enable or disable a group."""
        return await self.async_update(group_id, {"enabled": bool(enabled)})

    async def async_update_settings(self, settings: dict[str, Any]) -> dict[str, Any]:
        """Update global engine settings."""
        async with self._lock:
            merged = self.settings()
            merged.update(settings)
            self._validate_settings(merged)
            self._data["settings"] = merged
            await self._store.async_save(self._data)
            return deepcopy(merged)

    def export_data(self) -> dict[str, Any]:
        """Return portable configuration data."""
        return deepcopy(self._data)

    async def async_import_data(self, payload: dict[str, Any], replace: bool) -> dict[str, Any]:
        """Import a portable backup transactionally; invalid imports never mutate live data."""
        if not isinstance(payload, dict):
            raise ValueError("Import data must be an object")
        migrated = self._migrate(payload)
        for group in migrated["groups"]:
            self._validate_group(group)

        async with self._lock:
            self._snapshot("before_import")
            if replace:
                candidate = deepcopy(migrated)
                candidate["snapshots"] = deepcopy(self._data.get("snapshots") or [])
            else:
                candidate = deepcopy(self._data)
                current_ids = {group["id"] for group in candidate["groups"]}
                used_entities = {
                    entity_id
                    for group in candidate["groups"]
                    for entity_id in {
                        group["output"],
                        *(controller["entity_id"] for controller in group["controllers"]),
                        *([group["behavior"].get("fallback_output")] if group["behavior"].get("fallback_output") else []),
                    }
                }
                for imported in migrated["groups"]:
                    group = deepcopy(imported)
                    if group["id"] in current_ids:
                        group["id"] = uuid4().hex
                    requested = {
                        group["output"],
                        *(controller["entity_id"] for controller in group["controllers"]),
                        *([group["behavior"].get("fallback_output")] if group["behavior"].get("fallback_output") else []),
                    }
                    overlap = used_entities & requested
                    if overlap:
                        raise ValueError(
                            f"Entity {sorted(overlap)[0]} is already used by another group"
                        )
                    candidate["groups"].append(group)
                    current_ids.add(group["id"])
                    used_entities.update(requested)

                merged_settings = deepcopy(DEFAULT_SETTINGS)
                merged_settings.update(candidate.get("settings") or {})
                merged_settings.update(migrated.get("settings") or {})
                self._validate_settings(merged_settings)
                candidate["settings"] = merged_settings
                candidate["schema_version"] = SCHEMA_VERSION

            # Validate all overlaps in the final candidate, including replace imports.
            seen: set[str] = set()
            for group in candidate["groups"]:
                used = {
                    group["output"],
                    *(controller["entity_id"] for controller in group["controllers"]),
                }
                overlap = seen & used
                if overlap:
                    raise ValueError(f"Entity {sorted(overlap)[0]} is used more than once")
                seen.update(used)
            self._validate_settings(candidate["settings"])

            self._data = candidate
            await self._store.async_save(self._data)
            return self.export_data()

    async def async_undo_last(self) -> dict[str, Any]:
        """Restore the most recent automatic configuration snapshot."""
        async with self._lock:
            snapshots = self._data.get("snapshots") or []
            if not snapshots:
                raise ValueError("No snapshot is available")
            snap = snapshots.pop()
            groups = deepcopy(snap.get("groups") or [])
            for group in groups:
                self._validate_group(group)
            self._data["groups"] = groups
            await self._store.async_save(self._data)
            return {"restored": snap.get("created_at"), "reason": snap.get("reason")}

    async def async_remap_entities(self, mapping: dict[str, str]) -> dict[str, Any]:
        """Replace entity IDs transactionally across Multi-Way groups."""
        if not isinstance(mapping, dict) or not mapping:
            raise ValueError("A non-empty entity mapping is required")
        async with self._lock:
            self._snapshot("before_remap")
            candidate = deepcopy(self._data["groups"])
            for group in candidate:
                if group["output"] in mapping:
                    group["output"] = mapping[group["output"]]
                fallback = group["behavior"].get("fallback_output")
                if fallback in mapping:
                    group["behavior"]["fallback_output"] = mapping[fallback]
                for controller in group["controllers"]:
                    if controller["entity_id"] in mapping:
                        controller["entity_id"] = mapping[controller["entity_id"]]
                group["updated_at"] = _utcnow()
                self._validate_group(group)
            seen: set[str] = set()
            for group in candidate:
                used = {group["output"], *(c["entity_id"] for c in group["controllers"])}
                fallback = group["behavior"].get("fallback_output")
                if fallback:
                    used.add(fallback)
                overlap = seen & used
                if overlap:
                    raise ValueError(f"Entity {sorted(overlap)[0]} is used more than once")
                seen.update(used)
            self._data["groups"] = candidate
            await self._store.async_save(self._data)
            return self.export_data()

    def _snapshot(self, reason: str) -> None:
        snapshots = self._data.setdefault("snapshots", [])
        snapshots.append({
            "created_at": _utcnow(),
            "reason": reason,
            "groups": deepcopy(self._data.get("groups") or []),
        })
        del snapshots[:-25]

    def set_last_state(self, group_id: str, state: str) -> None:
        """Persist last confirmed group state with a short write debounce."""
        if state not in VALID_STATES:
            return
        for group in self._data["groups"]:
            if group["id"] == group_id:
                if group.get("last_state") == state:
                    return
                group["last_state"] = state
                group["updated_at"] = _utcnow()
                self._schedule_save()
                return

    def _schedule_save(self) -> None:
        if self._delayed_save_task and not self._delayed_save_task.done():
            self._delayed_save_task.cancel()
        self._delayed_save_task = self.hass.async_create_task(self._async_delayed_save())

    async def _async_delayed_save(self) -> None:
        try:
            await asyncio.sleep(2)
            await self._store.async_save(self._data)
        except asyncio.CancelledError:
            raise

    async def async_close(self) -> None:
        """Flush delayed persistence on unload."""
        if self._delayed_save_task and not self._delayed_save_task.done():
            self._delayed_save_task.cancel()
            try:
                await self._delayed_save_task
            except asyncio.CancelledError:
                pass
        await self._store.async_save(self._data)

    async def async_remove(self) -> None:
        """Remove persistent integration data after the config entry is deleted."""
        if self._delayed_save_task and not self._delayed_save_task.done():
            self._delayed_save_task.cancel()
            try:
                await self._delayed_save_task
            except asyncio.CancelledError:
                pass
        await self._store.async_remove()
        self._data = self._empty_data()

    def _normalize_group(self, payload: dict[str, Any], *, keep_id: bool) -> dict[str, Any]:
        now = _utcnow()
        controllers: list[dict[str, Any]] = []
        for raw in payload.get("controllers") or []:
            if isinstance(raw, str):
                raw = {"entity_id": raw, "mode": MODE_MIRROR}
            if not isinstance(raw, dict):
                continue
            entity_id = str(raw.get("entity_id", "")).strip()
            domain = self._entity_domain(entity_id)
            mode = raw.get("mode", MODE_MIRROR)
            # Button/input_button/event entities expose press/event timestamps rather than
            # ON/OFF state, so make the common default useful automatically.
            if domain in {"button", "input_button", "event"} and mode == MODE_MIRROR:
                mode = "event"
            default_reflect = mode in {MODE_MIRROR, MODE_FOLLOW}
            reflect_state = bool(raw.get("reflect_state", default_reflect))
            if domain not in COMMANDABLE_DOMAINS:
                reflect_state = False
            controllers.append(
                {
                    "entity_id": entity_id,
                    "mode": mode,
                    "invert": bool(raw.get("invert", False)),
                    "reflect_state": reflect_state,
                }
            )

        behavior = deepcopy(DEFAULT_BEHAVIOR)
        behavior.update(payload.get("behavior") or {})
        group = {
            "id": payload.get("id") if keep_id else uuid4().hex,
            "name": str(payload.get("name", "")).strip(),
            "output": str(payload.get("output", payload.get("main", ""))).strip(),
            "controllers": controllers,
            "enabled": bool(payload.get("enabled", True)),
            "virtual_type": payload.get("virtual_type", VIRTUAL_LIGHT),
            "area_id": payload.get("area_id") or None,
            "behavior": behavior,
            "last_state": payload.get("last_state")
            if payload.get("last_state") in VALID_STATES
            else None,
            "created_at": payload.get("created_at") or now,
            "updated_at": payload.get("updated_at") or now,
        }
        return group

    @staticmethod
    def _entity_domain(entity_id: str) -> str:
        if not isinstance(entity_id, str) or "." not in entity_id:
            return ""
        return entity_id.split(".", 1)[0]

    def _validate_group(self, group: dict[str, Any]) -> None:
        if not group["name"]:
            raise ValueError("Group name is required")
        if len(group["name"]) > 100:
            raise ValueError("Group name is too long")
        if not group.get("id"):
            raise ValueError("Group id is required")

        output_domain = self._entity_domain(group["output"])
        if output_domain not in OUTPUT_DOMAINS:
            raise ValueError(
                "Output must be a switch, light, input_boolean, or fan entity"
            )
        if not group["controllers"]:
            raise ValueError("At least one controller is required")
        if group["virtual_type"] not in VIRTUAL_TYPES:
            raise ValueError("virtual_type must be light or switch")

        entity_ids: list[str] = []
        for controller in group["controllers"]:
            entity_id = controller["entity_id"]
            domain = self._entity_domain(entity_id)
            if domain not in CONTROLLER_DOMAINS:
                raise ValueError(f"Unsupported controller entity: {entity_id}")
            if controller["mode"] not in CONTROLLER_MODES:
                raise ValueError(f"Unsupported controller mode: {controller['mode']}")
            if controller["reflect_state"] and domain not in COMMANDABLE_DOMAINS:
                raise ValueError(
                    f"Controller {entity_id} cannot reflect state because it is not commandable"
                )
            entity_ids.append(entity_id)

        if group["output"] in entity_ids:
            raise ValueError("Output cannot also be a controller")
        if len(entity_ids) != len(set(entity_ids)):
            raise ValueError("A controller can only be added once per group")

        behavior = group["behavior"]
        debounce = int(behavior.get("debounce_ms", 120))
        if not 0 <= debounce <= 5000:
            raise ValueError("debounce_ms must be between 0 and 5000")
        authority_window = int(behavior.get("authority_window_ms", 1800))
        if not 0 <= authority_window <= 10000:
            raise ValueError("authority_window_ms must be between 0 and 10000")
        rapid_settle = int(behavior.get("rapid_settle_ms", 2600))
        if not 250 <= rapid_settle <= 10000:
            raise ValueError("rapid_settle_ms must be between 250 and 10000")
        source_stable = int(behavior.get("source_stable_ms", 220))
        if not 50 <= source_stable <= 2000:
            raise ValueError("source_stable_ms must be between 50 and 2000")
        if source_stable >= rapid_settle:
            raise ValueError("source_stable_ms must be lower than rapid_settle_ms")
        if behavior.get("output_restore_policy") not in {"adopt", "enforce"}:
            raise ValueError("output_restore_policy must be adopt or enforce")
        if behavior.get("performance_mode") not in PERFORMANCE_MODES:
            raise ValueError("performance_mode must be instant, balanced, or safe")
        if behavior.get("source_policy", "latest_physical") not in SOURCE_POLICIES:
            raise ValueError("source_policy must be latest_physical or output_authority")
        fallback = behavior.get("fallback_output")
        if fallback:
            if self._entity_domain(fallback) not in OUTPUT_DOMAINS:
                raise ValueError("fallback_output must be a switch, light, input_boolean, or fan")
            if fallback == group["output"] or fallback in entity_ids:
                raise ValueError("Fallback output must be different from the output and controllers")
        for key in ("command_timeout", "max_retries"):
            value = behavior.get(key)
            if value is not None and float(value) < 0:
                raise ValueError(f"{key} cannot be negative")

    def _validate_no_overlap(self, group: dict[str, Any], ignore_id: str | None) -> None:
        requested = {group["output"], *(c["entity_id"] for c in group["controllers"])}
        fallback = group["behavior"].get("fallback_output")
        if fallback:
            requested.add(fallback)
        for existing in self._data["groups"]:
            if existing["id"] == ignore_id:
                continue
            used = {existing["output"], *(c["entity_id"] for c in existing["controllers"])}
            existing_fallback = existing["behavior"].get("fallback_output")
            if existing_fallback:
                used.add(existing_fallback)
            overlap = requested & used
            if overlap:
                entity_id = sorted(overlap)[0]
                raise ValueError(f"Entity {entity_id} is already used by group '{existing['name']}'")

    @staticmethod
    def _validate_settings(settings: dict[str, Any]) -> None:
        checks = {
            "startup_delay": (0, 120),
            "watchdog_interval": (10, 3600),
            "command_timeout": (0.5, 30),
            "max_retries": (0, 5),
            "history_size": (20, 1000),
            "repair_threshold": (1, 20),
        }
        for key, (minimum, maximum) in checks.items():
            value = float(settings[key])
            if not minimum <= value <= maximum:
                raise ValueError(f"{key} must be between {minimum} and {maximum}")
