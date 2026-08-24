"""Unified light platform for Multi-Way and Template Manager."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .multiway.light import async_setup_entry as async_setup_multiway_light
from .template_manager.light import async_setup_entry as async_setup_template_light


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    await async_setup_multiway_light(hass, entry, async_add_entities)
    await async_setup_template_light(hass, entry, async_add_entities)
