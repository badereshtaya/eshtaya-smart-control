"""Diagnostic sensors for Eshtaya Multi-Way Control."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DATA_RUNTIME, DOMAIN, SIGNAL_GROUPS_UPDATED, SIGNAL_SMART_GROUPS_UPDATED
from .entity import MultiWayEntity
from .smart_entity import SmartGroupEntity
from .smart_native_group import async_setup_smart_native_platform


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up diagnostic sensors for both engines."""
    known_multi: set[str] = set()
    known_smart: set[str] = set()

    @callback
    def add_multi() -> None:
        store = hass.data[DOMAIN][DATA_RUNTIME]["store"]
        entities: list[SensorEntity] = []
        for group in store.groups():
            group_id = group["id"]
            if group_id in known_multi:
                continue
            known_multi.add(group_id)
            entities.extend(
                [
                    MultiWayHealthSensor(hass, group_id),
                    MultiWayLastSourceSensor(hass, group_id),
                    MultiWayLatencySensor(hass, group_id),
                ]
            )
        if entities:
            async_add_entities(entities)

    @callback
    def add_smart() -> None:
        store = hass.data[DOMAIN][DATA_RUNTIME]["smart_store"]
        entities: list[SensorEntity] = []
        for group in store.groups():
            group_id = group["id"]
            if group_id in known_smart:
                continue
            known_smart.add(group_id)
            entities.extend(
                [
                    SmartGroupHealthSensor(hass, group_id),
                    SmartGroupQualitySensor(hass, group_id),
                    SmartGroupLastSourceSensor(hass, group_id),
                    SmartGroupLatencySensor(hass, group_id),
                ]
            )
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
    await async_setup_smart_native_platform(hass, entry, async_add_entities, "sensor")


class _DiagnosticSensor(MultiWayEntity, SensorEntity):
    """Base diagnostic sensor for Multi-Way groups."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC


class MultiWayHealthSensor(_DiagnosticSensor):
    """Expose Multi-Way group health."""

    _attr_translation_key = "health"

    def __init__(self, hass: HomeAssistant, group_id: str) -> None:
        super().__init__(hass, group_id, "health")

    @property
    def native_value(self):
        """Return the health value."""
        return self.manager.status(self.group_id).get("health")


class MultiWayLastSourceSensor(_DiagnosticSensor):
    """Expose the last source that changed the group."""

    _attr_translation_key = "last_source"
    _attr_entity_registry_enabled_default = False

    def __init__(self, hass: HomeAssistant, group_id: str) -> None:
        super().__init__(hass, group_id, "last_source")

    @property
    def native_value(self):
        """Return the last source."""
        return self.manager.status(self.group_id).get("last_source") or "none"


class MultiWayLatencySensor(_DiagnosticSensor):
    """Expose the latest Multi-Way transaction latency."""

    _attr_translation_key = "last_latency"
    _attr_native_unit_of_measurement = UnitOfTime.MILLISECONDS
    _attr_entity_registry_enabled_default = False

    def __init__(self, hass: HomeAssistant, group_id: str) -> None:
        super().__init__(hass, group_id, "last_latency")

    @property
    def native_value(self):
        """Return the last transaction latency."""
        return self.manager.status(self.group_id).get("last_latency_ms")


class _SmartDiagnosticSensor(SmartGroupEntity, SensorEntity):
    """Base diagnostic sensor for Smart Groups."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC


class SmartGroupHealthSensor(_SmartDiagnosticSensor):
    """Expose Smart Group health."""

    _attr_translation_key = "smart_group_health"

    def __init__(self, hass: HomeAssistant, group_id: str) -> None:
        super().__init__(hass, group_id, "health")

    @property
    def native_value(self):
        """Return the Smart Group health."""
        return self.manager.status(self.group_id).get("health")


class SmartGroupQualitySensor(_SmartDiagnosticSensor):
    """Expose Smart Group quality metrics."""

    _attr_translation_key = "smart_group_quality"

    def __init__(self, hass: HomeAssistant, group_id: str) -> None:
        super().__init__(hass, group_id, "quality")

    @property
    def native_value(self):
        """Return the quality score."""
        return self.manager.status(self.group_id).get("quality_score")

    @property
    def extra_state_attributes(self):
        """Return quality detail attributes."""
        base = super().extra_state_attributes
        status = self.manager.status(self.group_id)
        base.update(
            {
                "response_class": status.get("response_class"),
                "average_member_latency_ms": status.get(
                    "average_member_latency_ms"
                ),
            }
        )
        return base


class SmartGroupLastSourceSensor(_SmartDiagnosticSensor):
    """Expose the last Smart Group source."""

    _attr_translation_key = "smart_group_last_source"
    _attr_entity_registry_enabled_default = False

    def __init__(self, hass: HomeAssistant, group_id: str) -> None:
        super().__init__(hass, group_id, "last_source")

    @property
    def native_value(self):
        """Return the last source."""
        return self.manager.status(self.group_id).get("last_source") or "none"


class SmartGroupLatencySensor(_SmartDiagnosticSensor):
    """Expose the latest Smart Group latency."""

    _attr_translation_key = "smart_group_latency"
    _attr_native_unit_of_measurement = UnitOfTime.MILLISECONDS
    _attr_entity_registry_enabled_default = False

    def __init__(self, hass: HomeAssistant, group_id: str) -> None:
        super().__init__(hass, group_id, "last_latency")

    @property
    def native_value(self):
        """Return the latest Smart Group latency."""
        return self.manager.status(self.group_id).get("last_latency_ms")
