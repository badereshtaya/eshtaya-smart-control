"""Switch platform for Eshtaya Multi-Way Control."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DATA_RUNTIME, DOMAIN, SIGNAL_GROUPS_UPDATED, SIGNAL_SMART_GROUPS_UPDATED, VIRTUAL_SWITCH
from .entity import MultiWayEntity
from .smart_entity import SmartGroupEntity
from .smart_native_group import async_setup_smart_native_platform


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up switches for both engines plus native Smart switch groups."""
    known_control: set[str] = set()
    known_enabled: set[str] = set()
    known_smart_enabled: set[str] = set()

    @callback
    def add_multi() -> None:
        store = hass.data[DOMAIN][DATA_RUNTIME]["store"]
        entities: list[SwitchEntity] = []
        for group in store.groups():
            group_id = group["id"]
            if group_id not in known_enabled:
                known_enabled.add(group_id)
                entities.append(MultiWayEnabledSwitch(hass, group_id))
            if group["virtual_type"] == VIRTUAL_SWITCH and group_id not in known_control:
                known_control.add(group_id)
                entities.append(MultiWayVirtualSwitch(hass, group_id))
        if entities:
            async_add_entities(entities)

    @callback
    def add_smart_enabled() -> None:
        store = hass.data[DOMAIN][DATA_RUNTIME]["smart_store"]
        entities: list[SwitchEntity] = []
        for group in store.groups():
            group_id = group["id"]
            if group_id not in known_smart_enabled:
                known_smart_enabled.add(group_id)
                entities.append(SmartGroupEnabledSwitch(hass, group_id))
        if entities:
            async_add_entities(entities)

    add_multi()
    add_smart_enabled()
    entry.async_on_unload(async_dispatcher_connect(hass, SIGNAL_GROUPS_UPDATED, add_multi))
    entry.async_on_unload(async_dispatcher_connect(hass, SIGNAL_SMART_GROUPS_UPDATED, add_smart_enabled))
    await async_setup_smart_native_platform(hass, entry, async_add_entities, "switch")


class MultiWayVirtualSwitch(MultiWayEntity, SwitchEntity):
    """Virtual switch representing a Multi-Way group."""

    _attr_translation_key = "group_control"

    def __init__(self, hass: HomeAssistant, group_id: str) -> None:
        super().__init__(hass, group_id, "control_switch")

    def _still_expected(self, group) -> bool:
        return group is not None and group["virtual_type"] == VIRTUAL_SWITCH

    @property
    def is_on(self) -> bool | None:
        """Return the desired group state."""
        state = self.manager.status(self.group_id).get("desired_state")
        return True if state == "on" else False if state == "off" else None

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the group on."""
        await self.manager.async_request_state(
            self.group_id,
            "on",
            source=self.entity_id or "virtual_switch",
            origin="virtual_entity",
        )

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the group off."""
        await self.manager.async_request_state(
            self.group_id,
            "off",
            source=self.entity_id or "virtual_switch",
            origin="virtual_entity",
        )


class MultiWayEnabledSwitch(MultiWayEntity, SwitchEntity):
    """Enable or disable a Multi-Way group."""

    _attr_translation_key = "group_enabled"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, hass: HomeAssistant, group_id: str) -> None:
        super().__init__(hass, group_id, "enabled")

    @property
    def is_on(self) -> bool:
        """Return whether the group is enabled."""
        group = self.group
        return bool(group and group.get("enabled", True))

    async def async_turn_on(self, **kwargs) -> None:
        """Enable the group."""
        await self.manager.async_set_enabled(self.group_id, True)

    async def async_turn_off(self, **kwargs) -> None:
        """Disable the group."""
        await self.manager.async_set_enabled(self.group_id, False)


class SmartGroupEnabledSwitch(SmartGroupEntity, SwitchEntity):
    """Enable or disable a Smart Group."""

    _attr_translation_key = "smart_group_enabled"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, hass: HomeAssistant, group_id: str) -> None:
        super().__init__(hass, group_id, "enabled")

    @property
    def is_on(self) -> bool:
        """Return whether the Smart Group is enabled."""
        group = self.group
        return bool(group and group.get("enabled", True))

    async def async_turn_on(self, **kwargs) -> None:
        """Enable the Smart Group."""
        await self.manager.async_set_enabled(self.group_id, True)

    async def async_turn_off(self, **kwargs) -> None:
        """Disable the Smart Group."""
        await self.manager.async_set_enabled(self.group_id, False)

