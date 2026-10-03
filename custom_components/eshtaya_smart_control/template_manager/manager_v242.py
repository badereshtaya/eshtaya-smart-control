"""v2.4.5 Template Manager with generated YAML as the source of truth."""
from __future__ import annotations

import asyncio
from copy import deepcopy
from typing import Any

from homeassistant.helpers import entity_registry as er

from .editor_v243 import FullTemplateEditorMixin
from .generated_package_v245 import GeneratedPackageManager
from .manager import TemplateManager as _BaseTemplateManager

_ACTIVE_LOCK_PHASES = {"prepared", "restart_required"}
_SUPPORTED_TYPES = {"light", "fan"}


class TemplateManager(FullTemplateEditorMixin, _BaseTemplateManager):
    """Treat generated YAML templates as editable managed records."""

    def __init__(self, hass, store) -> None:
        super().__init__(hass, store)
        self.generated_packages = GeneratedPackageManager(hass)
        self._generated_count = 0
        self._yaml_conversion: dict[str, Any] = {
            "attempted": 0,
            "converted": 0,
            "error": None,
        }

    def _migration_locked(self) -> bool:
        migration = self.store.migration()
        return bool(
            migration.get("legacy_found")
            and not migration.get("completed")
            and str(migration.get("phase") or "") in _ACTIVE_LOCK_PHASES
        )

    def _ensure_mutation_allowed(self) -> None:
        if not self._migration_locked():
            return
        migration = self.store.migration()
        phase = str(migration.get("phase") or "migration")
        raise ValueError(
            f"Template Manager changes are locked while legacy migration is {phase}. "
            "Complete the migration/restart first."
        )

    @staticmethod
    def _registry_metadata(entry) -> dict[str, Any]:
        return {
            "name": entry.name,
            "icon": entry.icon,
            "area_id": entry.area_id,
            "labels": set(entry.labels),
        }

    @staticmethod
    def _restore_registry_metadata(registry, entity_id: str, metadata: dict[str, Any]) -> None:
        entry = registry.async_get(entity_id)
        if entry is None:
            return
        changes: dict[str, Any] = {}
        for key in ("name", "icon", "area_id"):
            if metadata.get(key) is not None:
                changes[key] = metadata[key]
        if metadata.get("labels"):
            changes["labels"] = set(metadata["labels"])
        if changes:
            registry.async_update_entity(entity_id, **changes)

    async def _async_wait_template_owner(
        self, entity_ids: list[str], timeout: float = 3.0
    ) -> bool:
        """Wait briefly for template.reload to claim all requested exact IDs."""
        registry = er.async_get(self.hass)
        deadline = self.hass.loop.time() + timeout
        wanted = set(entity_ids)
        while self.hass.loop.time() < deadline:
            ready = True
            for entity_id in wanted:
                entry = registry.async_get(entity_id)
                if entry is None or entry.platform != "template":
                    ready = False
                    break
            if ready:
                return True
            await asyncio.sleep(0.1)
        return False

    async def _async_sync_generated_packages(self) -> None:
        """Mirror generated package records into the unified store.

        Generated YAML is authoritative. The deferred flag prevents the Eshtaya
        native light/fan platforms from creating a second runtime owner.

        A parser/read failure never erases the last known external mirror.
        """
        if self._migration_locked():
            return
        generated = await self.generated_packages.async_scan()
        diagnostics = self.generated_packages.scan_diagnostics
        scan_has_errors = bool(diagnostics.get("errors"))
        current = self.store.templates()
        generated_by_id = {str(item["entity_id"]): item for item in generated}

        result: list[dict[str, Any]] = []
        for record in current:
            entity_id = str(record.get("entity_id") or "")
            if entity_id in generated_by_id:
                # YAML wins over a previous YAML mirror or an older native row.
                continue
            if record.get("external_managed"):
                if scan_has_errors:
                    result.append({**record, "deferred": True, "scan_stale": True})
                    continue
                continue
            result.append(record)

        for record in generated_by_id.values():
            clean = {**record, "deferred": True}
            clean.pop("scan_stale", None)
            result.append(clean)

        before = {str(item.get("entity_id")): item for item in current}
        after = {str(item.get("entity_id")): item for item in result}
        if before != after:
            await self.store.async_replace_all(result)
        self._generated_count = sum(1 for item in result if item.get("external_managed"))

    async def _async_materialize_native_records(self) -> None:
        """Convert old Eshtaya-native mappings into the generated YAML.

        This runs before the Eshtaya light/fan platforms are forwarded during
        integration setup, so exact entity IDs can move to the Home Assistant
        template integration without creating suffix duplicates.
        """
        if self._migration_locked():
            return

        current = self.store.templates()
        native = [
            record
            for record in current
            if not record.get("external_managed")
            and not record.get("deferred")
            and str(record.get("type") or "") in _SUPPORTED_TYPES
            and str(record.get("source_entity") or "").startswith("switch.")
        ]
        self._yaml_conversion = {
            "attempted": len(native),
            "converted": 0,
            "error": None,
        }
        if not native:
            return

        if not self.hass.services.has_service("template", "reload"):
            self._yaml_conversion["error"] = (
                "template.reload is unavailable; native records were left untouched"
            )
            return

        await self.generated_packages.async_scan()
        diagnostics = self.generated_packages.scan_diagnostics
        if diagnostics.get("errors"):
            self._yaml_conversion["error"] = (
                "generated YAML scan has errors; native records were left untouched"
            )
            return

        existing = {
            str(item["entity_id"])
            for item in await self.generated_packages.async_scan()
        }
        pending = [record for record in native if str(record["entity_id"]) not in existing]
        if not pending:
            await self._async_sync_generated_packages()
            self._yaml_conversion["converted"] = len(native)
            return

        registry = er.async_get(self.hass)
        metadata: dict[str, dict[str, Any]] = {}
        removable_ids: list[str] = []
        for record in pending:
            entity_id = str(record["entity_id"])
            entry = registry.async_get(entity_id)
            if entry is None:
                continue
            if entry.platform != "eshtaya_smart_control":
                self._yaml_conversion["error"] = (
                    f"{entity_id} is owned by {entry.platform}; automatic YAML conversion skipped"
                )
                return
            metadata[entity_id] = self._registry_metadata(entry)
            removable_ids.append(entity_id)

        transaction = await self.generated_packages.async_create_records(pending)
        try:
            for entity_id in removable_ids:
                if registry.async_get(entity_id):
                    registry.async_remove(entity_id)

            await self.generated_packages.async_reload_templates()
            pending_ids = [str(record["entity_id"]) for record in pending]
            if not await self._async_wait_template_owner(pending_ids):
                raise ValueError(
                    "Home Assistant template integration did not claim the exact generated entity IDs"
                )

            for entity_id, saved in metadata.items():
                self._restore_registry_metadata(registry, entity_id, saved)

            await self._async_sync_generated_packages()
            self._yaml_conversion["converted"] = len(pending)
        except Exception as err:  # noqa: BLE001
            await self.generated_packages.async_restore_create(transaction)
            try:
                await self.generated_packages.async_reload_templates()
            except Exception:  # noqa: BLE001
                pass
            self._yaml_conversion["error"] = str(err)
            # Store records remain native; normal platform setup can recreate them.

    async def async_start(self) -> None:
        await self._async_materialize_native_records()
        await self._async_sync_generated_packages()
        await super().async_start()

    async def async_scan(self) -> dict[str, Any]:
        await self._async_sync_generated_packages()
        snapshot = await super().async_scan()
        snapshot["mutation_locked"] = self._migration_locked()
        snapshot["generated_managed_count"] = self._generated_count
        snapshot["generated_scan"] = self.generated_packages.scan_diagnostics
        snapshot["defined_count"] = len(self.store.templates())
        snapshot["yaml_source_of_truth"] = deepcopy(self._yaml_conversion)
        migration = deepcopy(snapshot.get("migration") or {})
        if (
            not self._migration_locked()
            and migration.get("legacy_found")
            and not migration.get("completed")
        ):
            migration["legacy_found"] = False
            migration["stale_state"] = True
        snapshot["migration"] = migration
        self._last_snapshot = deepcopy(snapshot)
        return snapshot

    async def async_create(
        self, *, source_entity: str, template_type: str, name: str, entity_id: str
    ) -> dict[str, Any]:
        """Create a YAML-backed managed entity transactionally."""
        self._ensure_mutation_allowed()
        template_type = template_type.lower().strip()
        entity_id = entity_id.strip()
        source_entity = source_entity.strip()
        if template_type not in _SUPPORTED_TYPES:
            raise ValueError(f"Unsupported template type: {template_type}")
        if not entity_id.startswith(f"{template_type}."):
            raise ValueError(f"Entity ID must start with {template_type}.")
        if self.hass.states.get(source_entity) is None:
            raise ValueError(f"Source entity not found: {source_entity}")
        if not self.hass.services.has_service("template", "reload"):
            raise ValueError(
                "Home Assistant template.reload is unavailable; refusing to create "
                "a record that cannot be persisted safely to generated YAML"
            )

        registry = er.async_get(self.hass)
        if self.store.get(entity_id) or registry.async_get(entity_id) or self.hass.states.get(entity_id):
            raise ValueError(f"Entity ID is already in use: {entity_id}")

        record = {
            "entity_id": entity_id,
            "source_entity": source_entity,
            "type": template_type,
            "name": name.strip() or entity_id,
            "unique_id": f"esc_template::{entity_id}",
        }
        transaction = await self.generated_packages.async_create_records([record])
        try:
            await self.generated_packages.async_reload_templates()
            if not await self._async_wait_template_owner([entity_id]):
                raise ValueError(
                    f"Generated template was written but Home Assistant did not claim {entity_id}"
                )
            await self._async_sync_generated_packages()
            await self.async_scan()
            saved = self.store.get(entity_id)
            if not saved or not saved.get("external_managed"):
                raise ValueError(
                    f"Generated template could not be adopted as YAML managed: {entity_id}"
                )
            return saved
        except Exception as err:  # noqa: BLE001
            await self.generated_packages.async_restore_create(transaction)
            try:
                await self.generated_packages.async_reload_templates()
            except Exception:  # noqa: BLE001
                pass
            await self._async_sync_generated_packages()
            raise ValueError(f"Template creation failed and YAML was rolled back: {err}") from err

    async def async_edit(
        self, *, managed_entity: str, name: str, entity_id: str
    ) -> dict[str, Any]:
        self._ensure_mutation_allowed()
        record = self.store.get(managed_entity)
        if not record or not record.get("external_managed"):
            return await super().async_edit(
                managed_entity=managed_entity, name=name, entity_id=entity_id
            )

        entity_id = entity_id.strip()
        if not entity_id.startswith(f"{record['type']}."):
            raise ValueError(f"Entity ID must remain in the {record['type']} domain")
        registry = er.async_get(self.hass)
        if entity_id != managed_entity:
            occupied = registry.async_get(entity_id) or self.hass.states.get(entity_id)
            if occupied:
                raise ValueError(f"Entity ID is already in use: {entity_id}")

        await self.generated_packages.async_edit(record, name=name, entity_id=entity_id)
        await self.generated_packages.async_reload_templates()

        entry = registry.async_get(managed_entity)
        if entry:
            changes: dict[str, Any] = {}
            if entity_id != managed_entity:
                changes["new_entity_id"] = entity_id
            if name.strip():
                changes["name"] = name.strip()
            if changes:
                registry.async_update_entity(managed_entity, **changes)

        await self._async_sync_generated_packages()
        await self.async_scan()
        updated = self.store.get(entity_id)
        if not updated:
            raise ValueError(f"Generated template could not be reloaded: {entity_id}")
        return updated

    async def async_relink(
        self, *, managed_entity: str, source_entity: str
    ) -> dict[str, Any]:
        self._ensure_mutation_allowed()
        record = self.store.get(managed_entity)
        if not record or not record.get("external_managed"):
            return await super().async_relink(
                managed_entity=managed_entity, source_entity=source_entity
            )
        source_entity = source_entity.strip()
        if self.hass.states.get(source_entity) is None:
            raise ValueError(f"Source entity not found: {source_entity}")
        await self.generated_packages.async_relink(record, source_entity=source_entity)
        await self.generated_packages.async_reload_templates()
        await self._async_sync_generated_packages()
        await self.async_scan()
        updated = self.store.get(managed_entity)
        if not updated:
            raise ValueError(f"Generated template could not be reloaded: {managed_entity}")
        return updated

    async def async_delete(self, managed_entity: str) -> None:
        self._ensure_mutation_allowed()
        record = self.store.get(managed_entity)
        if not record or not record.get("external_managed"):
            await super().async_delete(managed_entity)
            return
        await self.generated_packages.async_delete(record)
        await self.generated_packages.async_reload_templates()
        registry = er.async_get(self.hass)
        entry = registry.async_get(managed_entity)
        if entry and entry.platform == "template":
            registry.async_remove(managed_entity)
        await self._async_sync_generated_packages()
        await self.async_scan()
