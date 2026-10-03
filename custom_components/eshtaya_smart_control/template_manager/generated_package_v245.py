"""v2.4.5 YAML source-of-truth support for Template Manager."""
from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .generated_package_v244 import GeneratedPackageManager as _V244GeneratedPackageManager

_CREATE_PRIORITY = (
    "packages/eshtaya_generated_lights.yaml",
    "packages/eshtaya_generated_templates.yaml",
    "eshtaya_template_manager/generated_templates.yaml",
)


class GeneratedPackageManager(_V244GeneratedPackageManager):
    """Create new Template Manager records in the managed YAML package."""

    def _create_target_path(self) -> Path:
        for relative in _CREATE_PRIORITY:
            candidate = self.config_root / relative
            if candidate.is_file():
                return candidate
        return self.config_root / _CREATE_PRIORITY[0]

    @staticmethod
    def _template_node(record: dict[str, Any]) -> dict[str, Any]:
        entity_id = str(record["entity_id"]).strip()
        source = str(record["source_entity"]).strip()
        template_type = str(record["type"]).strip().lower()
        name = str(record.get("name") or entity_id).strip()
        unique_id = str(record.get("unique_id") or f"esc_template::{entity_id}").strip()

        if template_type not in {"light", "fan"}:
            raise ValueError(f"Unsupported template type: {template_type}")
        if not entity_id.startswith(f"{template_type}."):
            raise ValueError(f"Entity ID must start with {template_type}.")
        if not source.startswith("switch."):
            raise ValueError("Source entity must be a switch.* entity")

        return {
            "name": name or entity_id,
            "unique_id": unique_id,
            "default_entity_id": entity_id,
            "state": f"{{{{ is_state('{source}', 'on') }}}}",
            "availability": f"{{{{ not is_state('{source}', 'unavailable') }}}}",
            "turn_on": {
                "action": "switch.turn_on",
                "target": {"entity_id": source},
            },
            "turn_off": {
                "action": "switch.turn_off",
                "target": {"entity_id": source},
            },
        }

    @classmethod
    def _append_node(
        cls,
        root: Any,
        *,
        template_type: str,
        node: dict[str, Any],
    ) -> dict[str, Any]:
        if root is None:
            root = {}
        if not isinstance(root, dict):
            raise ValueError("Generated package root must be a YAML mapping")

        templates = root.get("template")
        if templates is None:
            templates = []
            root["template"] = templates
        if not isinstance(templates, list):
            raise ValueError("The generated package 'template' key must contain a list")

        # Prefer the existing domain container so newly created records keep the
        # same layout as the user's current generated package.
        for block in templates:
            if not isinstance(block, dict) or template_type not in block:
                continue
            entries = block[template_type]
            if isinstance(entries, list):
                entries.append(node)
                return root
            if isinstance(entries, dict):
                block[template_type] = [entries, node]
                return root
            raise ValueError(f"Unsupported {template_type} container in generated package")

        templates.append({template_type: [node]})
        return root

    def _backup_existing(self, path: Path) -> None:
        relative = path.relative_to(self.config_root)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = (
            self.config_root
            / "eshtaya_smart_control_backups"
            / "generated_packages"
            / stamp
            / relative
        )
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup)

    def _create_records_sync(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        path = self._create_target_path()
        existed = path.is_file()
        previous_text = path.read_text(encoding="utf-8") if existed else ""
        value = yaml.safe_load(previous_text) if previous_text.strip() else {}

        created: list[str] = []
        for record in records:
            entity_id = str(record["entity_id"]).strip()
            existing = self._find_typed_location(value, entity_id)
            if existing is not None:
                # Idempotent startup conversion: if the YAML already has the ID,
                # leave it untouched and let the scanner adopt it.
                continue
            template_type = str(record["type"]).strip().lower()
            value = self._append_node(
                value,
                template_type=template_type,
                node=self._template_node(record),
            )
            created.append(entity_id)

        if not created:
            return {
                "path": str(path),
                "previous_text": previous_text,
                "previous_exists": existed,
                "created": [],
            }

        path.parent.mkdir(parents=True, exist_ok=True)
        if existed:
            self._backup_existing(path)
        temp = path.with_suffix(path.suffix + ".esc-create-tmp")
        temp.write_text(
            yaml.safe_dump(value, allow_unicode=True, sort_keys=False, default_flow_style=False),
            encoding="utf-8",
        )
        temp.replace(path)
        return {
            "path": str(path),
            "previous_text": previous_text,
            "previous_exists": existed,
            "created": created,
        }

    async def async_create_records(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        return await self.hass.async_add_executor_job(self._create_records_sync, records)

    def _restore_create_sync(self, transaction: dict[str, Any]) -> None:
        path = Path(str(transaction["path"])).resolve()
        root = self.config_root.resolve()
        path.relative_to(root)
        if transaction.get("previous_exists"):
            temp = path.with_suffix(path.suffix + ".esc-create-rollback")
            temp.write_text(str(transaction.get("previous_text") or ""), encoding="utf-8")
            temp.replace(path)
        elif path.exists():
            path.unlink()

    async def async_restore_create(self, transaction: dict[str, Any]) -> None:
        await self.hass.async_add_executor_job(self._restore_create_sync, transaction)
