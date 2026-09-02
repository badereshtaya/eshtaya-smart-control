"""v2.4.3 full editor support for generated Home Assistant template packages."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

import yaml

from .generated_package import GeneratedPackageManager as _BaseGeneratedPackageManager

_SUPPORTED_TYPES = {"light", "fan"}


class GeneratedPackageManager(_BaseGeneratedPackageManager):
    """Read and transactionally update complete generated template definitions."""

    @classmethod
    def _find_typed_location(cls, value: Any, entity_id: str):
        """Return (domain_container, domain, entries, index, node) for a template node."""
        if isinstance(value, dict):
            for domain in _SUPPORTED_TYPES:
                entries = value.get(domain)
                if isinstance(entries, list):
                    for index, node in enumerate(entries):
                        if isinstance(node, dict) and cls._node_entity_id(node) == entity_id:
                            return value, domain, entries, index, node
                elif isinstance(entries, dict) and cls._node_entity_id(entries) == entity_id:
                    return value, domain, entries, None, entries
            if cls._node_entity_id(value) == entity_id:
                return None, entity_id.split(".", 1)[0], None, None, value
            for child in value.values():
                found = cls._find_typed_location(child, entity_id)
                if found is not None:
                    return found
        elif isinstance(value, list):
            for child in value:
                found = cls._find_typed_location(child, entity_id)
                if found is not None:
                    return found
        return None

    @staticmethod
    def _dump_definition(node: dict[str, Any]) -> str:
        return yaml.safe_dump(
            node,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        ).rstrip() + "\n"

    def _get_definition_sync(self, record: dict[str, Any]) -> dict[str, Any]:
        path, value = self._load_path(str(record.get("generated_path") or ""))
        entity_id = str(record["entity_id"])
        location = self._find_typed_location(value, entity_id)
        if location is None:
            raise ValueError(f"Generated template not found in package: {entity_id}")
        _container, domain, _entries, _index, node = location
        source = self._source_from(node) or str(record.get("source_entity") or "")
        return {
            "template_type": domain,
            "name": str(node.get("name") or record.get("name") or entity_id),
            "entity_id": self._node_entity_id(node) or entity_id,
            "source_entity": source,
            "unique_id": str(node.get("unique_id") or record.get("unique_id") or ""),
            "definition_yaml": self._dump_definition(deepcopy(node)),
            "generated_path": str(path),
        }

    async def async_get_definition(self, record: dict[str, Any]) -> dict[str, Any]:
        return await self.hass.async_add_executor_job(self._get_definition_sync, record)

    @staticmethod
    def _set_entity_id(node: dict[str, Any], entity_id: str) -> None:
        if "default_entity_id" in node:
            node["default_entity_id"] = entity_id
            node.pop("entity_id", None)
        elif "entity_id" in node:
            node["entity_id"] = entity_id
        else:
            node["default_entity_id"] = entity_id

    @classmethod
    def _move_type(
        cls,
        *,
        container: dict[str, Any] | None,
        old_domain: str,
        new_domain: str,
        entries: Any,
        index: int | None,
        node: dict[str, Any],
    ) -> None:
        if old_domain == new_domain:
            return
        if container is None:
            raise ValueError("This package layout does not support changing the template type")

        if isinstance(entries, list) and index is not None:
            entries.pop(index)
        elif isinstance(entries, dict):
            container.pop(old_domain, None)
        else:
            raise ValueError("This package layout does not support changing the template type")

        target = container.get(new_domain)
        if target is None:
            container[new_domain] = [node]
        elif isinstance(target, list):
            target.append(node)
        elif isinstance(target, dict):
            container[new_domain] = [target, node]
        else:
            raise ValueError(f"Unsupported {new_domain} template container in generated package")

        old_target = container.get(old_domain)
        if isinstance(old_target, list) and not old_target:
            container.pop(old_domain, None)

    def _save_definition_sync(
        self,
        record: dict[str, Any],
        *,
        template_type: str,
        name: str,
        entity_id: str,
        source_entity: str,
        definition_yaml: str,
    ) -> dict[str, Any]:
        old_entity = str(record["entity_id"])
        old_source = str(record.get("source_entity") or "")
        template_type = template_type.strip().lower()
        entity_id = entity_id.strip()
        source_entity = source_entity.strip()

        if template_type not in _SUPPORTED_TYPES:
            raise ValueError(f"Unsupported template type: {template_type}")
        if not entity_id.startswith(f"{template_type}."):
            raise ValueError(f"Entity ID must start with {template_type}.")
        if not source_entity.startswith("switch."):
            raise ValueError("Source entity must be a switch.* entity")

        try:
            edited = yaml.safe_load(definition_yaml)
        except yaml.YAMLError as err:
            raise ValueError(f"Advanced YAML is invalid: {err}") from err
        if not isinstance(edited, dict):
            raise ValueError("Advanced YAML must contain exactly one template definition mapping")

        path, value = self._load_path(str(record.get("generated_path") or ""))
        location = self._find_typed_location(value, old_entity)
        if location is None:
            raise ValueError(f"Generated template not found in package: {old_entity}")
        container, old_domain, entries, index, _old_node = location

        duplicate = self._find_typed_location(value, entity_id)
        if entity_id != old_entity and duplicate is not None:
            raise ValueError(f"Entity ID is already defined in generated package: {entity_id}")

        definition_source = self._source_from(edited)
        if definition_source:
            edited = self._replace_source(edited, definition_source, source_entity)
        elif old_source:
            edited = self._replace_source(edited, old_source, source_entity)
        if self._source_from(edited) is None:
            raise ValueError(
                "Advanced YAML must reference the selected switch source in state/turn_on/turn_off or a service target"
            )

        self._set_entity_id(edited, entity_id)
        edited["name"] = name.strip() or entity_id

        if isinstance(entries, list) and index is not None:
            entries[index] = edited
            active_entries: Any = entries
            active_index: int | None = index
        elif isinstance(entries, dict) and container is not None:
            container[old_domain] = edited
            active_entries = edited
            active_index = None
        elif container is None:
            # The node is not below an explicit light:/fan: container. Full editing is
            # still safe, but a domain conversion cannot be represented unambiguously.
            if old_domain != template_type:
                raise ValueError("Template type cannot be changed for this package layout")
            _old_node.clear()
            _old_node.update(edited)
            active_entries = None
            active_index = None
        else:
            raise ValueError("Unsupported generated package structure")

        self._move_type(
            container=container,
            old_domain=old_domain,
            new_domain=template_type,
            entries=active_entries,
            index=active_index,
            node=edited,
        )

        previous_text = path.read_text(encoding="utf-8")
        self._backup_and_write(path, value)
        return {
            "path": str(path),
            "previous_text": previous_text,
            "old_entity_id": old_entity,
            "entity_id": entity_id,
            "old_type": old_domain,
            "template_type": template_type,
            "unique_id": str(edited.get("unique_id") or record.get("unique_id") or ""),
        }

    async def async_save_definition(self, record: dict[str, Any], **changes: Any) -> dict[str, Any]:
        return await self.hass.async_add_executor_job(
            self._save_definition_sync,
            record,
            **changes,
        )

    def _restore_sync(self, transaction: dict[str, Any]) -> None:
        path, _value = self._load_path(str(transaction["path"]))
        temp = path.with_suffix(path.suffix + ".esc-rollback")
        temp.write_text(str(transaction["previous_text"]), encoding="utf-8")
        temp.replace(path)

    async def async_restore(self, transaction: dict[str, Any]) -> None:
        await self.hass.async_add_executor_job(self._restore_sync, transaction)
