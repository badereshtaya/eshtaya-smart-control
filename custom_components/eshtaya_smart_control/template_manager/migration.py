"""Transactional migration from standalone eshtaya_template_manager."""
from __future__ import annotations

import asyncio
import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from homeassistant.config_entries import ConfigEntryDisabler
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import LEGACY_DOMAIN, LEGACY_SENSOR
from .store import TemplateManagerStore

_LOGGER = logging.getLogger(__name__)
LEGACY_RUNTIME_WAIT_SECONDS = 90
LEGACY_RUNTIME_POLL_SECONDS = 2


class LegacyTemplateMigration:
    """Move the old manager into Smart Control without running two engines."""

    def __init__(self, hass: HomeAssistant, store: TemplateManagerStore) -> None:
        self.hass = hass
        self.store = store
        self._prepared = False
        self._legacy_entries = []
        self._records: list[dict[str, Any]] = []
        self._registry_backup: dict[str, dict[str, Any]] = {}
        self._sensor_registry_backup: dict[str, Any] | None = None
        self._previous_records: list[dict[str, Any]] = []
        self._backup_dir: Path | None = None

    def _legacy_paths(self) -> list[Path]:
        config = Path(self.hass.config.config_dir)
        paths: list[Path] = []
        fixed = [
            config / "custom_components" / LEGACY_DOMAIN,
            config / LEGACY_DOMAIN,
            config / "www" / "eshtaya-template-manager.js",
            config / "www" / "eshtaya-template-manager-card.js",
        ]
        paths.extend(path for path in fixed if path.exists())
        for pattern in (
            f".storage/{LEGACY_DOMAIN}*",
            f"packages/{LEGACY_DOMAIN}*.yaml",
            "packages/eshtaya_template*.yaml",
        ):
            paths.extend(path for path in config.glob(pattern) if path.exists())
        return list(dict.fromkeys(paths))

    async def _wait_for_legacy_runtime(self) -> None:
        if self.hass.states.get(LEGACY_SENSOR) is not None or not self._legacy_entries:
            return
        deadline = self.hass.loop.time() + LEGACY_RUNTIME_WAIT_SECONDS
        while self.hass.loop.time() < deadline:
            if self.hass.states.get(LEGACY_SENSOR) is not None:
                return
            await asyncio.sleep(LEGACY_RUNTIME_POLL_SECONDS)

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
            records.append({
                "entity_id": entity_id,
                "source_entity": source,
                "type": template_type,
                "name": str(raw.get("name") or entity_id),
                "unique_id": f"esc_template::{entity_id}",
                "legacy_unique_id": raw.get("unique_id"),
            })
        return records

    @staticmethod
    def _registry_row(entry) -> dict[str, Any]:
        return {
            "entity_id": entry.entity_id,
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

    def _capture_registry(self, records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        registry = er.async_get(self.hass)
        result: dict[str, dict[str, Any]] = {}
        for record in records:
            entry = registry.async_get(str(record["entity_id"]))
            if entry:
                result[entry.entity_id] = self._registry_row(entry)
        sensor_entry = registry.async_get(LEGACY_SENSOR)
        self._sensor_registry_backup = self._registry_row(sensor_entry) if sensor_entry else None
        return result

    async def _backup(self, records: list[dict[str, Any]], registry_data: dict[str, dict[str, Any]]) -> Path:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        root = Path(self.hass.config.path("eshtaya_smart_control_backups", f"template_manager_{stamp}"))
        config = Path(self.hass.config.config_dir)
        legacy_paths = self._legacy_paths()

        def _copy() -> None:
            root.mkdir(parents=True, exist_ok=True)
            payload = {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "legacy_domain": LEGACY_DOMAIN,
                "records": records,
                "registry": registry_data,
                "sensor_registry": self._sensor_registry_backup,
                "legacy_paths": [str(path) for path in legacy_paths],
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
            (root / "migration.json").write_text(
                json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
            )
            files_root = root / "legacy_files"
            for path in legacy_paths:
                try:
                    rel = path.relative_to(config)
                except ValueError:
                    continue
                destination = files_root / rel
                destination.parent.mkdir(parents=True, exist_ok=True)
                if path.is_dir():
                    shutil.copytree(path, destination, dirs_exist_ok=True)
                else:
                    shutil.copy2(path, destination)

        await self.hass.async_add_executor_job(_copy)
        return root

    async def async_prepare(self) -> dict[str, Any]:
        """Capture, back up and quiesce legacy runtime before new platforms load."""
        self._legacy_entries = list(self.hass.config_entries.async_entries(LEGACY_DOMAIN))
        legacy_files = self._legacy_paths()
        sensor_exists = self.hass.states.get(LEGACY_SENSOR) is not None
        if not self._legacy_entries and not legacy_files and not sensor_exists:
            state = {"completed": True, "legacy_found": False, "phase": "not_found", "migrated": 0}
            await self.store.async_set_migration(state)
            return state

        await self._wait_for_legacy_runtime()
        sensor_exists = self.hass.states.get(LEGACY_SENSOR) is not None
        records = self._capture_records()
        if self._legacy_entries and not sensor_exists:
            raise RuntimeError(
                "Legacy Template Manager config entry exists but sensor.eshtaya_template_manager did not become ready; refusing cleanup"
            )
        if sensor_exists:
            attrs = self.hass.states[LEGACY_SENSOR].attributes
            reported_managed = int(attrs.get("managed_count") or len(attrs.get("managed") or []))
            if reported_managed and len(records) != reported_managed:
                raise RuntimeError(
                    f"Legacy Template Manager reports {reported_managed} managed entities but only {len(records)} mappings were readable; refusing cleanup"
                )

        self._records = records
        self._previous_records = self.store.templates()
        self._registry_backup = self._capture_registry(records)
        self._backup_dir = await self._backup(records, self._registry_backup)

        for entry in self._legacy_entries:
            self.hass.config_entries.async_update_entry(entry, disabled_by=ConfigEntryDisabler.INTEGRATION)
            unloaded = await self.hass.config_entries.async_unload(entry.entry_id)
            if unloaded is False:
                raise RuntimeError(f"Could not unload legacy Template Manager entry {entry.entry_id}")

        registry = er.async_get(self.hass)
        for entity_id in [*self._registry_backup, LEGACY_SENSOR]:
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
            "legacy_paths": [str(path) for path in legacy_files],
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
        wrong_owner: list[str] = []
        registry = er.async_get(self.hass)
        for entity_id in expected:
            if self.hass.states.get(entity_id) is None:
                missing.append(entity_id)
                continue
            reg = registry.async_get(entity_id)
            if not reg or reg.platform != "eshtaya_smart_control":
                wrong_owner.append(entity_id)

        sensor_state = self.hass.states.get(LEGACY_SENSOR)
        sensor_registry = registry.async_get(LEGACY_SENSOR)
        if sensor_state is None or not sensor_registry or sensor_registry.platform != "eshtaya_smart_control":
            missing.append(LEGACY_SENSOR)

        if missing or wrong_owner:
            raise RuntimeError(
                "Template migration verification failed; missing="
                + ",".join(missing)
                + " wrong_owner="
                + ",".join(wrong_owner)
            )

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

        for entry_id in state.get("legacy_entry_ids") or []:
            await self.hass.config_entries.async_remove(entry_id)

        config = Path(self.hass.config.config_dir)
        backup_root = Path(str(state.get("backup_path") or ""))
        paths_to_remove = [Path(path) for path in state.get("legacy_paths") or []]

        def _remove_legacy_files() -> None:
            for path in paths_to_remove:
                try:
                    path.resolve().relative_to(config.resolve())
                    if backup_root and backup_root in path.parents:
                        continue
                    if path.is_dir():
                        shutil.rmtree(path)
                    elif path.exists():
                        path.unlink()
                except (OSError, ValueError):
                    _LOGGER.exception("Could not remove legacy Template Manager path %s", path)

        await self.hass.async_add_executor_job(_remove_legacy_files)
        remaining = [str(path) for path in paths_to_remove if path.exists()]
        state.update({
            "completed": True,
            "phase": "completed",
            "verified": len(expected),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "legacy_component_removed": not remaining,
            "remaining_legacy_paths": remaining,
        })
        await self.store.async_set_migration(state)
        return state

    async def async_rollback(self, reason: str) -> None:
        """Remove new registry ownership before restoring the standalone engine."""
        if not self._prepared:
            return
        registry = er.async_get(self.hass)
        # The caller should unload unified platforms first. This registry cleanup is an
        # additional guard so the old integration cannot be assigned *_2 Entity IDs.
        for record in self._records:
            entity_id = str(record.get("entity_id") or "")
            current = registry.async_get(entity_id) if entity_id else None
            if current and current.platform == "eshtaya_smart_control":
                registry.async_remove(entity_id)
        sensor_entry = registry.async_get(LEGACY_SENSOR)
        if sensor_entry and sensor_entry.platform == "eshtaya_smart_control":
            registry.async_remove(LEGACY_SENSOR)

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
