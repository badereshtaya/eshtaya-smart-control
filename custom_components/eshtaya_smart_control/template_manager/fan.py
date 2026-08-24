"""Fan entities managed by Eshtaya Smart Control Template Manager."""
from __future__ import annotations

from homeassistant.components.fan import FanEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DATA_TEMPLATE_MANAGER, SIGNAL_TEMPLATE_CHANGED
from .entity import TemplateManagedEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    manager = hass.data["eshtaya_smart_control"][DATA_TEMPLATE_MANAGER]
    known: set[str] = set()

    @callback
    def add_entities() -> None:
        records = [item for item in manager.store.templates() if item.get("type") == "fan"]
        current_ids = {str(item["entity_id"]) for item in records}
        known.intersection_update(current_ids)
        entities = []
        for record in records:
            entity_id = str(record["entity_id"])
            if entity_id in known:
                continue
            known.add(entity_id)
            entities.append(ManagedTemplateFan(hass, manager, record))
        if entities:
            async_add_entities(entities)

    add_entities()
    entry.async_on_unload(async_dispatcher_connect(hass, SIGNAL_TEMPLATE_CHANGED, add_entities))


class ManagedTemplateFan(TemplateManagedEntity, FanEntity):
    """Permanent fan wrapper whose source is normally a Tuya switch."""

    @property
    def is_on(self) -> bool | None:
        state = self.hass.states.get(self.source_entity)
        if state is None:
            return None
        return state.state == "on"

    async def async_turn_on(self, **kwargs) -> None:
        await self.hass.services.async_call(
            "switch", "turn_on", {"entity_id": self.source_entity}, blocking=True
        )

    async def async_turn_off(self, **kwargs) -> None:
        await self.hass.services.async_call(
            "switch", "turn_off", {"entity_id": self.source_entity}, blocking=True
        )
