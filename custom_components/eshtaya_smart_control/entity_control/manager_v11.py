"""v1.1 enhancements: dual YAML outputs plus legacy rule import/export."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
from typing import Any

import yaml

from homeassistant.core import HomeAssistant

from .const import (
    PUBLIC_BACKUP_FILE,
    PUBLIC_HIDDEN_FILE,
    RULE_ALLOW,
    RULE_EXCLUDE,
    RULES_BACKUP_FILE,
)
from .manager import EntityManager


class EntityManagerV11(EntityManager):
    """Entity manager with synchronized public YAML and rules migration tools."""

    def __init__(self, hass: HomeAssistant) -> None:
        super().__init__(hass)
        self.public_hidden_path = Path(hass.config.path(PUBLIC_HIDDEN_FILE))
        self.public_backup_path = Path(hass.config.path(PUBLIC_BACKUP_FILE))
        self.rules_backup_path = Path(hass.config.path(RULES_BACKUP_FILE))
        self.hidden_paths = (self.hidden_path, self.public_hidden_path)

    async def async_initialize(self) -> None:
        """Load storage, import an existing YAML copy, or create two empty copies."""
        loaded = await self.store.async_load()
        if loaded:
            self.data = self._normalize_data(loaded)
        else:
            existing_paths = await self.hass.async_add_executor_job(
                lambda: [path for path in self.hidden_paths if path.exists()]
            )
            if existing_paths:
                source = self.hidden_path if self.hidden_path in existing_paths else existing_paths[0]
                imported = await self.hass.async_add_executor_job(self._read_hidden_path, source)
                self.data = self._default_data(import_mode=True)
                self.data["entities"] = {entity_id: RULE_EXCLUDE for entity_id in imported}
                self.data["migration"]["imported_existing_file"] = True
                await self.hass.async_add_executor_job(self._backup_existing_files)
            else:
                # Fresh setup: all domains enabled, no automatic exclusions, valid [] YAML.
                self.data = self._default_data(import_mode=True)

            self._ensure_domains()
            await self.store.async_save(self.data)

        self._ensure_domains()
        await self.async_regenerate_hidden_file(save_store=True)

    @staticmethod
    def _read_hidden_path(path: Path) -> list[str]:
        if not path.exists():
            return []
        try:
            parsed = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as err:
            raise ValueError(f"Unable to import {path}: {err}") from err
        if parsed is None:
            return []
        if not isinstance(parsed, list):
            raise ValueError(f"Existing {path} is not a YAML list; refusing to overwrite it")
        return sorted(
            {
                str(item).strip()
                for item in parsed
                if isinstance(item, str) and "." in item
            }
        )

    def _backup_existing_files(self) -> None:
        for source, backup in (
            (self.hidden_path, self.backup_path),
            (self.public_hidden_path, self.public_backup_path),
        ):
            if not source.exists() or backup.exists():
                continue
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, backup)

    def _write_hidden_file_atomic(self, content: str) -> None:
        """Keep /config and /config/www hidden files byte-identical."""
        for path in self.hidden_paths:
            path.parent.mkdir(parents=True, exist_ok=True)
            temp_path = path.with_suffix(path.suffix + ".tmp")
            temp_path.write_text(content, encoding="utf-8")
            temp_path.replace(path)

    def _generate_hidden_file_text(self) -> str:
        content = super()._generate_hidden_file_text()
        marker = "# Excluded entities: 0\n\n"
        if marker in content and content.rstrip().endswith("# Excluded entities: 0"):
            return content + "[]\n"
        return content

    async def async_get_snapshot(self, *, include_file: bool = False) -> dict[str, Any]:
        payload = await super().async_get_snapshot(include_file=include_file)
        payload["file"].update(
            {
                "public_path": str(self.public_hidden_path),
                "paths": [str(path) for path in self.hidden_paths],
                "public_backup_path": str(self.public_backup_path),
                "rules_backup_path": str(self.rules_backup_path),
                "exists": all(path.exists() for path in self.hidden_paths),
            }
        )
        return payload

    def export_legacy_rules(self) -> dict[str, Any]:
        """Return the alexa_rules.json structure used by the legacy PHP manager."""
        return {
            "domains": {
                domain: {"enabled": bool(enabled)}
                for domain, enabled in sorted(self.data.get("domains", {}).items())
            },
            "entities": {
                entity_id: {"enabled": mode == RULE_ALLOW}
                for entity_id, mode in sorted(self.data.get("entities", {}).items())
                if mode in {RULE_ALLOW, RULE_EXCLUDE}
            },
            "defaults": {
                "exclude_entity_category": list(
                    self.data.get("defaults", {}).get("exclude_entity_category", [])
                ),
                "exclude_name_keywords": list(
                    self.data.get("defaults", {}).get("exclude_name_keywords", [])
                ),
            },
        }

    def _write_rules_backup(self) -> None:
        self.rules_backup_path.parent.mkdir(parents=True, exist_ok=True)
        self.rules_backup_path.write_text(
            json.dumps(self.export_legacy_rules(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    async def async_import_legacy_rules(self, rules: dict[str, Any]) -> dict[str, int]:
        """Replace current rules from an alexa_rules.json-compatible object."""
        if not isinstance(rules, dict):
            raise ValueError("Rules payload must be a JSON object")
        if not any(key in rules for key in ("domains", "entities", "defaults")):
            raise ValueError("Invalid alexa_rules.json: domains/entities/defaults are missing")

        await self.hass.async_add_executor_job(self._write_rules_backup)
        normalized = self._normalize_data(rules)
        normalized["migration"]["domain_default_enabled"] = True
        self.data = normalized
        self._ensure_domains()
        await self.async_regenerate_hidden_file(save_store=True)

        allow_count = sum(1 for mode in self.data["entities"].values() if mode == RULE_ALLOW)
        exclude_count = sum(1 for mode in self.data["entities"].values() if mode == RULE_EXCLUDE)
        return {
            "domains": len(self.data["domains"]),
            "entities": len(self.data["entities"]),
            "force_allow": allow_count,
            "force_exclude": exclude_count,
        }
