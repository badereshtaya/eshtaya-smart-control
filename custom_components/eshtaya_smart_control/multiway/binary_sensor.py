"""Binary sensors for Eshtaya Multi-Way Control."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    DATA_RUNTIME,
    DOMAIN,
    HEALTH_HEALTHY,
    SIGNAL_GROUPS_UPDATED,
    SIGNAL_SMART_GROUPS_UPDATED,
)
from .entity import MultiWayEntity
from .smart_entity import SmartGroupEntity
from .smart_native_group import async_setup_smart_native_platform


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Multi-Way and Smart Group binary sensors."""
    known_multi: set[str] = set()
    known_smart: set[str] = set()

    @callback
    def add_multi() -> None:
        store = hass.data[DOMAIN][DATA_RUNTIME]["store"]
        entities: list[BinarySensorEntity] = []
        for group in store.groups():
            group_id = group["id"]
            if group_id in known_multi:
                continue
            known_multi.add(group_id)
            entities.append(MultiWayInSyncSensor(hass, group_id))
        if entities:
            async_add_entities(entities)

    @callback
    def add_smart() -> None:
        store = hass.data[DOMAIN][DATA_RUNTIME]["smart_store"]
        entities: list[BinarySensorEntity] = []
        for group in store.groups():
            group_id = group["id"]
            if group_id in known_smart:
                continue
            known_smart.add(group_id)
            entities.append(SmartGroupHealthySensor(hass, group_id))
        if entities:
            async_add_entities(entities)

    add_multi()
    add_smart()
    entry.async_on_unload(
        async_dispatcher_connect(hass, SIGNAL_GROUPS_UPDATED, add_multi)
    )
    entry.async_on_unload(
        async_dispatcher_connect(hass, SIGNAL_SMART_GROUPS_UPDATED, add_smart)
    )
    await async_setup_smart_native_platform(hass, entry, async_add_entities, "binary_sensor")


class MultiWayInSyncSensor(MultiWayEntity, BinarySensorEntity):
    """Report whether a Multi-Way group is synchronized."""

    _attr_translation_key = "in_sync"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, hass: HomeAssistant, group_id: str) -> None:
        super().__init__(hass, group_id, "in_sync")

    @property
    def is_on(self) -> bool:
        """Return true when the group is healthy."""
        return self.manager.status(self.group_id).get("health") == HEALTH_HEALTHY


class SmartGroupHealthySensor(SmartGroupEntity, BinarySensorEntity):
    """Report whether a Smart Group is healthy."""

    _attr_translation_key = "smart_group_healthy"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, hass: HomeAssistant, group_id: str) -> None:
        super().__init__(hass, group_id, "healthy")

    @property
    def is_on(self) -> bool:
        """Return true when the Smart Group is healthy."""
        return self.manager.status(self.group_id).get("health") == "healthy"
