"""v1.2 enhancements: batch actions, sync health and orphan rule maintenance."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Iterable

from homeassistant.core import HomeAssistant

from .const import RULE_ALLOW, RULE_EXCLUDE, RULE_INHERIT, RULE_VALUES
from .manager_v11 import EntityManagerV11


class EntityManagerV12(EntityManagerV11):
    """Entity manager with UX-oriented maintenance helpers."""

    def __init__(self, hass: HomeAssistant) -> None:
        super().__init__(hass)

    @staticmethod
    def _path_meta(path: Path) -> dict[str, Any]:
        if not path.exists():
            return {"exists": False, "size": 0, "sha256": ""}
        raw = path.read_bytes()
        return {
            "exists": True,
            "size": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }

    def _sync_meta(self) -> dict[str, Any]:
        primary = self._path_meta(self.hidden_path)
        public = self._path_meta(self.public_hidden_path)
        synced = (
            primary["exists"]
            and public["exists"]
            and primary["sha256"] == public["sha256"]
        )
        return {"ok": synced, "primary": primary, "public": public}

    def _orphan_entity_ids(self) -> list[str]:
        current_ids = self._all_entity_ids()
        return sorted(
            entity_id
            for entity_id in self.data.get("entities", {})
            if entity_id not in current_ids
        )

    async def async_get_snapshot(self, *, include_file: bool = False) -> dict[str, Any]:
        payload = await super().async_get_snapshot(include_file=include_file)
        orphan_ids = self._orphan_entity_ids()
        payload["file"]["sync"] = await self.hass.async_add_executor_job(self._sync_meta)
        payload["maintenance"] = {
            "orphan_rules": orphan_ids,
            "orphan_count": len(orphan_ids),
        }
        payload["stats"]["unavailable"] = sum(
            1 for item in payload["entities"] if not item.get("available", False)
        )
        payload["stats"]["overrides"] = sum(
            1 for item in payload["entities"] if item.get("rule") != RULE_INHERIT
        )
        return payload

    async def async_set_many_rules(self, entity_ids: Iterable[str], mode: str) -> int:
        if mode not in RULE_VALUES:
            raise ValueError("Invalid rule mode")

        current_ids = self._all_entity_ids()
        unique_ids = list(dict.fromkeys(str(value).strip() for value in entity_ids if str(value).strip()))
        changed = 0
        rules = self.data.setdefault("entities", {})

        for entity_id in unique_ids:
            if entity_id not in current_ids:
                continue
            if mode == RULE_INHERIT:
                if entity_id in rules:
                    rules.pop(entity_id, None)
                    changed += 1
            elif rules.get(entity_id) != mode:
                rules[entity_id] = mode
                changed += 1

        if changed:
            await self.async_regenerate_hidden_file(save_store=True)
        return changed

    async def async_repair_sync(self) -> dict[str, Any]:
        await self.async_regenerate_hidden_file(save_store=False)
        return await self.hass.async_add_executor_job(self._sync_meta)

    async def async_cleanup_orphan_rules(self) -> int:
        orphan_ids = self._orphan_entity_ids()
        if not orphan_ids:
            return 0
        rules = self.data.setdefault("entities", {})
        for entity_id in orphan_ids:
            rules.pop(entity_id, None)
        await self.async_regenerate_hidden_file(save_store=True)
        return len(orphan_ids)
