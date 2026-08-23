"""Eshtaya Smart Control unified Home Assistant platform."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_registry as er

from .const import DATA_ENTITY_MANAGER, DATA_ENTRY, DATA_TUYA_MANAGER, DOMAIN
from .entity_control.manager_unified import UnifiedEntityManager
from .entity_control.websocket_v12 import async_register_websocket_commands as async_register_entity_ws
from .multiway import async_remove_entry as async_remove_multiway_entry
from .multiway import async_setup as async_setup_multiway
from .multiway import async_setup_entry as async_setup_multiway_entry
from .multiway import async_unload_entry as async_unload_multiway_entry
from .panel import async_register_panel, async_remove_panel
from .tuya.manager import TuyaManager
from .tuya.websocket import async_register_websocket_commands as async_register_tuya_ws
from .websocket import async_register_websocket_commands as async_register_core_ws

_LOGGER = logging.getLogger(__name__)
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    hass.data.setdefault(DOMAIN, {})
    await async_setup_multiway(hass, config)
    async_register_entity_ws(hass)
    async_register_tuya_ws(hass)
    async_register_core_ws(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = hass.data.setdefault(DOMAIN, {})
    data[DATA_ENTRY] = entry

    entity_manager = UnifiedEntityManager(hass)
    await entity_manager.async_initialize()
    data[DATA_ENTITY_MANAGER] = entity_manager
    data[DATA_TUYA_MANAGER] = TuyaManager(hass, entry)

    if not await async_setup_multiway_entry(hass, entry):
        return False

    await async_register_panel(hass)

    async def _entity_registry_changed(event) -> None:
        try:
            await entity_manager.async_handle_registry_event(dict(event.data))
        except Exception:  # keep Home Assistant alive if file I/O fails
            _LOGGER.exception("Entity Control failed after entity registry update")

    entry.async_on_unload(
        hass.bus.async_listen(er.EVENT_ENTITY_REGISTRY_UPDATED, _entity_registry_changed)
    )
    entry.async_on_unload(entry.add_update_listener(_entry_updated))
    return True


async def _entry_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    manager = hass.data.get(DOMAIN, {}).get(DATA_TUYA_MANAGER)
    if manager:
        manager._reload_config()  # internal synchronized config refresh


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    async_remove_panel(hass)
    ok = await async_unload_multiway_entry(hass, entry)
    if ok:
        hass.data.pop(DOMAIN, None)
    return ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await async_remove_multiway_entry(hass, entry)
