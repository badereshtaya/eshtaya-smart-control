"""v2.4.2+ Template Manager behavior for generated package adoption."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from homeassistant.helpers import entity_registry as er

from .editor_v243 import FullTemplateEditorMixin
from .generated_package_v244 import GeneratedPackageManager
from .manager import TemplateManager as _BaseTemplateManager

_ACTIVE_LOCK_PHASES = {"prepared", "restart_required"}


class TemplateManager(FullTemplateEditorMixin, _BaseTemplateManager):
    """Treat Eshtaya generated YAML templates as editable managed records."""

    def __init__(self, hass, store) -> None:
        super().__init__(hass, store)
        self.generated_packages = GeneratedPackageManager(hass)
        self._generated_count = 0

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

    async def _async_sync_generated_packages(self) -> None:
        """Mirror known generated package records into the unified store.

        The YAML file remains the runtime owner. ``deferred`` prevents the native
        Eshtaya light/fan platforms from creating a duplicate entity with the same ID.

        A parser/read failure must never erase the last known external mirror. The
        scan diagnostics remain visible in the snapshot so the user can fix the file
        while the previous managed rows stay available for recovery.
        """
        if self._migration_locked():
            return
        generated = await self.generated_packages.async_scan()
        diagnostics = self.generated_packages.scan_diagnostics
        scan_has_errors = bool(diagnostics.get("errors"))
        current = self.store.templates()
        current_by_id = {str(item.get("entity_id")): item for item in current}
        generated_by_id = {str(item["entity_id"]): item for item in generated}

        result: list[dict[str, Any]] = []
        for record in current:
            entity_id = str(record.get("entity_id") or "")
            if record.get("external_managed"):
                if entity_id in generated_by_id:
                    # Fresh file data wins for external records.
                    continue
                if scan_has_errors:
                    # Do not destructively purge a previously known mapping because a
                    # generated YAML file is temporarily unreadable or malformed.
                    result.append({**record, "deferred": True, "scan_stale": True})
                    continue
                # No scan errors and the definition is genuinely gone from the
                # managed package files, so remove only the stale mirror record.
                continue
            result.append(record)

        for entity_id, record in generated_by_id.items():
            existing = current_by_id.get(entity_id)
            if existing and not existing.get("external_managed"):
                # Never replace a native Eshtaya-managed entity with a file mirror.
                continue
            clean = {**record, "deferred": True}
            clean.pop("scan_stale", None)
            result.append(clean)

        before = {str(item.get("entity_id")): item for item in current}
        after = {str(item.get("entity_id")): item for item in result}
        if before != after:
            await self.store.async_replace_all(result)
        self._generated_count = sum(1 for item in result if item.get("external_managed"))

    async def async_start(self) -> None:
        await self._async_sync_generated_packages()
        await super().async_start()

    async def async_scan(self) -> dict[str, Any]:
        await self._async_sync_generated_packages()
        snapshot = await super().async_scan()
        snapshot["mutation_locked"] = self._migration_locked()
        snapshot["generated_managed_count"] = self._generated_count
        snapshot["generated_scan"] = self.generated_packages.scan_diagnostics
        snapshot["defined_count"] = len(self.store.templates())
        migration = deepcopy(snapshot.get("migration") or {})
        if not self._migration_locked() and migration.get("legacy_found") and not migration.get("completed"):
            # A rolled-back/failed/stale migration must never leave the normal manager
            # permanently read-only. Preserve the real state in storage, but present it
            # as non-locking to the UI.
            migration["legacy_found"] = False
            migration["stale_state"] = True
        snapshot["migration"] = migration
        self._last_snapshot = deepcopy(snapshot)
        return snapshot

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
