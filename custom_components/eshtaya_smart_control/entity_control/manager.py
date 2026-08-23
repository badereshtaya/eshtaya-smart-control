"""Core data and rule manager for Eshtaya Entity Manager."""

from __future__ import annotations

from collections.abc import Iterable
import logging
from pathlib import Path
import shutil
from typing import Any

import yaml

from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.storage import Store

from .const import (
    BACKUP_FILE,
    DEFAULT_DISABLED_DOMAINS,
    DEFAULT_EXCLUDED_ENTITY_CATEGORIES,
    DEFAULT_EXCLUDED_NAME_KEYWORDS,
    HIDDEN_FILE,
    RULE_ALLOW,
    RULE_EXCLUDE,
    RULE_INHERIT,
    STORAGE_KEY,
    STORAGE_VERSION,
)

_LOGGER = logging.getLogger(__name__)


def _domain_of(entity_id: str) -> str:
    return entity_id.partition(".")[0]


def _safe_lower(value: Any) -> str:
    return str(value or "").casefold()


class EntityManager:
    """Manage entity names, Alexa visibility rules and the generated YAML file."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self.data: dict[str, Any] = {}
        self.hidden_path = Path(hass.config.path(HIDDEN_FILE))
        self.backup_path = Path(hass.config.path(BACKUP_FILE))

    async def async_initialize(self) -> None:
        """Load persisted rules, importing an existing YAML file when appropriate."""
        loaded = await self.store.async_load()
        if loaded:
            self.data = self._normalize_data(loaded)
        else:
            existing_file = await self.hass.async_add_executor_job(self.hidden_path.exists)
            if existing_file:
                imported = await self.hass.async_add_executor_job(self._read_existing_hidden_file)
                self.data = self._default_data(import_mode=True)
                self.data["entities"] = {entity_id: RULE_EXCLUDE for entity_id in imported}
                self.data["migration"]["imported_existing_file"] = True
                await self.hass.async_add_executor_job(self._backup_existing_file)
            else:
                self.data = self._default_data(import_mode=False)

            self._ensure_domains()
            await self.store.async_save(self.data)

        self._ensure_domains()
        await self.async_regenerate_hidden_file(save_store=True)

    def _default_data(self, *, import_mode: bool) -> dict[str, Any]:
        return {
            "domains": {},
            "entities": {},
            "defaults": {
                "exclude_entity_category": []
                if import_mode
                else list(DEFAULT_EXCLUDED_ENTITY_CATEGORIES),
                "exclude_name_keywords": []
                if import_mode
                else list(DEFAULT_EXCLUDED_NAME_KEYWORDS),
            },
            "migration": {
                "imported_existing_file": False,
                "domain_default_enabled": True if import_mode else None,
            },
        }

    def _normalize_data(self, raw: dict[str, Any]) -> dict[str, Any]:
        defaults = raw.get("defaults") if isinstance(raw.get("defaults"), dict) else {}
        migration = raw.get("migration") if isinstance(raw.get("migration"), dict) else {}

        domains: dict[str, bool] = {}
        for domain, value in (raw.get("domains") or {}).items():
            if isinstance(value, dict):
                domains[str(domain)] = bool(value.get("enabled", True))
            else:
                domains[str(domain)] = bool(value)

        entities: dict[str, str] = {}
        for entity_id, value in (raw.get("entities") or {}).items():
            if isinstance(value, dict):
                enabled = value.get("enabled")
                if enabled is True:
                    entities[str(entity_id)] = RULE_ALLOW
                elif enabled is False:
                    entities[str(entity_id)] = RULE_EXCLUDE
            elif value in {RULE_ALLOW, RULE_EXCLUDE}:
                entities[str(entity_id)] = str(value)

        return {
            "domains": domains,
            "entities": entities,
            "defaults": {
                "exclude_entity_category": [
                    str(v).strip().casefold()
                    for v in defaults.get(
                        "exclude_entity_category", DEFAULT_EXCLUDED_ENTITY_CATEGORIES
                    )
                    if str(v).strip()
                ],
                "exclude_name_keywords": [
                    str(v).strip()
                    for v in defaults.get(
                        "exclude_name_keywords", DEFAULT_EXCLUDED_NAME_KEYWORDS
                    )
                    if str(v).strip()
                ],
            },
            "migration": {
                "imported_existing_file": bool(
                    migration.get("imported_existing_file", False)
                ),
                "domain_default_enabled": migration.get("domain_default_enabled"),
            },
        }

    def _read_existing_hidden_file(self) -> list[str]:
        if not self.hidden_path.exists():
            return []
        try:
            parsed = yaml.safe_load(self.hidden_path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as err:
            raise ValueError(f"Unable to import {self.hidden_path}: {err}") from err

        if parsed is None:
            return []
        if isinstance(parsed, list):
            return sorted(
                {
                    str(item).strip()
                    for item in parsed
                    if isinstance(item, str) and "." in item
                }
            )
        raise ValueError(
            f"Existing {self.hidden_path} is not a YAML list; refusing to overwrite it"
        )

    def _backup_existing_file(self) -> None:
        if not self.hidden_path.exists() or self.backup_path.exists():
            return
        try:
            shutil.copy2(self.hidden_path, self.backup_path)
        except OSError as err:
            _LOGGER.warning("Unable to back up %s: %s", self.hidden_path, err)

    def _all_entity_ids(self) -> set[str]:
        registry = er.async_get(self.hass)
        entity_ids = {entry.entity_id for entry in registry.entities.values()}
        entity_ids.update(state.entity_id for state in self.hass.states.async_all())
        return entity_ids

    def _ensure_domains(self) -> bool:
        changed = False
        domains = self.data.setdefault("domains", {})
        migration = self.data.setdefault("migration", {})
        imported_default = migration.get("domain_default_enabled")

        for domain in sorted({_domain_of(eid) for eid in self._all_entity_ids() if "." in eid}):
            if domain in domains:
                continue
            if isinstance(imported_default, bool):
                domains[domain] = imported_default
            else:
                domains[domain] = domain not in DEFAULT_DISABLED_DOMAINS
            changed = True
        return changed

    def _display_name_for(self, entity_id: str, reg_entry: er.RegistryEntry | None) -> str:
        if reg_entry and reg_entry.name:
            return reg_entry.name
        state = self.hass.states.get(entity_id)
        if state:
            friendly_name = state.attributes.get("friendly_name")
            if friendly_name:
                return str(friendly_name)
        if reg_entry and reg_entry.original_name:
            return reg_entry.original_name
        return entity_id

    def _entity_category_for(self, entity_id: str, reg_entry: er.RegistryEntry | None) -> str:
        if reg_entry and reg_entry.entity_category is not None:
            return str(reg_entry.entity_category)
        state = self.hass.states.get(entity_id)
        if state and state.attributes.get("entity_category"):
            return str(state.attributes["entity_category"])
        return ""

    def evaluate(self, entity_id: str, display_name: str = "", entity_category: str = "") -> tuple[bool, str]:
        """Return (excluded, reason) using the same precedence as the original PHP tool."""
        override = self.data.get("entities", {}).get(entity_id, RULE_INHERIT)
        if override == RULE_ALLOW:
            return False, "Force allow"
        if override == RULE_EXCLUDE:
            return True, "Force exclude"

        domain = _domain_of(entity_id)
        if not bool(self.data.get("domains", {}).get(domain, True)):
            return True, f"Domain off: {domain}"

        category = _safe_lower(entity_category)
        excluded_categories = {
            _safe_lower(value)
            for value in self.data.get("defaults", {}).get("exclude_entity_category", [])
        }
        if category and category in excluded_categories:
            return True, f"Auto: entity_category={category}"

        searchable = f"{_safe_lower(entity_id)} {_safe_lower(display_name)}"
        for keyword in self.data.get("defaults", {}).get("exclude_name_keywords", []):
            keyword = str(keyword).strip()
            if keyword and _safe_lower(keyword) in searchable:
                return True, f"Auto: keyword={keyword}"

        return False, "Included"

    def _build_entity(self, entity_id: str) -> dict[str, Any]:
        entity_registry = er.async_get(self.hass)
        device_registry = dr.async_get(self.hass)
        area_registry = ar.async_get(self.hass)

        reg_entry = entity_registry.async_get(entity_id)
        state = self.hass.states.get(entity_id)
        display_name = self._display_name_for(entity_id, reg_entry)
        category = self._entity_category_for(entity_id, reg_entry)
        excluded, reason = self.evaluate(entity_id, display_name, category)

        device_id = reg_entry.device_id if reg_entry else None
        area_id = reg_entry.area_id if reg_entry else None
        device_name = ""
        area_name = ""
        platform = reg_entry.platform if reg_entry else ""
        user_name = reg_entry.name if reg_entry else None
        original_name = reg_entry.original_name if reg_entry else None

        if device_id:
            device = device_registry.async_get(device_id)
            if device:
                device_name = device.name_by_user or device.name or ""
                area_id = area_id or device.area_id
        if area_id:
            area = area_registry.async_get_area(area_id)
            if area:
                area_name = area.name

        state_value = state.state if state else "unavailable"
        available = state is not None and state_value not in {"unavailable", "unknown"}

        return {
            "entity_id": entity_id,
            "domain": _domain_of(entity_id),
            "name": display_name,
            "registry_name": user_name,
            "original_name": original_name,
            "state": state_value,
            "available": available,
            "entity_category": category,
            "platform": platform,
            "device_id": device_id,
            "device_name": device_name,
            "area_id": area_id,
            "area_name": area_name,
            "can_rename": reg_entry is not None,
            "rule": self.data.get("entities", {}).get(entity_id, RULE_INHERIT),
            "excluded": excluded,
            "reason": reason,
        }

    def get_entities(self) -> list[dict[str, Any]]:
        """Return all registered/state entities with computed Alexa visibility metadata."""
        entities = [self._build_entity(entity_id) for entity_id in sorted(self._all_entity_ids())]
        return entities

    async def async_get_snapshot(self, *, include_file: bool = False) -> dict[str, Any]:
        changed = self._ensure_domains()
        if changed:
            await self.store.async_save(self.data)

        entities = self.get_entities()
        excluded_count = sum(1 for item in entities if item["excluded"])
        renamed_count = sum(1 for item in entities if item.get("registry_name") is not None)
        domains = [
            {
                "domain": domain,
                "enabled": bool(enabled),
                "count": sum(1 for item in entities if item["domain"] == domain),
                "excluded": sum(
                    1
                    for item in entities
                    if item["domain"] == domain and item["excluded"]
                ),
            }
            for domain, enabled in sorted(self.data.get("domains", {}).items())
        ]

        payload: dict[str, Any] = {
            "entities": entities,
            "domains": domains,
            "settings": {
                "exclude_entity_category": list(
                    self.data.get("defaults", {}).get("exclude_entity_category", [])
                ),
                "exclude_name_keywords": list(
                    self.data.get("defaults", {}).get("exclude_name_keywords", [])
                ),
            },
            "stats": {
                "total": len(entities),
                "included": len(entities) - excluded_count,
                "excluded": excluded_count,
                "renamed": renamed_count,
            },
            "file": {
                "path": str(self.hidden_path),
                "backup_path": str(self.backup_path),
                "exists": True,
            },
        }
        if include_file:
            payload["file"]["content"] = await self.hass.async_add_executor_job(
                self._read_generated_file_text
            )
        return payload

    def _read_generated_file_text(self) -> str:
        try:
            return self.hidden_path.read_text(encoding="utf-8")
        except OSError:
            return ""

    async def async_set_entity_rule(self, entity_id: str, mode: str) -> None:
        if entity_id not in self._all_entity_ids():
            raise ValueError(f"Entity not found: {entity_id}")
        if mode == RULE_INHERIT:
            self.data.setdefault("entities", {}).pop(entity_id, None)
        else:
            self.data.setdefault("entities", {})[entity_id] = mode
        await self.async_regenerate_hidden_file(save_store=True)

    async def async_set_domain(self, domain: str, enabled: bool) -> None:
        if not domain or "." in domain:
            raise ValueError("Invalid domain")
        self.data.setdefault("domains", {})[domain] = bool(enabled)
        await self.async_regenerate_hidden_file(save_store=True)

    async def async_set_defaults(self, categories: Iterable[str], keywords: Iterable[str]) -> None:
        self.data.setdefault("defaults", {})["exclude_entity_category"] = sorted(
            {_safe_lower(v.strip()) for v in categories if str(v).strip()}
        )
        self.data.setdefault("defaults", {})["exclude_name_keywords"] = list(
            dict.fromkeys(str(v).strip() for v in keywords if str(v).strip())
        )
        await self.async_regenerate_hidden_file(save_store=True)

    async def async_bulk_rule(
        self,
        *,
        keyword: str,
        where: str,
        mode: str,
        domain: str | None = None,
    ) -> int:
        keyword_folded = _safe_lower(keyword.strip())
        if not keyword_folded:
            raise ValueError("Keyword is required")

        changed = 0
        for item in self.get_entities():
            if domain and item["domain"] != domain:
                continue
            match = False
            if where in {"id", "both"}:
                match = match or keyword_folded in _safe_lower(item["entity_id"])
            if where in {"name", "both"}:
                match = match or keyword_folded in _safe_lower(item["name"])
            if not match:
                continue

            if mode == RULE_INHERIT:
                if item["entity_id"] in self.data.setdefault("entities", {}):
                    self.data["entities"].pop(item["entity_id"], None)
                    changed += 1
            elif self.data.setdefault("entities", {}).get(item["entity_id"]) != mode:
                self.data["entities"][item["entity_id"]] = mode
                changed += 1

        if changed:
            await self.async_regenerate_hidden_file(save_store=True)
        return changed

    async def async_rename_entity(self, entity_id: str, name: str | None) -> None:
        registry = er.async_get(self.hass)
        entry = registry.async_get(entity_id)
        if entry is None:
            raise ValueError(
                "This entity is not present in Home Assistant's entity registry and cannot be renamed here"
            )
        normalized_name = None if name is None or not name.strip() else name.strip()
        registry.async_update_entity(entity_id, name=normalized_name)

    def _generate_hidden_file_text(self) -> str:
        lines = [
            "# Generated by Eshtaya Entity Manager.\n",
            "# Manage this file from Home Assistant > Entity Manager.\n",
            "# Manual edits may be overwritten.\n",
        ]
        excluded_map: dict[str, str] = {}
        current_ids = self._all_entity_ids()
        for item in self.get_entities():
            if item["excluded"]:
                excluded_map[item["entity_id"]] = item["reason"]

        # Preserve explicit Force Exclude entries even if an integration/entity is
        # temporarily not loaded, so a restart or outage cannot silently erase them.
        for entity_id, mode in self.data.get("entities", {}).items():
            if mode == RULE_EXCLUDE and entity_id not in current_ids:
                excluded_map[entity_id] = "Force exclude (entity not currently loaded)"

        excluded = sorted(excluded_map.items())
        lines.append(f"# Excluded entities: {len(excluded)}\n\n")
        for entity_id, reason in excluded:
            clean_reason = str(reason).replace("\n", " ").replace("#", "").strip()
            lines.append(f"- {entity_id}  # {clean_reason}\n")
        return "".join(lines)

    def _write_hidden_file_atomic(self, content: str) -> None:
        self.hidden_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.hidden_path.with_suffix(self.hidden_path.suffix + ".tmp")
        temp_path.write_text(content, encoding="utf-8")
        temp_path.replace(self.hidden_path)

    async def async_handle_registry_event(self, event_data: dict[str, Any]) -> None:
        """Migrate explicit rules when an entity_id changes, then regenerate YAML."""
        old_entity_id = event_data.get("old_entity_id")
        new_entity_id = event_data.get("entity_id")
        if old_entity_id and new_entity_id and old_entity_id != new_entity_id:
            entities = self.data.setdefault("entities", {})
            if old_entity_id in entities and new_entity_id not in entities:
                entities[new_entity_id] = entities.pop(old_entity_id)
        await self.async_regenerate_hidden_file(save_store=True)

    async def async_regenerate_hidden_file(self, *, save_store: bool = False) -> int:
        self._ensure_domains()
        content = self._generate_hidden_file_text()
        await self.hass.async_add_executor_job(self._write_hidden_file_atomic, content)
        if save_store:
            await self.store.async_save(self.data)
        return content.count("\n- ") + (1 if content.startswith("- ") else 0)
