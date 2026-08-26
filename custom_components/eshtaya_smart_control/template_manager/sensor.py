"""Compatibility/diagnostic sensor for the integrated Template Manager."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DATA_TEMPLATE_MANAGER, SIGNAL_TEMPLATE_CHANGED


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    manager = hass.data["eshtaya_smart_control"][DATA_TEMPLATE_MANAGER]
    migration = manager.store.migration()
    # When legacy generated entities are still resident in memory, do not claim the
    # legacy sensor ID either. The next restart completes the exact-ID takeover.
    if migration.get("phase") == "restart_required":
        return
    async_add_entities([TemplateManagerSensor(manager)])


class TemplateManagerSensor(SensorEntity):
    """Expose the same data contract the old Lovelace card used."""

    _attr_should_poll = False
    _attr_name = "Eshtaya Template Manager"
    _attr_unique_id = "eshtaya_smart_control_template_manager"
    entity_id = "sensor.eshtaya_template_manager"
    _attr_icon = "mdi:swap-horizontal-bold"

    def __init__(self, manager) -> None:
        self.manager = manager

    @property
    def native_value(self):
        return self.manager.snapshot().get("managed_count", 0)

    @property
    def extra_state_attributes(self):
        return self.manager.snapshot()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_TEMPLATE_CHANGED, self._update)
        )

    @callback
    def _update(self) -> None:
        self.async_write_ha_state()
