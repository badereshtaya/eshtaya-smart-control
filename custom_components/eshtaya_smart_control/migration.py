"""Safe first-run migration from legacy Eshtaya integrations."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntryDisabler
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN
from .entity_control.const import STORAGE_KEY as ENTITY_STORAGE_KEY
from .multiway.const import (
    SMART_STORAGE_KEY,
    SMART_STORAGE_VERSION,
    STORAGE_KEY as MULTIWAY_STORAGE_KEY,
    STORAGE_VERSION as MULTIWAY_STORAGE_VERSION,
)

_LOGGER = logging.getLogger(__name__)

LEGACY_ENTITY_DOMAIN = "eshtaya_entity_manager"
LEGACY_MULTIWAY_DOMAIN = "eshtaya_multiway"
LEGACY_ENTITY_STORAGE_KEY = LEGACY_ENTITY_DOMAIN
LEGACY_MULTIWAY_STORAGE_KEY = f"{LEGACY_MULTIWAY_DOMAIN}.groups"
LEGACY_SMART_STORAGE_KEY = f"{LEGACY_MULTIWAY_DOMAIN}.smart_groups"

MIGRATION_STORE_KEY = f"{DOMAIN}.migration"
MIGRATION_BACKUP_KEY = f"{DOMAIN}.migration_backup"
MIGRATION_VERSION = 1


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _entry_snapshot(entry) -> dict[str, Any]:
    return {
        "entry_id": entry.entry_id,
        "domain": entry.domain,
        "title": entry.title,
        "unique_id": entry.unique_id,
        "disabled_by": entry.disabled_by.value if entry.disabled_by else None,
        "data": dict(entry.data),
        "options": dict(entry.options),
    }


def _count_entity_rules(data: Any) -> int:
    if not isinstance(data, dict):
        return 0
    rules = data.get("entity_rules")
    return len(rules) if isinstance(rules, dict) else 0


def _count_groups(data: Any) -> int:
    if not isinstance(data, dict):
        return 0
    groups = data.get("groups")
    return len(groups) if isinstance(groups, list) else 0


def _has_payload(data: Any) -> bool:
    if not isinstance(data, dict) or not data:
        return False
    if _count_entity_rules(data) or _count_groups(data):
        return True
    if data.get("templates"):
        return True
    domains = data.get("domains") or data.get("domain_rules")
    return bool(domains)


class LegacyMigrationCoordinator:
    """Move legacy data transactionally and retire legacy config entries."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._store: Store[dict[str, Any]] = Store(
            hass, MIGRATION_VERSION, MIGRATION_STORE_KEY, atomic_writes=True
        )
        self._backup_store: Store[dict[str, Any]] = Store(
            hass, MIGRATION_VERSION, MIGRATION_BACKUP_KEY, atomic_writes=True
        )
        self.state: dict[str, Any] = {}

    async def async_prepare(self) -> dict[str, Any]:
        """Detect legacy integrations, back them up, and copy storage if safe."""
        saved = await self._store.async_load()
        if isinstance(saved, dict) and saved.get("completed"):
            self.state = saved
            return deepcopy(self.state)

        entity_entries = self.hass.config_entries.async_entries(LEGACY_ENTITY_DOMAIN)
        multiway_entries = self.hass.config_entries.async_entries(LEGACY_MULTIWAY_DOMAIN)
        entries = [*entity_entries, *multiway_entries]

        legacy_entity = await Store(
            self.hass, 1, LEGACY_ENTITY_STORAGE_KEY
        ).async_load()
        legacy_multiway = await Store(
            self.hass, MULTIWAY_STORAGE_VERSION, LEGACY_MULTIWAY_STORAGE_KEY
        ).async_load()
        legacy_smart = await Store(
            self.hass, SMART_STORAGE_VERSION, LEGACY_SMART_STORAGE_KEY
        ).async_load()

        legacy_found = bool(entries) or any(
            _has_payload(item) for item in (legacy_entity, legacy_multiway, legacy_smart)
        )
        if not legacy_found:
            self.state = {
                "version": MIGRATION_VERSION,
                "completed": True,
                "phase": "no_legacy",
                "completed_at": _utcnow(),
                "legacy_found": False,
                "removed_entries": [],
            }
            await self._store.async_save(self.state)
            return deepcopy(self.state)

        backup = {
            "version": MIGRATION_VERSION,
            "created_at": _utcnow(),
            "entries": [_entry_snapshot(entry) for entry in entries],
            "entity_control": deepcopy(legacy_entity),
            "multiway": deepcopy(legacy_multiway),
            "smart_groups": deepcopy(legacy_smart),
        }
        await self._backup_store.async_save(backup)

        copied = {
            "entity_control": False,
            "multiway": False,
            "smart_groups": False,
        }

        new_entity_store = Store(self.hass, 1, ENTITY_STORAGE_KEY, atomic_writes=True)
        new_entity = await new_entity_store.async_load()
        if _has_payload(legacy_entity) and not _has_payload(new_entity):
            await new_entity_store.async_save(deepcopy(legacy_entity))
            copied["entity_control"] = True

        new_multiway_store = Store(
            self.hass,
            MULTIWAY_STORAGE_VERSION,
            MULTIWAY_STORAGE_KEY,
            atomic_writes=True,
        )
        new_multiway = await new_multiway_store.async_load()
        if _has_payload(legacy_multiway) and not _has_payload(new_multiway):
            await new_multiway_store.async_save(deepcopy(legacy_multiway))
            copied["multiway"] = True

        new_smart_store = Store(
            self.hass, SMART_STORAGE_VERSION, SMART_STORAGE_KEY, atomic_writes=True
        )
        new_smart = await new_smart_store.async_load()
        if _has_payload(legacy_smart) and not _has_payload(new_smart):
            await new_smart_store.async_save(deepcopy(legacy_smart))
            copied["smart_groups"] = True

        self.state = {
            "version": MIGRATION_VERSION,
            "completed": False,
            "phase": "prepared",
            "prepared_at": _utcnow(),
            "legacy_found": True,
            "entries": [_entry_snapshot(entry) for entry in entries],
            "copied": copied,
            "expected": {
                "entity_rules": _count_entity_rules(legacy_entity),
                "multiway_groups": _count_groups(legacy_multiway),
                "smart_groups": _count_groups(legacy_smart),
            },
            "backup_store": MIGRATION_BACKUP_KEY,
            "removed_entries": [],
            "errors": [],
        }
        await self._store.async_save(self.state)
        return deepcopy(self.state)

    async def async_quiesce_legacy(self) -> dict[str, Any]:
        """Unload active legacy engines without deleting anything yet."""
        if self.state.get("completed") or not self.state.get("legacy_found"):
            return deepcopy(self.state)

        disabled_by_us: list[str] = []
        for item in self.state.get("entries", []):
            entry_id = item.get("entry_id")
            if not entry_id or item.get("disabled_by") is not None:
                continue
            entry = self.hass.config_entries.async_get_entry(entry_id)
            if entry is None:
                continue
            success = await self.hass.config_entries.async_set_disabled_by(
                entry_id, ConfigEntryDisabler.USER
            )
            if not success:
                raise RuntimeError(f"Could not safely unload legacy entry {entry_id}")
            disabled_by_us.append(entry_id)

        self.state["disabled_by_migration"] = disabled_by_us
        self.state["phase"] = "legacy_disabled"
        self.state["legacy_disabled_at"] = _utcnow()
        await self._store.async_save(self.state)
        return deepcopy(self.state)

    async def async_validate(self, runtime: dict[str, Any] | None = None) -> dict[str, Any]:
        """Verify that migrated data is available in the new integration."""
        expected = self.state.get("expected") or {}
        errors: list[str] = []

        entity_data = await Store(self.hass, 1, ENTITY_STORAGE_KEY).async_load()
        if self.state.get("copied", {}).get("entity_control"):
            actual = _count_entity_rules(entity_data)
            wanted = int(expected.get("entity_rules") or 0)
            if actual < wanted:
                errors.append(f"Entity rules: expected {wanted}, got {actual}")

        runtime = runtime or {}
        multi_store = runtime.get("store")
        smart_store = runtime.get("smart_store")

        if self.state.get("copied", {}).get("multiway"):
            actual = len(multi_store.groups()) if multi_store else -1
            wanted = int(expected.get("multiway_groups") or 0)
            if actual < wanted:
                errors.append(f"Multi-Way groups: expected {wanted}, got {actual}")

        if self.state.get("copied", {}).get("smart_groups"):
            actual = len(smart_store.groups()) if smart_store else -1
            wanted = int(expected.get("smart_groups") or 0)
            if actual < wanted:
                errors.append(f"Smart Groups: expected {wanted}, got {actual}")

        result = {
            "ok": not errors,
            "errors": errors,
            "expected": deepcopy(expected),
        }
        self.state["validation"] = result
        self.state["phase"] = "validated" if result["ok"] else "validation_failed"
        self.state["validated_at"] = _utcnow()
        self.state["errors"] = errors
        await self._store.async_save(self.state)
        return deepcopy(result)

    async def async_finalize(self, runtime: dict[str, Any] | None = None) -> dict[str, Any]:
        """Remove legacy config entries only after successful validation."""
        if self.state.get("completed"):
            return deepcopy(self.state)
        validation = self.state.get("validation") or {}
        if not validation.get("ok"):
            raise RuntimeError("Legacy migration cannot finalize before successful validation")

        removed: list[dict[str, Any]] = []
        for item in self.state.get("entries", []):
            entry_id = item.get("entry_id")
            if not entry_id:
                continue
            entry = self.hass.config_entries.async_get_entry(entry_id)
            if entry is None:
                continue
            try:
                result = await self.hass.config_entries.async_remove(entry_id)
            except Exception as err:  # noqa: BLE001 - preserve migration state for recovery
                _LOGGER.exception("Failed to remove legacy config entry %s", entry_id)
                self.state["phase"] = "cleanup_partial"
                self.state.setdefault("errors", []).append(f"Remove {entry_id}: {err}")
                await self._store.async_save(self.state)
                raise
            removed.append({"entry_id": entry_id, "domain": item.get("domain"), "result": result})

        # Legacy Multi-Way removal may release registry visibility it owned.
        # Reconcile once more so the new Smart Group engine becomes the owner.
        runtime = runtime or {}
        smart_manager = runtime.get("smart_manager")
        if smart_manager is not None:
            await smart_manager.async_reload()

        self.state["removed_entries"] = removed
        self.state["phase"] = "completed"
        self.state["completed"] = True
        self.state["completed_at"] = _utcnow()
        await self._store.async_save(self.state)
        return deepcopy(self.state)

    async def async_rollback(self, reason: str) -> dict[str, Any]:
        """Re-enable legacy entries disabled by this migration when cutover fails."""
        restored: list[str] = []
        for entry_id in self.state.get("disabled_by_migration", []):
            entry = self.hass.config_entries.async_get_entry(entry_id)
            if entry is None:
                continue
            try:
                await self.hass.config_entries.async_set_disabled_by(entry_id, None)
                restored.append(entry_id)
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Failed to re-enable legacy entry %s", entry_id)

        self.state["phase"] = "rolled_back"
        self.state["completed"] = False
        self.state["rollback_at"] = _utcnow()
        self.state["rollback_reason"] = reason
        self.state["restored_entries"] = restored
        self.state.setdefault("errors", []).append(reason)
        await self._store.async_save(self.state)
        return deepcopy(self.state)

    async def async_public_status(self) -> dict[str, Any]:
        """Return a credential-free migration status for the UI."""
        data = self.state or await self._store.async_load() or {}
        entries = data.get("entries") or []
        return {
            "legacy_found": bool(data.get("legacy_found")),
            "completed": bool(data.get("completed")),
            "phase": data.get("phase", "not_started"),
            "prepared_at": data.get("prepared_at"),
            "completed_at": data.get("completed_at"),
            "copied": deepcopy(data.get("copied") or {}),
            "expected": deepcopy(data.get("expected") or {}),
            "validation": deepcopy(data.get("validation") or {}),
            "removed_entries": [
                {"entry_id": item.get("entry_id"), "domain": item.get("domain")}
                for item in data.get("removed_entries") or []
            ],
            "legacy_entries": [
                {"entry_id": item.get("entry_id"), "domain": item.get("domain"), "title": item.get("title")}
                for item in entries
            ],
            "backup_store": data.get("backup_store"),
            "errors": list(data.get("errors") or []),
        }
