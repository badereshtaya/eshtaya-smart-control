"""media_player Smart Group platform for Eshtaya Multi-Way Control."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .smart_native_group import async_setup_smart_native_platform


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up domain-native media_player Smart Groups."""
    await async_setup_smart_native_platform(hass, entry, async_add_entities, "media_player")
