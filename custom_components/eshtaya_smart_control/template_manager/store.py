"""Persistent storage for integrated permanent template entities."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import STORE_KEY, STORE_VERSION


class TemplateManagerStore:
    """Persist template mappings independently from the legacy integration."""

    def __init__(self, hass: HomeAssistant) -> None:
        self._store = Store(hass, STORE_VERSION, STORE_KEY)
        self._data: dict[str, Any] = {"templates": {}, "migration": {}}

    async def async_load(self) -> None:
        loaded = await self._store.async_load()
        if isinstance(loaded, dict):
            self._data = {
                "templates": dict(loaded.get("templates") or {}),
                "migration": dict(loaded.get("migration") or {}),
            }

    async def async_save(self) -> None:
        await self._store.async_save(self._data)

    def templates(self) -> list[dict[str, Any]]:
        return [deepcopy(value) for value in self._data["templates"].values()]

    def get(self, entity_id: str) -> dict[str, Any] | None:
        value = self._data["templates"].get(entity_id)
        return deepcopy(value) if value else None

    async def async_upsert(self, record: dict[str, Any]) -> None:
        entity_id = str(record["entity_id"])
        old_entity_id = str(record.get("old_entity_id") or entity_id)
        if old_entity_id != entity_id:
            self._data["templates"].pop(old_entity_id, None)
        clean = deepcopy(record)
        clean.pop("old_entity_id", None)
        self._data["templates"][entity_id] = clean
        await self.async_save()

    async def async_replace_all(self, records: list[dict[str, Any]]) -> None:
        self._data["templates"] = {
            str(record["entity_id"]): deepcopy(record) for record in records
        }
        await self.async_save()

    async def async_delete(self, entity_id: str) -> None:
        self._data["templates"].pop(entity_id, None)
        await self.async_save()

    def migration(self) -> dict[str, Any]:
        return deepcopy(self._data.get("migration") or {})

    async def async_set_migration(self, migration: dict[str, Any]) -> None:
        self._data["migration"] = deepcopy(migration)
        await self.async_save()
