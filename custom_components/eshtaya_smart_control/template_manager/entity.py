"""Entity primitives for the integrated Template Manager."""
from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import SIGNAL_TEMPLATE_CHANGED


class TemplateManagedEntity:
    """Mixin shared by managed light/fan wrappers."""

    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant, manager, record: dict[str, Any]) -> None:
        self.hass = hass
        self.manager = manager
        self.record = record
        self.entity_id = str(record["entity_id"])
        self._attr_unique_id = str(record.get("unique_id") or f"esc_template::{self.entity_id}")
        self._attr_name = str(record.get("name") or self.entity_id)

    @property
    def source_entity(self) -> str:
        current = self.manager.store.get(self.entity_id) or self.record
        return str(current.get("source_entity") or "")

    @property
    def available(self) -> bool:
        return self.hass.states.get(self.source_entity) is not None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(async_dispatcher_connect(self.hass, SIGNAL_TEMPLATE_CHANGED, self._template_changed))

    @callback
    def _template_changed(self) -> None:
        current = self.manager.store.get(self.entity_id)
        if current is None:
            self.hass.async_create_task(self.async_remove(), f"Remove template entity {self.entity_id}")
            return
        self.record = current
        self._attr_name = str(current.get("name") or self.entity_id)
        self.async_write_ha_state()
