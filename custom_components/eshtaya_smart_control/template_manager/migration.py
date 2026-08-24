"""Transactional migration from standalone eshtaya_template_manager."""
from __future__ import annotations

import asyncio
import json
import logging
import shutil
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from homeassistant.config_entries import ConfigEntryDisabler
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import LEGACY_DOMAIN, LEGACY_SENSOR
from .store import TemplateManagerStore

_LOGGER = logging.getLogger(__name__)


class LegacyTemplateMigration:
    """Move the old manager into Smart Control without running two engines."""

    def __init__(self, hass: HomeAssistant, store: TemplateManagerStore) -> None:
        self.hass = hass
        self.store = store
        self._prepared = False
        self._legacy_entries = []
        self._records: list[dict[str, Any]] = []
        self._registry_backup: dict[str, dict[str, Any]] = {}
        self._previous_records: list[dict[str, Any]] = []
        self._backup_dir: Path | None = None

    def _capture_records(self) -> list[dict[str, Any]]:
        state = self.hass.states.get(LEGACY_SENSOR)
        attrs = dict(state.attributes) if state else {}
        managed = attrs.get("managed") or []
        records: list[dict[str, Any]] = []
        for raw in managed:
            if not isinstance(raw, dict):
                continue
            entity_id = str(raw.get("entity_id") or "").strip()
            source = str(raw.get("source_entity") or "").strip()
            if not entity_id or not source:
                continue
            template_type = str(raw.get("type") or entity_id.split(".", 1)[0]).lower()
            if template_type not in {"light", "fan"}:
                continue
            records.append(
                {
                    "entity_id": entity_id,
                    "source_entity": source,
                    "type": template_type,
                    "name": str(raw.get("name") or entity_id),
                    "unique_id": str(raw.get("unique_id") or f"esc_template::{entity_id}"),
                    "legacy_unique_id": raw.get("unique_id"),
                }
            )
        return records

    def _capture_registry(self, records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        registry = er.async_get(self.hass)
        result: dict[str, dict[str, Any]] = {}
        for record in records:
            entity_id = str(record["entity_id"])
            entry = registry.async_get(entity_id)
            if not entry:
                continue
            result[entity_id] = {
                "entity_id": entity_id,
                "unique_id": entry.unique_id,
                "platform": entry.platform,
                "config_entry_id": entry.config_entry_id,
                "name": entry.name,
                "icon": entry.icon,
                "area_id": entry.area_id,
                "disabled_by": entry.disabled_by.value if entry.disabled_by else None,
                "hidden_by": entry.hidden_by.value if entry.hidden_by else None,
                "labels": sorted(entry.labels),
            }
        return result

    async def _backup(self, records: list[dict[str, Any]], registry_data: dict[str, dict[str, Any]]) -> Path:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        root = Path(self.hass.config.path("eshtaya_smart_control_backups", f"template_manager_{stamp}"))
        legacy_dir = Path(self.hass.config.path("custom_components", LEGACY_DOMAIN))

        def _copy() -> None:
            root.mkdir(parents=True, exist_ok=True)
            payload = {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "legacy_domain": LEGACY_DOMAIN,
                "records": records,
                "registry": registry_data,
                "config_entries": [
                    {
                        "entry_id": entry.entry_id,
                        "title": entry.title,
                        "data": dict(entry.data),
                        "options": dict(entry.options),
                    }
                    for entry in self._legacy_entries
                ],
            }
            (root / "migration.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            if legacy_dir.exists():
                shutil.copytree(legacy_dir, root / "custom_components" / LEGACY_DOMAIN, dirs_exist_ok=True)

        await self.hass.async_add_executor_job(_copy)
        return root

    async def async_prepare(self) -> dict[str, Any]:
        """Capture, back up and quiesce legacy runtime before new platforms load."""
        migration_state = self.store.migration()
        if migration_state.get("completed"):
            return migration_state

        self._legacy_entries = list(self.hass.config_entries.async_entries(LEGACY_DOMAIN))
        sensor_exists = self.hass.states.get(LEGACY_SENSOR) is not None
        if not self._legacy_entries and not sensor_exists:
            state = {"completed": True, "legacy_found": False, "migrated": 0}
            await self.store.async_set_migration(state)
            return state

        records = self._capture_records()
        if sensor_exists and not records:
            raise RuntimeError(
                "Legacy Template Manager was detected but its managed mappings could not be read; refusing cleanup"
            )

        self._records = records
        self._previous_records = self.store.templates()
        self._registry_backup = self._capture_registry(records)
        self._backup_dir = await self._backup(records, self._registry_backup)

        # Stop the old engine before releasing its entity IDs. This is the key zero-duplicate boundary.
        for entry in self._legacy_entries:
            self.hass.config_entries.async_update_entry(
                entry, disabled_by=ConfigEntryDisabler.INTEGRATION
            )
            try:
                await self.hass.config_entries.async_unload(entry.entry_id)
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Could not unload legacy Template Manager entry %s", entry.entry_id)

        registry = er.async_get(self.hass)
        for entity_id in self._registry_backup:
            if registry.async_get(entity_id):
                registry.async_remove(entity_id)

        await self.store.async_replace_all(records)
        state = {
            "completed": False,
            "legacy_found": True,
            "phase": "prepared",
            "migrated": len(records),
            "backup_path": str(self._backup_dir),
            "legacy_entry_ids": [entry.entry_id for entry in self._legacy_entries],
        }
        await self.store.async_set_migration(state)
        self._prepared = True
        return state

    async def async_finalize(self) -> dict[str, Any]:
        """Verify exact entity IDs then permanently remove the legacy implementation."""
        state = self.store.migration()
        if not state.get("legacy_found") or state.get("completed"):
            return state

        expected = [str(record["entity_id"]) for record in self.store.templates()]
        missing: list[str] = []
        wrong_source: list[str] = []
        registry = er.async_get(self.hass)
        for entity_id in expected:
            if self.hass.states.get(entity_id) is None:
                missing.append(entity_id)
                continue
            reg = registry.async_get(entity_id)
            if not reg or reg.platform != "eshtaya_smart_control":
                wrong_source.append(entity_id)

        if missing or wrong_source:
            raise RuntimeError(
                "Template migration verification failed; missing="
                + ",".join(missing)
                + " wrong_owner="
                + ",".join(wrong_source)
            )

        # Restore user-facing registry metadata after ownership has moved to the unified integration.
        for entity_id, old in self._registry_backup.items():
            current = registry.async_get(entity_id)
            if not current:
                continue
            changes: dict[str, Any] = {}
            for key in ("name", "icon", "area_id"):
                if old.get(key) is not None:
                    changes[key] = old[key]
            if old.get("labels"):
                changes["labels"] = set(old["labels"])
            if changes:
                registry.async_update_entity(entity_id, **changes)

        # Remove config entries only after every migrated entity has passed verification.
        for entry_id in state.get("legacy_entry_ids") or []:
            try:
                await self.hass.config_entries.async_remove(entry_id)
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Could not remove legacy Template Manager config entry %s", entry_id)

        legacy_dir = Path(self.hass.config.path("custom_components", LEGACY_DOMAIN))

        def _remove_legacy_dir() -> None:
            if legacy_dir.exists():
                shutil.rmtree(legacy_dir)

        await self.hass.async_add_executor_job(_remove_legacy_dir)
        state.update(
            {
                "completed": True,
                "phase": "completed",
                "verified": len(expected),
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "legacy_component_removed": not legacy_dir.exists(),
            }
        )
        await self.store.async_set_migration(state)
        return state

    async def async_rollback(self, reason: str) -> None:
        """Keep the backup and restore the standalone entry when verification fails."""
        if not self._prepared:
            return
        await self.store.async_replace_all(self._previous_records)
        for entry in self._legacy_entries:
            try:
                self.hass.config_entries.async_update_entry(entry, disabled_by=None)
                await self.hass.config_entries.async_reload(entry.entry_id)
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Could not restore legacy Template Manager entry %s", entry.entry_id)
        state = self.store.migration()
        state.update({"completed": False, "phase": "rolled_back", "error": reason})
        await self.store.async_set_migration(state)
