"""Light platform for Eshtaya Multi-Way Control."""
from __future__ import annotations

from homeassistant.components.light import LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DATA_RUNTIME, DOMAIN, SIGNAL_GROUPS_UPDATED, VIRTUAL_LIGHT
from .entity import MultiWayEntity
from .smart_native_group import async_setup_smart_native_platform


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Multi-Way and domain-native Smart Group light entities."""
    known_multi: set[str] = set()

    @callback
    def add_multi() -> None:
        store = hass.data[DOMAIN][DATA_RUNTIME]["store"]
        entities = []
        for group in store.groups():
            if group["virtual_type"] == VIRTUAL_LIGHT and group["id"] not in known_multi:
                known_multi.add(group["id"])
                entities.append(MultiWayVirtualLight(hass, group["id"]))
        if entities:
            async_add_entities(entities)

    add_multi()
    entry.async_on_unload(async_dispatcher_connect(hass, SIGNAL_GROUPS_UPDATED, add_multi))
    await async_setup_smart_native_platform(hass, entry, async_add_entities, "light")


class MultiWayVirtualLight(MultiWayEntity, LightEntity):
    _attr_translation_key = "group_control"

    def __init__(self, hass: HomeAssistant, group_id: str) -> None:
        super().__init__(hass, group_id, "control_light")

    def _still_expected(self, group) -> bool:
        return group is not None and group["virtual_type"] == VIRTUAL_LIGHT

    @property
    def is_on(self) -> bool | None:
        state = self.manager.status(self.group_id).get("desired_state")
        return True if state == "on" else False if state == "off" else None

    async def async_turn_on(self, **kwargs) -> None:
        await self.manager.async_request_state(
            self.group_id,
            "on",
            source=self.entity_id or "virtual_light",
            origin="virtual_entity",
        )

    async def async_turn_off(self, **kwargs) -> None:
        await self.manager.async_request_state(
            self.group_id,
            "off",
            source=self.entity_id or "virtual_light",
            origin="virtual_entity",
        )

