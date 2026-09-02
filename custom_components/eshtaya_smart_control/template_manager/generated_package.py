"""Manage legacy-generated Home Assistant template package files in place.

These files are not a legacy integration by themselves. They are valid user-owned
Home Assistant package files that may still define permanent Light/Fan wrappers.
Eshtaya Smart Control therefore adopts them non-destructively: records are exposed
as Managed in Template Manager, while Home Assistant's template integration remains
the runtime owner of the entity until the user explicitly runs a legacy migration.
"""
from __future__ import annotations

import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from homeassistant.core import HomeAssistant

SWITCH_RE = re.compile(r"\bswitch\.[a-zA-Z0-9_]+\b")
GENERATED_RELATIVE_PATHS = (
    "packages/eshtaya_generated_templates.yaml",
    "packages/eshtaya_generated_lights.yaml",
    "eshtaya_template_manager/generated_templates.yaml",
)


class GeneratedPackageManager:
    """Discover and safely mutate generated package templates."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    @property
    def config_root(self) -> Path:
        return Path(self.hass.config.config_dir)

    def paths(self) -> list[Path]:
        return [self.config_root / relative for relative in GENERATED_RELATIVE_PATHS]

    @staticmethod
    def _source_from(value: Any) -> str | None:
        if isinstance(value, str):
            match = SWITCH_RE.search(value)
            return match.group(0) if match else None
        if isinstance(value, dict):
            for key in ("entity_id", "target", "data", "turn_on", "turn_off", "state"):
                if key in value:
                    found = GeneratedPackageManager._source_from(value[key])
                    if found:
                        return found
            for child in value.values():
                found = GeneratedPackageManager._source_from(child)
                if found:
                    return found
        if isinstance(value, list):
            for child in value:
                found = GeneratedPackageManager._source_from(child)
                if found:
                    return found
        return None

    @staticmethod
    def _records_from(value: Any, path: Path) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        if isinstance(value, dict):
            entity_id = value.get("default_entity_id") or value.get("entity_id")
            if isinstance(entity_id, str) and entity_id.startswith(("light.", "fan.")):
                source = GeneratedPackageManager._source_from(value)
                if source:
                    records.append(
                        {
                            "entity_id": entity_id.strip(),
                            "source_entity": source,
                            "type": entity_id.split(".", 1)[0].lower(),
                            "name": str(value.get("name") or entity_id),
                            "unique_id": str(value.get("unique_id") or f"generated::{entity_id}"),
                            "external_managed": True,
                            "generated_path": str(path),
                            "management_origin": "generated_package",
                        }
                    )
            for child in value.values():
                records.extend(GeneratedPackageManager._records_from(child, path))
        elif isinstance(value, list):
            for child in value:
                records.extend(GeneratedPackageManager._records_from(child, path))
        return records

    def _scan_sync(self) -> list[dict[str, Any]]:
        merged: dict[str, dict[str, Any]] = {}
        for path in self.paths():
            if not path.is_file():
                continue
            try:
                value = yaml.safe_load(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            for record in self._records_from(value, path):
                merged[str(record["entity_id"])] = record
        return list(merged.values())

    async def async_scan(self) -> list[dict[str, Any]]:
        return await self.hass.async_add_executor_job(self._scan_sync)

    @staticmethod
    def _node_entity_id(node: dict[str, Any]) -> str:
        value = node.get("default_entity_id") or node.get("entity_id") or ""
        return str(value).strip()

    @classmethod
    def _find_node(cls, value: Any, entity_id: str) -> dict[str, Any] | None:
        if isinstance(value, dict):
            if cls._node_entity_id(value) == entity_id:
                return value
            for child in value.values():
                found = cls._find_node(child, entity_id)
                if found is not None:
                    return found
        elif isinstance(value, list):
            for child in value:
                found = cls._find_node(child, entity_id)
                if found is not None:
                    return found
        return None

    @classmethod
    def _remove_node(cls, value: Any, entity_id: str) -> bool:
        changed = False
        if isinstance(value, list):
            for index in range(len(value) - 1, -1, -1):
                child = value[index]
                if isinstance(child, dict) and cls._node_entity_id(child) == entity_id:
                    value.pop(index)
                    changed = True
                    continue
                if cls._remove_node(child, entity_id):
                    changed = True
        elif isinstance(value, dict):
            for key, child in list(value.items()):
                if isinstance(child, dict) and cls._node_entity_id(child) == entity_id:
                    del value[key]
                    changed = True
                    continue
                if cls._remove_node(child, entity_id):
                    changed = True
        return changed

    @classmethod
    def _replace_source(cls, value: Any, old_source: str, new_source: str) -> Any:
        if isinstance(value, str):
            return value.replace(old_source, new_source)
        if isinstance(value, list):
            for index, child in enumerate(value):
                value[index] = cls._replace_source(child, old_source, new_source)
            return value
        if isinstance(value, dict):
            for key, child in list(value.items()):
                value[key] = cls._replace_source(child, old_source, new_source)
            return value
        return value

    def _backup_and_write(self, path: Path, value: Any) -> None:
        relative = path.relative_to(self.config_root)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = self.config_root / "eshtaya_smart_control_backups" / "generated_packages" / stamp / relative
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup)
        temp = path.with_suffix(path.suffix + ".esc-tmp")
        temp.write_text(
            yaml.safe_dump(value, allow_unicode=True, sort_keys=False, default_flow_style=False),
            encoding="utf-8",
        )
        temp.replace(path)

    def _load_path(self, raw_path: str) -> tuple[Path, Any]:
        path = Path(raw_path).resolve()
        root = self.config_root.resolve()
        path.relative_to(root)
        if path not in [candidate.resolve() for candidate in self.paths()]:
            raise ValueError("Generated package path is not managed by Eshtaya Smart Control")
        if not path.is_file():
            raise ValueError(f"Generated package file not found: {path}")
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
        return path, value

    async def async_edit(self, record: dict[str, Any], *, name: str, entity_id: str) -> None:
        old_entity = str(record["entity_id"])
        raw_path = str(record.get("generated_path") or "")

        def _edit() -> None:
            path, value = self._load_path(raw_path)
            node = self._find_node(value, old_entity)
            if node is None:
                raise ValueError(f"Generated template not found in package: {old_entity}")
            if entity_id != old_entity and self._find_node(value, entity_id) is not None:
                raise ValueError(f"Entity ID is already defined in generated package: {entity_id}")
            if "default_entity_id" in node:
                node["default_entity_id"] = entity_id
            else:
                node["entity_id"] = entity_id
            node["name"] = name.strip() or entity_id
            self._backup_and_write(path, value)

        await self.hass.async_add_executor_job(_edit)

    async def async_relink(self, record: dict[str, Any], *, source_entity: str) -> None:
        old_entity = str(record["entity_id"])
        old_source = str(record["source_entity"])
        raw_path = str(record.get("generated_path") or "")

        def _relink() -> None:
            path, value = self._load_path(raw_path)
            node = self._find_node(value, old_entity)
            if node is None:
                raise ValueError(f"Generated template not found in package: {old_entity}")
            self._replace_source(node, old_source, source_entity)
            self._backup_and_write(path, value)

        await self.hass.async_add_executor_job(_relink)

    async def async_delete(self, record: dict[str, Any]) -> None:
        old_entity = str(record["entity_id"])
        raw_path = str(record.get("generated_path") or "")

        def _delete() -> None:
            path, value = self._load_path(raw_path)
            if not self._remove_node(value, old_entity):
                raise ValueError(f"Generated template not found in package: {old_entity}")
            self._backup_and_write(path, value)

        await self.hass.async_add_executor_job(_delete)

    async def async_reload_templates(self) -> None:
        if self.hass.services.has_service("template", "reload"):
            await self.hass.services.async_call("template", "reload", {}, blocking=True)
