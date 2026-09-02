"""v2.4.3 full-editor behavior mixed into the active Template Manager."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import SIGNAL_TEMPLATE_CHANGED

_SUPPORTED_TYPES = {"light", "fan"}


class FullTemplateEditorMixin:
    """Add complete Managed-item editing without replacing legacy APIs."""

    async def async_editor_get(self, managed_entity: str) -> dict[str, Any]:
        record = self.store.get(managed_entity)
        if not record:
            raise ValueError(f"Managed entity not found: {managed_entity}")

        result: dict[str, Any] = {
            "managed_entity": managed_entity,
            "template_type": str(record.get("type") or managed_entity.split(".", 1)[0]),
            "name": str(record.get("name") or managed_entity),
            "entity_id": str(record.get("entity_id") or managed_entity),
            "source_entity": str(record.get("source_entity") or ""),
            "external_managed": bool(record.get("external_managed")),
            "advanced_available": bool(record.get("external_managed")),
            "definition_yaml": "",
            "unique_id": str(record.get("unique_id") or ""),
        }
        if record.get("external_managed"):
            package = await self.generated_packages.async_get_definition(record)
            result.update(package)
            raw_path = str(package.get("generated_path") or "")
            result["generated_file"] = raw_path.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
            result.pop("generated_path", None)
        return result

    @staticmethod
    def _editor_validate_basic(
        *, template_type: str, entity_id: str, source_entity: str
    ) -> tuple[str, str, str]:
        template_type = template_type.strip().lower()
        entity_id = entity_id.strip()
        source_entity = source_entity.strip()
        if template_type not in _SUPPORTED_TYPES:
            raise ValueError(f"Unsupported template type: {template_type}")
        if not entity_id.startswith(f"{template_type}."):
            raise ValueError(f"Entity ID must start with {template_type}.")
        if not source_entity.startswith("switch."):
            raise ValueError("Source entity must be a switch.* entity")
        return template_type, entity_id, source_entity

    def _editor_validate_target_free(self, old_entity: str, new_entity: str) -> None:
        if new_entity == old_entity:
            return
        registry = er.async_get(self.hass)
        if self.store.get(new_entity) or registry.async_get(new_entity) or self.hass.states.get(new_entity):
            raise ValueError(f"Entity ID is already in use: {new_entity}")

    def _editor_validate_external_unique_id(
        self, *, old_entity: str, template_type: str, unique_id: str
    ) -> None:
        unique_id = unique_id.strip()
        if not unique_id:
            return
        registry = er.async_get(self.hass)
        existing_entity = registry.async_get_entity_id(template_type, "template", unique_id)
        if existing_entity and existing_entity != old_entity:
            raise ValueError(f"Unique ID is already in use by {existing_entity}: {unique_id}")

    async def _editor_save_native(
        self,
        record: dict[str, Any],
        *,
        template_type: str,
        name: str,
        entity_id: str,
        source_entity: str,
    ) -> dict[str, Any]:
        old_entity = str(record["entity_id"])
        old_type = str(record.get("type") or old_entity.split(".", 1)[0])
        registry = er.async_get(self.hass)
        entry = registry.async_get(old_entity)

        if template_type != old_type and entry:
            registry.async_remove(old_entity)
        elif entry:
            changes: dict[str, Any] = {}
            if entity_id != old_entity:
                changes["new_entity_id"] = entity_id
            if name.strip():
                changes["name"] = name.strip()
            if changes:
                registry.async_update_entity(old_entity, **changes)

        updated = deepcopy(record)
        updated["old_entity_id"] = old_entity
        updated["entity_id"] = entity_id
        updated["type"] = template_type
        updated["name"] = name.strip() or entity_id
        updated["source_entity"] = source_entity
        updated["unique_id"] = str(updated.get("unique_id") or f"esc_template::{old_entity}")
        await self.store.async_upsert(updated)
        async_dispatcher_send(self.hass, SIGNAL_TEMPLATE_CHANGED)
        await self.async_scan()
        saved = self.store.get(entity_id)
        if not saved:
            raise ValueError(f"Managed template could not be saved: {entity_id}")
        return saved

    async def _editor_save_external(
        self,
        record: dict[str, Any],
        *,
        template_type: str,
        name: str,
        entity_id: str,
        source_entity: str,
        unique_id: str,
        definition_yaml: str,
    ) -> dict[str, Any]:
        old_entity = str(record["entity_id"])
        old_type = str(record.get("type") or old_entity.split(".", 1)[0])
        old_unique_id = str(record.get("unique_id") or "")
        self._editor_validate_external_unique_id(
            old_entity=old_entity,
            template_type=template_type,
            unique_id=unique_id,
        )
        transaction = await self.generated_packages.async_save_definition(
            record,
            template_type=template_type,
            name=name,
            entity_id=entity_id,
            source_entity=source_entity,
            unique_id=unique_id,
            definition_yaml=definition_yaml,
        )
        new_unique_id = str(transaction.get("unique_id") or "")
        identity_changed = template_type != old_type or new_unique_id != old_unique_id

        registry = er.async_get(self.hass)
        old_entry = registry.async_get(old_entity)
        if identity_changed and old_entry:
            registry.async_remove(old_entity)

        try:
            await self.generated_packages.async_reload_templates()
        except Exception as err:  # noqa: BLE001
            await self.generated_packages.async_restore(transaction)
            try:
                await self.generated_packages.async_reload_templates()
            except Exception:  # noqa: BLE001
                pass
            raise ValueError(f"Template reload failed; the YAML file was rolled back: {err}") from err

        if not identity_changed and old_entry:
            changes: dict[str, Any] = {}
            if entity_id != old_entity:
                changes["new_entity_id"] = entity_id
            if name.strip():
                changes["name"] = name.strip()
            if changes:
                registry.async_update_entity(old_entity, **changes)

        await self._async_sync_generated_packages()
        await self.async_scan()
        saved = self.store.get(entity_id)
        if not saved:
            raise ValueError(f"Generated template could not be reloaded: {entity_id}")
        return saved

    async def async_editor_save(
        self,
        *,
        managed_entity: str,
        template_type: str,
        name: str,
        entity_id: str,
        source_entity: str,
        unique_id: str = "",
        definition_yaml: str = "",
    ) -> dict[str, Any]:
        self._ensure_mutation_allowed()
        record = self.store.get(managed_entity)
        if not record:
            raise ValueError(f"Managed entity not found: {managed_entity}")

        template_type, entity_id, source_entity = self._editor_validate_basic(
            template_type=template_type,
            entity_id=entity_id,
            source_entity=source_entity,
        )
        if self.hass.states.get(source_entity) is None:
            raise ValueError(f"Source entity not found: {source_entity}")
        self._editor_validate_target_free(managed_entity, entity_id)

        if record.get("external_managed"):
            if not definition_yaml.strip():
                raise ValueError("Advanced YAML definition is required for generated-package templates")
            saved = await self._editor_save_external(
                record,
                template_type=template_type,
                name=name,
                entity_id=entity_id,
                source_entity=source_entity,
                unique_id=unique_id,
                definition_yaml=definition_yaml,
            )
        else:
            saved = await self._editor_save_native(
                record,
                template_type=template_type,
                name=name,
                entity_id=entity_id,
                source_entity=source_entity,
            )

        editor = await self.async_editor_get(entity_id)
        return {"record": saved, "editor": editor}
