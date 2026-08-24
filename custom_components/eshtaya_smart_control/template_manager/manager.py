"""Runtime manager for permanent light/fan wrappers backed by source switches."""
from __future__ import annotations

import asyncio
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import SIGNAL_TEMPLATE_CHANGED, STARTUP_GRACE_SECONDS, STARTUP_RETRY_SECONDS, SUPPORTED_TYPES
from .store import TemplateManagerStore


class TemplateManager:
    """Own permanent template mappings and source reconciliation."""

    def __init__(self, hass: HomeAssistant, store: TemplateManagerStore) -> None:
        self.hass = hass
        self.store = store
        self._scan_lock = asyncio.Lock()
        self._ready = False
        self._last_snapshot: dict[str, Any] = {"managed": [], "candidates": [], "missing": []}

    @property
    def ready(self) -> bool:
        return self._ready

    async def async_start(self) -> None:
        self._ready = False
        deadline = self.hass.loop.time() + STARTUP_GRACE_SECONDS
        while self.hass.loop.time() < deadline:
            if self._sources_have_started():
                break
            await asyncio.sleep(STARTUP_RETRY_SECONDS)
        self._ready = True
        await self.async_scan()

    def _sources_have_started(self) -> bool:
        records = self.store.templates()
        if not records:
            return True
        if self.hass.is_running:
            return True
        return all(
            not str(record.get("source_entity") or "")
            or self.hass.states.get(str(record.get("source_entity"))) is not None
            for record in records
        )

    def _candidate_rows(self) -> list[dict[str, Any]]:
        registry = er.async_get(self.hass)
        managed_sources = {str(item.get("source_entity")) for item in self.store.templates()}
        rows: list[dict[str, Any]] = []
        for state in self.hass.states.async_all("switch"):
            if state.entity_id in managed_sources:
                continue
            reg = registry.async_get(state.entity_id)
            platform = reg.platform if reg else None
            if platform not in {"tuya", None} and not str(platform).startswith("tuya"):
                continue
            rows.append({
                "entity_id": state.entity_id,
                "name": state.attributes.get("friendly_name") or state.entity_id,
                "state": state.state,
                "platform": platform or "unknown",
                "device_id": reg.device_id if reg else None,
            })
        return sorted(rows, key=lambda row: str(row["entity_id"]))

    def _managed_rows(self, candidates: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        registry = er.async_get(self.hass)
        managed: list[dict[str, Any]] = []
        missing: list[dict[str, Any]] = []
        for record in self.store.templates():
            source = str(record.get("source_entity") or "")
            source_state = self.hass.states.get(source)
            source_reg = registry.async_get(source) if source else None
            row = {
                **deepcopy(record),
                "source_state": source_state.state if source_state else "missing",
                "source_platform": source_reg.platform if source_reg else None,
            }
            if source_state is not None:
                managed.append(row)
                continue
            if not self._ready:
                managed.append({**row, "source_state": "starting"})
                continue
            suggestions = self._suggestions(record, candidates)
            missing.append({
                **row,
                "missing_reason": "source_entity_not_found",
                "suggestions": suggestions,
                "best_match": suggestions[0] if suggestions else None,
            })
        return managed, missing

    def _suggestions(self, record: dict[str, Any], candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        source = str(record.get("source_entity") or "")
        old_tail = source.split(".", 1)[-1].lower()
        words = {part for part in old_tail.replace("-", "_").split("_") if part}
        scored: list[dict[str, Any]] = []
        for candidate in candidates:
            tail = str(candidate["entity_id"]).split(".", 1)[-1].lower()
            candidate_words = {part for part in tail.replace("-", "_").split("_") if part}
            union = words | candidate_words
            overlap = words & candidate_words
            score = 0 if not union else round((len(overlap) / len(union)) * 100)
            if old_tail and old_tail == tail:
                score = 100
            scored.append({**candidate, "score": score})
        scored.sort(key=lambda item: (-int(item.get("score") or 0), str(item["entity_id"])))
        return scored[:5]

    async def async_scan(self) -> dict[str, Any]:
        async with self._scan_lock:
            candidates = self._candidate_rows()
            managed, missing = self._managed_rows(candidates)
            snapshot = {
                "ready": self._ready,
                "managed": managed,
                "candidates": candidates,
                "missing": missing,
                "managed_count": len(managed),
                "available_count": len(candidates),
                "missing_count": len(missing),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "migration": self.store.migration(),
            }
            self._last_snapshot = snapshot
            async_dispatcher_send(self.hass, SIGNAL_TEMPLATE_CHANGED)
            return deepcopy(snapshot)

    def snapshot(self) -> dict[str, Any]:
        return deepcopy(self._last_snapshot)

    async def async_create(self, *, source_entity: str, template_type: str, name: str, entity_id: str) -> dict[str, Any]:
        template_type = template_type.lower().strip()
        entity_id = entity_id.strip()
        source_entity = source_entity.strip()
        if template_type not in SUPPORTED_TYPES:
            raise ValueError(f"Unsupported template type: {template_type}")
        if not entity_id.startswith(f"{template_type}."):
            raise ValueError(f"Entity ID must start with {template_type}.")
        if self.hass.states.get(source_entity) is None:
            raise ValueError(f"Source entity not found: {source_entity}")
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
        await self.store.async_upsert(record)
        async_dispatcher_send(self.hass, SIGNAL_TEMPLATE_CHANGED)
        await self.async_scan()
        return record

    async def async_edit(self, *, managed_entity: str, name: str, entity_id: str) -> dict[str, Any]:
        record = self.store.get(managed_entity)
        if not record:
            raise ValueError(f"Managed entity not found: {managed_entity}")
        entity_id = entity_id.strip()
        if not entity_id.startswith(f"{record['type']}."):
            raise ValueError(f"Entity ID must remain in the {record['type']} domain")
        registry = er.async_get(self.hass)
        entry = registry.async_get(managed_entity)
        if entity_id != managed_entity:
            occupied = registry.async_get(entity_id) or self.hass.states.get(entity_id)
            if occupied:
                raise ValueError(f"Entity ID is already in use: {entity_id}")
            if entry:
                registry.async_update_entity(managed_entity, new_entity_id=entity_id)
        elif entry and name.strip():
            registry.async_update_entity(managed_entity, name=name.strip())
        record["old_entity_id"] = managed_entity
        record["entity_id"] = entity_id
        record["name"] = name.strip() or entity_id
        record["unique_id"] = str(record.get("unique_id") or f"esc_template::{managed_entity}")
        await self.store.async_upsert(record)
        async_dispatcher_send(self.hass, SIGNAL_TEMPLATE_CHANGED)
        await self.async_scan()
        return record

    async def async_delete(self, managed_entity: str) -> None:
        if not self.store.get(managed_entity):
            raise ValueError(f"Managed entity not found: {managed_entity}")
        await self.store.async_delete(managed_entity)
        registry = er.async_get(self.hass)
        if registry.async_get(managed_entity):
            registry.async_remove(managed_entity)
        async_dispatcher_send(self.hass, SIGNAL_TEMPLATE_CHANGED)
        await self.async_scan()

    async def async_relink(self, *, managed_entity: str, source_entity: str) -> dict[str, Any]:
        record = self.store.get(managed_entity)
        if not record:
            raise ValueError(f"Managed entity not found: {managed_entity}")
        if self.hass.states.get(source_entity) is None:
            raise ValueError(f"Source entity not found: {source_entity}")
        record["source_entity"] = source_entity.strip()
        await self.store.async_upsert(record)
        async_dispatcher_send(self.hass, SIGNAL_TEMPLATE_CHANGED)
        await self.async_scan()
        return record

    def source_available(self, entity_id: str) -> bool:
        state = self.hass.states.get(entity_id)
        return state is not None and state.state not in {STATE_UNKNOWN, STATE_UNAVAILABLE}
