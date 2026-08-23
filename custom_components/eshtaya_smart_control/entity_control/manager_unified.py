"""Unified Entity Control manager with safe legacy storage migration."""
from __future__ import annotations

from homeassistant.helpers.storage import Store

from .manager_v12 import EntityManagerV12


class UnifiedEntityManager(EntityManagerV12):
    """Use the new storage key and import the former standalone storage once."""

    async def async_initialize(self) -> None:
        current = await self.store.async_load()
        if not current:
            legacy = await Store(self.hass, 1, "eshtaya_entity_manager").async_load()
            if isinstance(legacy, dict) and legacy:
                await self.store.async_save(self._normalize_data(legacy))
        await super().async_initialize()
