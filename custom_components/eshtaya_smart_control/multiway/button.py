"""Button entities for Eshtaya Multi-Way Control."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    DATA_RUNTIME,
    DOMAIN,
    SIGNAL_GROUPS_UPDATED,
    SIGNAL_SMART_GROUPS_UPDATED,
    SMART_ACTION_TYPES,
)
from .entity import MultiWayEntity
from .smart_entity import SmartGroupEntity
from .smart_native_group import async_setup_smart_native_platform


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up sync buttons for both engines."""
    known_multi: set[str] = set()
    known_smart: set[str] = set()
    known_action: set[str] = set()

    @callback
    def add_multi() -> None:
        store = hass.data[DOMAIN][DATA_RUNTIME]["store"]
        entities: list[ButtonEntity] = []
        for group in store.groups():
            group_id = group["id"]
            if group_id in known_multi:
                continue
            known_multi.add(group_id)
            entities.append(MultiWaySyncButton(hass, group_id))
        if entities:
            async_add_entities(entities)

    @callback
    def add_smart() -> None:
        store = hass.data[DOMAIN][DATA_RUNTIME]["smart_store"]
        groups = store.groups()
        sync_ids = {
            group["id"]
            for group in groups
            if (group.get("group_type") or group.get("virtual_type")) not in SMART_ACTION_TYPES
        }
        action_ids = {
            group["id"]
            for group in groups
            if (group.get("group_type") or group.get("virtual_type")) in SMART_ACTION_TYPES
        }
        known_smart.intersection_update(sync_ids)
        known_action.intersection_update(action_ids)
        entities: list[ButtonEntity] = []
        for group in groups:
            group_id = group["id"]
            group_type = group.get("group_type") or group.get("virtual_type")
            if group_type not in SMART_ACTION_TYPES and group_id not in known_smart:
                known_smart.add(group_id)
                entities.append(SmartGroupSyncButton(hass, group_id))
            if group_type in SMART_ACTION_TYPES and group_id not in known_action:
                known_action.add(group_id)
                entities.append(SmartActionGroupButton(hass, group_id))
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
    await async_setup_smart_native_platform(hass, entry, async_add_entities, "button")


class MultiWaySyncButton(MultiWayEntity, ButtonEntity):
    """Synchronize a Multi-Way group on demand."""

    _attr_translation_key = "sync_now"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, hass: HomeAssistant, group_id: str) -> None:
        super().__init__(hass, group_id, "sync")

    def _still_expected(self, group):
        if group is None:
            return False
        group_type = group.get("group_type") or group.get("virtual_type")
        return group_type not in SMART_ACTION_TYPES

    async def async_press(self) -> None:
        """Synchronize the group."""
        await self.manager.async_sync_group(self.group_id)


class SmartGroupSyncButton(SmartGroupEntity, ButtonEntity):
    """Synchronize a Smart Group on demand."""

    _attr_translation_key = "smart_group_sync"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, hass: HomeAssistant, group_id: str) -> None:
        super().__init__(hass, group_id, "sync")

    async def async_press(self) -> None:
        """Synchronize the Smart Group."""
        await self.manager.async_sync(self.group_id)


class SmartActionGroupButton(SmartGroupEntity, ButtonEntity):
    """Run a scene/script/automation Smart Action Group."""

    _attr_icon = "mdi:play-box-multiple-outline"

    def __init__(self, hass: HomeAssistant, group_id: str) -> None:
        super().__init__(hass, group_id, "control_action")
        group = self.group
        self._attr_translation_key = None
        self._attr_name = None
        if group:
            preferred = group.get("preferred_entity_id")
            if preferred and "." in preferred:
                self._attr_suggested_object_id = preferred.split(".", 1)[1]
            else:
                self._attr_suggested_object_id = group.get("name")

    def _still_expected(self, group):
        if group is None:
            return False
        group_type = group.get("group_type") or group.get("virtual_type")
        return group_type in SMART_ACTION_TYPES

    @property
    def available(self) -> bool:
        group = self.group
        return bool(
            group
            and group.get("enabled", True)
            and not group.get("maintenance", False)
        )

    async def async_press(self) -> None:
        """Run every enabled action member once."""
        await self.manager.async_run_action_group(
            self.group_id, source="virtual_button", origin="button_entity"
        )
