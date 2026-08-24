"""Unified sensor platform for Multi-Way and Template Manager."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .multiway.sensor import async_setup_entry as async_setup_multiway_sensor
from .template_manager.sensor import async_setup_entry as async_setup_template_sensor


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    await async_setup_multiway_sensor(hass, entry, async_add_entities)
    await async_setup_template_sensor(hass, entry, async_add_entities)
