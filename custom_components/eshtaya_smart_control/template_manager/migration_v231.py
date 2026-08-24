"""v2.3.1 hardening for legacy Template Manager migration."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .const import LEGACY_DOMAIN, LEGACY_SENSOR
from .migration import LegacyTemplateMigration as _BaseLegacyTemplateMigration


class LegacyTemplateMigration(_BaseLegacyTemplateMigration):
    """Harden migration across YAML runtimes and restart-staged cutovers."""

    def _legacy_paths(self) -> list[Path]:
        """Return only legacy paths that are safe to remove automatically.

        The base migrator intentionally recognizes several broad historical naming
        patterns for discovery. v2.3.1 narrows destructive cleanup to exact generated
        files and paths explicitly owned by the old integration domain so an unrelated
        user package with a similar name is never deleted automatically.
        """
        config = self.config_root
        safe: list[Path] = [
            config / "custom_components" / LEGACY_DOMAIN,
            config / LEGACY_DOMAIN,
            config / "www" / "eshtaya-template-manager.js",
            config / "www" / "eshtaya-template-manager-card.js",
            *self._generated_paths(),
        ]
        safe.extend(config.glob(f".storage/{LEGACY_DOMAIN}*"))
        safe.extend(config.glob(f"packages/{LEGACY_DOMAIN}*.yaml"))
        return list(dict.fromkeys(path for path in safe if path.exists()))

    async def _backup(
        self,
        records: list[dict[str, Any]],
        registry_data: dict[str, dict[str, Any]],
    ) -> Path:
        """Include the pre-migration unified store in the persistent rollback backup."""
        root = await super()._backup(records, registry_data)
        backup_file = root / "migration.json"
        previous_records = self._previous_records

        def _patch_backup() -> None:
            payload = json.loads(backup_file.read_text(encoding="utf-8"))
            payload["previous_unified_records"] = previous_records
            backup_file.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8",
            )

        await self.hass.async_add_executor_job(_patch_backup)
        return root

    async def _hydrate_resume_state(self, prior: dict[str, Any]) -> None:
        """Restore in-memory rollback/registry context after a Home Assistant restart."""
        backup_path = str(prior.get("backup_path") or "").strip()
        if backup_path:
            self._backup_dir = Path(backup_path)
            backup_file = self._backup_dir / "migration.json"

            def _read_backup() -> dict[str, Any]:
                if not backup_file.is_file():
                    return {}
                try:
                    value = json.loads(backup_file.read_text(encoding="utf-8"))
                    return value if isinstance(value, dict) else {}
                except (OSError, json.JSONDecodeError):
                    return {}

            payload = await self.hass.async_add_executor_job(_read_backup)
            self._registry_backup = dict(payload.get("registry") or {})
            sensor_backup = payload.get("sensor_registry")
            self._sensor_registry_backup = (
                dict(sensor_backup) if isinstance(sensor_backup, dict) else None
            )
            previous = payload.get("previous_unified_records")
            self._previous_records = list(previous) if isinstance(previous, list) else []

        entry_ids = {str(value) for value in prior.get("legacy_entry_ids") or []}
        self._legacy_entries = [
            entry
            for entry in self.hass.config_entries.async_entries()
            if entry.entry_id in entry_ids
        ]
        self._records = self.store.templates()

    async def _resume_staged_migration(self, prior: dict[str, Any]) -> dict[str, Any]:
        """Resume exact-ID takeover with the original backup context restored."""
        await self._hydrate_resume_state(prior)
        return await super()._resume_staged_migration(prior)

    def _occupied_legacy_entities(self, records: list[dict[str, Any]]) -> list[str]:
        """Treat a live old compatibility sensor as occupied, not a stale registry row."""
        occupied = super()._occupied_legacy_entities(records)
        if (
            self.hass.states.get(LEGACY_SENSOR) is not None
            and self._legacy_sensor_is_external()
            and LEGACY_SENSOR not in occupied
        ):
            occupied.append(LEGACY_SENSOR)
        return occupied
