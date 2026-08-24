"""Transactional migration from the standalone Eshtaya Template Manager."""
from __future__ import annotations

import asyncio
import json
import logging
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from homeassistant.config_entries import ConfigEntryDisabler
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import LEGACY_DOMAIN, LEGACY_SENSOR
from .store import TemplateManagerStore

_LOGGER = logging.getLogger(__name__)
LEGACY_RUNTIME_WAIT_SECONDS = 90
LEGACY_RUNTIME_POLL_SECONDS = 2
LEGACY_RELEASE_WAIT_SECONDS = 20
SWITCH_RE = re.compile(r"\bswitch\.[a-zA-Z0-9_]+\b")

# Files created by the original permanent-entity workflow. These are treated as
# migration sources, not merely cleanup candidates.
LEGACY_GENERATED_RELATIVE_PATHS = (
    "packages/eshtaya_generated_templates.yaml",
    "packages/eshtaya_generated_lights.yaml",
    "eshtaya_template_manager/generated_templates.yaml",
    "eshtaya_template_manager/templates.json",
    "eshtaya_template_manager/mappings.json",
)


class LegacyTemplateMigration:
    """Move the old manager into Smart Control without duplicate entity engines."""

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

    @property
    def config_root(self) -> Path:
        return Path(self.hass.config.config_dir)

    def _generated_paths(self) -> list[Path]:
        return [self.config_root / rel for rel in LEGACY_GENERATED_RELATIVE_PATHS]

    def _legacy_paths(self) -> list[Path]:
        config = self.config_root
        paths: list[Path] = []
        fixed = [
            config / "custom_components" / LEGACY_DOMAIN,
            config / LEGACY_DOMAIN,
            config / "www" / "eshtaya-template-manager.js",
            config / "www" / "eshtaya-template-manager-card.js",
            *self._generated_paths(),
        ]
        paths.extend(path for path in fixed if path.exists())
        for pattern in (
            f".storage/{LEGACY_DOMAIN}*",
            f"packages/{LEGACY_DOMAIN}*.yaml",
            "packages/eshtaya_template*.yaml",
            "packages/eshtaya_generated_*.yaml",
        ):
            paths.extend(path for path in config.glob(pattern) if path.exists())
        return list(dict.fromkeys(paths))

    def _legacy_sensor_is_external(self) -> bool:
        registry = er.async_get(self.hass)
        entry = registry.async_get(LEGACY_SENSOR)
        if entry is None:
            return self.hass.states.get(LEGACY_SENSOR) is not None
        return entry.platform != "eshtaya_smart_control"

    def _legacy_evidence(self) -> bool:
        return bool(
            self._legacy_entries
            or self._legacy_paths()
            or self._legacy_sensor_is_external()
            or self.hass.services.has_service(LEGACY_DOMAIN, "scan")
        )

    async def _wait_for_legacy_runtime(self) -> None:
        """Give the old YAML/custom integration time to expose its runtime sensor."""
        if not self._legacy_evidence() or self._legacy_sensor_is_external():
            return
        deadline = self.hass.loop.time() + LEGACY_RUNTIME_WAIT_SECONDS
        while self.hass.loop.time() < deadline:
            if self._legacy_sensor_is_external():
                return
            await asyncio.sleep(LEGACY_RUNTIME_POLL_SECONDS)

    @staticmethod
    def _record(
        entity_id: str,
        source_entity: str,
        *,
        name: str | None = None,
        unique_id: str | None = None,
        origin: str,
    ) -> dict[str, Any] | None:
        entity_id = str(entity_id or "").strip()
        source_entity = str(source_entity or "").strip()
        if "." not in entity_id or not source_entity.startswith("switch."):
            return None
        template_type = entity_id.split(".", 1)[0].lower()
        if template_type not in {"light", "fan"}:
            return None
        return {
            "entity_id": entity_id,
            "source_entity": source_entity,
            "type": template_type,
            "name": str(name or entity_id),
            "unique_id": f"esc_template::{entity_id}",
            "legacy_unique_id": unique_id,
            "migration_origin": origin,
        }

    def _capture_runtime_records(self) -> list[dict[str, Any]]:
        if not self._legacy_sensor_is_external():
            return []
        state = self.hass.states.get(LEGACY_SENSOR)
        attrs = dict(state.attributes) if state else {}
        records: list[dict[str, Any]] = []
        for raw in attrs.get("managed") or []:
            if not isinstance(raw, dict):
                continue
            record = self._record(
                raw.get("entity_id"),
                raw.get("source_entity"),
                name=raw.get("name"),
                unique_id=raw.get("unique_id"),
                origin="legacy_runtime",
            )
            if record:
                records.append(record)
        return records

    @staticmethod
    def _switch_from_object(value: Any) -> str | None:
        if isinstance(value, str):
            match = SWITCH_RE.search(value)
            return match.group(0) if match else None
        if isinstance(value, dict):
            # Prefer explicit service targets because they are the most reliable source mapping.
            for key in ("entity_id", "target", "data", "turn_on", "turn_off", "state"):
                if key in value:
                    found = LegacyTemplateMigration._switch_from_object(value[key])
                    if found:
                        return found
            for child in value.values():
                found = LegacyTemplateMigration._switch_from_object(child)
                if found:
                    return found
        if isinstance(value, list):
            for child in value:
                found = LegacyTemplateMigration._switch_from_object(child)
                if found:
                    return found
        return None

    def _records_from_json_value(self, value: Any, origin: str) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        if isinstance(value, dict):
            entity_id = value.get("entity_id") or value.get("managed_entity")
            source = value.get("source_entity") or value.get("source")
            if entity_id and source:
                record = self._record(
                    entity_id,
                    source,
                    name=value.get("name"),
                    unique_id=value.get("unique_id"),
                    origin=origin,
                )
                if record:
                    records.append(record)
            # mappings.json may be a simple {"light.foo": "switch.foo"} mapping.
            for key, child in value.items():
                if isinstance(key, str) and key.startswith(("light.", "fan.")) and isinstance(child, str):
                    record = self._record(key, child, origin=origin)
                    if record:
                        records.append(record)
                records.extend(self._records_from_json_value(child, origin))
        elif isinstance(value, list):
            for child in value:
                records.extend(self._records_from_json_value(child, origin))
        return records

    def _records_from_yaml_value(self, value: Any, origin: str) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        if isinstance(value, dict):
            default_entity_id = value.get("default_entity_id") or value.get("entity_id")
            if isinstance(default_entity_id, str) and default_entity_id.startswith(("light.", "fan.")):
                source = self._switch_from_object(value)
                if source:
                    record = self._record(
                        default_entity_id,
                        source,
                        name=value.get("name"),
                        unique_id=value.get("unique_id"),
                        origin=origin,
                    )
                    if record:
                        records.append(record)
            for child in value.values():
                records.extend(self._records_from_yaml_value(child, origin))
        elif isinstance(value, list):
            for child in value:
                records.extend(self._records_from_yaml_value(child, origin))
        return records

    def _capture_file_records_sync(self) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for path in self._generated_paths():
            if not path.exists() or not path.is_file():
                continue
            try:
                if path.suffix.lower() == ".json":
                    value = json.loads(path.read_text(encoding="utf-8"))
                    records.extend(self._records_from_json_value(value, str(path)))
                else:
                    value = yaml.safe_load(path.read_text(encoding="utf-8"))
                    records.extend(self._records_from_yaml_value(value, str(path)))
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Could not parse legacy Template Manager source %s", path)
        return records

    async def _capture_records(self) -> list[dict[str, Any]]:
        file_records = await self.hass.async_add_executor_job(self._capture_file_records_sync)
        runtime_records = self._capture_runtime_records()
        # File records provide startup-independent recovery; a live runtime record wins
        # because it reflects the exact mapping the old manager is currently using.
        merged: dict[str, dict[str, Any]] = {}
        for record in [*file_records, *runtime_records]:
            merged[str(record["entity_id"])] = record
        return list(merged.values())

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
        if sensor_entry and sensor_entry.platform != "eshtaya_smart_control":
            self._sensor_registry_backup = self._registry_row(sensor_entry)
        return result

    async def _backup(self, records: list[dict[str, Any]], registry_data: dict[str, dict[str, Any]]) -> Path:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        root = Path(self.hass.config.path("eshtaya_smart_control_backups", f"template_manager_{stamp}"))
        config = self.config_root
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

    async def _remove_legacy_services(self) -> None:
        for service in list(self.hass.services.async_services().get(LEGACY_DOMAIN, {})):
            self.hass.services.async_remove(LEGACY_DOMAIN, service)

    async def _remove_legacy_paths(self, paths: list[Path]) -> list[str]:
        config = self.config_root.resolve()

        def _remove() -> list[str]:
            failed: list[str] = []
            for path in paths:
                try:
                    path.resolve().relative_to(config)
                    if path.is_dir():
                        shutil.rmtree(path)
                    elif path.exists():
                        path.unlink()
                except (OSError, ValueError):
                    _LOGGER.exception("Could not remove legacy Template Manager path %s", path)
                    failed.append(str(path))
            return failed

        return await self.hass.async_add_executor_job(_remove)

    def _occupied_legacy_entities(self, records: list[dict[str, Any]]) -> list[str]:
        registry = er.async_get(self.hass)
        occupied: list[str] = []
        for record in records:
            entity_id = str(record["entity_id"])
            state = self.hass.states.get(entity_id)
            reg = registry.async_get(entity_id)
            if state is not None and (reg is None or reg.platform != "eshtaya_smart_control"):
                occupied.append(entity_id)
        return occupied

    async def _wait_for_legacy_entities_to_release(self, records: list[dict[str, Any]]) -> list[str]:
        deadline = self.hass.loop.time() + LEGACY_RELEASE_WAIT_SECONDS
        while self.hass.loop.time() < deadline:
            occupied = self._occupied_legacy_entities(records)
            if not occupied:
                return []
            await asyncio.sleep(1)
        return self._occupied_legacy_entities(records)

    async def _resume_staged_migration(self, prior: dict[str, Any]) -> dict[str, Any]:
        records = self.store.templates()
        occupied = self._occupied_legacy_entities(records)
        if occupied:
            prior.update({
                "completed": False,
                "legacy_found": True,
                "phase": "restart_required",
                "restart_required": True,
                "occupied_entities": occupied,
            })
            await self.store.async_set_migration(prior)
            return prior

        registry = er.async_get(self.hass)
        cleaned: list[dict[str, Any]] = []
        for record in records:
            item = dict(record)
            item.pop("deferred", None)
            entity_id = str(item["entity_id"])
            reg = registry.async_get(entity_id)
            if reg and reg.platform != "eshtaya_smart_control":
                registry.async_remove(entity_id)
            cleaned.append(item)
        await self.store.async_replace_all(cleaned)
        prior.update({
            "phase": "prepared",
            "restart_required": False,
            "occupied_entities": [],
            "resumed_at": datetime.now(timezone.utc).isoformat(),
        })
        await self.store.async_set_migration(prior)
        self._records = cleaned
        self._prepared = True
        return prior

    async def async_prepare(self) -> dict[str, Any]:
        """Capture, back up, stop old definitions and prepare exact-ID takeover."""
        prior = self.store.migration()
        if prior.get("phase") == "restart_required":
            return await self._resume_staged_migration(prior)

        self._legacy_entries = list(self.hass.config_entries.async_entries(LEGACY_DOMAIN))
        if not self._legacy_evidence():
            if prior.get("completed"):
                return prior
            state = {"completed": True, "legacy_found": False, "phase": "not_found", "migrated": 0}
            await self.store.async_set_migration(state)
            return state

        await self._wait_for_legacy_runtime()
        records = await self._capture_records()
        if not records:
            raise RuntimeError(
                "Legacy Template Manager was detected but no permanent entity mappings could be recovered from its runtime or generated files; refusing cleanup"
            )

        if self._legacy_sensor_is_external():
            attrs = self.hass.states.get(LEGACY_SENSOR).attributes if self.hass.states.get(LEGACY_SENSOR) else {}
            reported = int(attrs.get("managed_count") or len(attrs.get("managed") or []))
            runtime_records = self._capture_runtime_records()
            if reported and len(runtime_records) != reported:
                raise RuntimeError(
                    f"Legacy Template Manager reports {reported} managed entities but only {len(runtime_records)} runtime mappings were readable; refusing cleanup"
                )

        self._records = records
        self._previous_records = self.store.templates()
        self._registry_backup = self._capture_registry(records)
        self._backup_dir = await self._backup(records, self._registry_backup)
        legacy_paths = self._legacy_paths()

        # Config-entry legacy installs can be unloaded cleanly. YAML/non-config-entry
        # installs are neutralized by removing their generated files after backup.
        for entry in self._legacy_entries:
            self.hass.config_entries.async_update_entry(entry, disabled_by=ConfigEntryDisabler.INTEGRATION)
            unloaded = await self.hass.config_entries.async_unload(entry.entry_id)
            if unloaded is False:
                raise RuntimeError(f"Could not unload legacy Template Manager entry {entry.entry_id}")

        await self._remove_legacy_services()
        failed_cleanup = await self._remove_legacy_paths(legacy_paths)
        if failed_cleanup:
            raise RuntimeError("Could not remove all legacy Template Manager files: " + ", ".join(failed_cleanup))

        # Old permanent entities were generated as Home Assistant template entities.
        # Reloading template after removing the generated package releases them without
        # requiring a second restart on normal installations.
        if self.hass.services.has_service("template", "reload"):
            try:
                await self.hass.services.async_call("template", "reload", {}, blocking=True)
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Template reload failed during Template Manager migration")

        occupied = await self._wait_for_legacy_entities_to_release(records)
        if occupied:
            staged = [{**record, "deferred": True} for record in records]
            await self.store.async_replace_all(staged)
            state = {
                "completed": False,
                "legacy_found": True,
                "phase": "restart_required",
                "restart_required": True,
                "migrated": len(records),
                "backup_path": str(self._backup_dir),
                "legacy_entry_ids": [entry.entry_id for entry in self._legacy_entries],
                "legacy_paths": [str(path) for path in legacy_paths],
                "occupied_entities": occupied,
                "message": "Legacy generated entities are still loaded in memory. Legacy files are removed and a Home Assistant restart will complete the exact-ID takeover.",
            }
            await self.store.async_set_migration(state)
            self._prepared = True
            return state

        registry = er.async_get(self.hass)
        for entity_id in [*self._registry_backup, LEGACY_SENSOR]:
            reg = registry.async_get(entity_id)
            if reg and reg.platform != "eshtaya_smart_control":
                registry.async_remove(entity_id)

        await self.store.async_replace_all(records)
        state = {
            "completed": False,
            "legacy_found": True,
            "phase": "prepared",
            "restart_required": False,
            "migrated": len(records),
            "backup_path": str(self._backup_dir),
            "legacy_entry_ids": [entry.entry_id for entry in self._legacy_entries],
            "legacy_paths": [str(path) for path in legacy_paths],
            "occupied_entities": [],
        }
        await self.store.async_set_migration(state)
        self._prepared = True
        return state

    async def async_finalize(self) -> dict[str, Any]:
        """Verify exact entity IDs before permanently completing the migration."""
        state = self.store.migration()
        if not state.get("legacy_found") or state.get("completed"):
            return state
        if state.get("phase") == "restart_required":
            return state

        expected = [
            str(record["entity_id"])
            for record in self.store.templates()
            if not record.get("deferred")
        ]
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
            try:
                await self.hass.config_entries.async_remove(entry_id)
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Could not remove legacy Template Manager config entry %s", entry_id)

        remaining = [str(path) for path in self._legacy_paths() if path.exists()]
        state.update({
            "completed": True,
            "phase": "completed",
            "restart_required": False,
            "verified": len(expected),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "legacy_component_removed": not remaining,
            "remaining_legacy_paths": remaining,
        })
        await self.store.async_set_migration(state)
        return state

    async def _restore_backup_files(self) -> None:
        if not self._backup_dir:
            return
        source = self._backup_dir / "legacy_files"
        config = self.config_root

        def _restore() -> None:
            if not source.exists():
                return
            for child in source.rglob("*"):
                if not child.is_file():
                    continue
                rel = child.relative_to(source)
                destination = config / rel
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(child, destination)

        await self.hass.async_add_executor_job(_restore)

    async def async_rollback(self, reason: str) -> None:
        """Restore old files/config entry when a prepared migration fails."""
        if not self._prepared:
            return
        registry = er.async_get(self.hass)
        for record in self._records:
            entity_id = str(record.get("entity_id") or "")
            current = registry.async_get(entity_id) if entity_id else None
            if current and current.platform == "eshtaya_smart_control":
                registry.async_remove(entity_id)
        sensor_entry = registry.async_get(LEGACY_SENSOR)
        if sensor_entry and sensor_entry.platform == "eshtaya_smart_control":
            registry.async_remove(LEGACY_SENSOR)

        await self.store.async_replace_all(self._previous_records)
        await self._restore_backup_files()
        if self.hass.services.has_service("template", "reload"):
            try:
                await self.hass.services.async_call("template", "reload", {}, blocking=True)
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Could not reload template integration during rollback")

        for entry in self._legacy_entries:
            try:
                self.hass.config_entries.async_update_entry(entry, disabled_by=None)
                await self.hass.config_entries.async_reload(entry.entry_id)
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Could not restore legacy Template Manager entry %s", entry.entry_id)
        state = self.store.migration()
        state.update({"completed": False, "phase": "rolled_back", "error": reason})
        await self.store.async_set_migration(state)
