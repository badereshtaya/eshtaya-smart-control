"""Domain-native Smart Group entities backed by Home Assistant's Group semantics."""
from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.group.binary_sensor import BinarySensorGroup
from homeassistant.components.group.button import ButtonGroup
from homeassistant.components.group.cover import CoverGroup
from homeassistant.components.group.event import EventGroup
from homeassistant.components.group.fan import FanGroup
from homeassistant.components.group.light import LightGroup
from homeassistant.components.group.lock import LockGroup
from homeassistant.components.group.media_player import MediaPlayerGroup
from homeassistant.components.group.notify import NotifyGroup
from homeassistant.components.group.sensor import SensorGroup
from homeassistant.components.group.switch import SwitchGroup
from homeassistant.components.group.valve import ValveGroup
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    DATA_RUNTIME,
    DOMAIN,
    MANUFACTURER,
    SIGNAL_SMART_GROUPS_UPDATED,
    SIGNAL_SMART_RUNTIME_UPDATED,
    SMART_KIND_VIRTUAL,
    SMART_MODEL,
    SMART_STATE_ALL,
    VERSION,
)


def _group_members(group: dict[str, Any]) -> list[str]:
    return [
        item["entity_id"]
        for item in group.get("members", [])
        if item.get("enabled", True)
    ]


def native_group_fingerprint(group: dict[str, Any]) -> tuple[Any, ...]:
    """Return the configuration fields that require entity recreation."""
    behavior = group.get("behavior") or {}
    return (
        group.get("name"),
        group.get("group_type") or group.get("virtual_type"),
        tuple((m.get("entity_id"), bool(m.get("enabled", True))) for m in group.get("members", [])),
        behavior.get("state_policy"),
        behavior.get("sensor_calc_type"),
        bool(behavior.get("ignore_non_numeric", False)),
        group.get("preferred_entity_id"),
    )


class SmartNativeMixin:
    """Attach Eshtaya metadata and lifecycle to a native Group entity class."""

    group_id: str
    smart_group_type: str

    def _eshtaya_init(self, hass: HomeAssistant, group_id: str, group_type: str) -> None:
        self.hass = hass
        self.group_id = group_id
        self.smart_group_type = group_type
        self._attr_unique_id = f"smart_{group_id}_control_{group_type}"
        group = self.group
        if group:
            self._attr_name = group["name"]
            preferred = group.get("preferred_entity_id")
            if preferred and "." in preferred:
                self._attr_suggested_object_id = preferred.split(".", 1)[1]

    @property
    def _runtime_data(self) -> dict[str, Any]:
        return self.hass.data[DOMAIN][DATA_RUNTIME]

    @property
    def manager(self):
        return self._runtime_data["smart_manager"]

    @property
    def store(self):
        return self._runtime_data["smart_store"]

    @property
    def group(self) -> dict[str, Any] | None:
        return self.store.get(self.group_id)

    @property
    def device_info(self) -> DeviceInfo | None:
        group = self.group
        if group is None:
            return None
        return DeviceInfo(
            identifiers={(DOMAIN, f"smart_{self.group_id}")},
            name=group["name"],
            manufacturer=MANUFACTURER,
            model=f"{SMART_MODEL} · {self.smart_group_type}",
            sw_version=VERSION,
        )

    @property
    def available(self) -> bool:
        group = self.group
        if not group or not group.get("enabled", True) or group.get("maintenance"):
            return False
        try:
            return bool(super().available)
        except (AttributeError, TypeError):
            return True

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        try:
            base = dict(super().extra_state_attributes or {})
        except (AttributeError, TypeError):
            base = {}
        group = self.group
        if not group:
            return base
        status = self.manager.status(self.group_id)
        base.update(
            {
                "smart_group_id": self.group_id,
                "group_type": self.smart_group_type,
                "kind": group.get("kind"),
                "members": _group_members(group),
                "member_count": len(_group_members(group)),
                "health": status.get("health"),
                "quality_score": status.get("quality_score"),
                "last_source": status.get("last_source"),
                "last_latency_ms": status.get("last_latency_ms"),
                "maintenance": bool(group.get("maintenance")),
                "locked": bool(group.get("locked")),
                "takeover_managed": bool((group.get("migration") or {}).get("takeover")),
            }
        )
        return base

    def _eshtaya_register_runtime_listener(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_SMART_RUNTIME_UPDATED, self._eshtaya_runtime_updated
            )
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._eshtaya_register_runtime_listener()

    @callback
    def _eshtaya_runtime_updated(self, group_id: str) -> None:
        if group_id == self.group_id:
            self.async_write_ha_state()


class EshtayaLightGroup(SmartNativeMixin, LightGroup):
    def __init__(self, hass: HomeAssistant, group_id: str, group: dict[str, Any]) -> None:
        LightGroup.__init__(
            self,
            f"smart_{group_id}_control_light",
            group["name"],
            _group_members(group),
            (group.get("behavior") or {}).get("state_policy") == SMART_STATE_ALL,
        )
        self._eshtaya_init(hass, group_id, "light")


class EshtayaSwitchGroup(SmartNativeMixin, SwitchGroup):
    def __init__(self, hass: HomeAssistant, group_id: str, group: dict[str, Any]) -> None:
        SwitchGroup.__init__(
            self,
            f"smart_{group_id}_control_switch",
            group["name"],
            _group_members(group),
            (group.get("behavior") or {}).get("state_policy") == SMART_STATE_ALL,
        )
        self._eshtaya_init(hass, group_id, "switch")


class EshtayaFanGroup(SmartNativeMixin, FanGroup):
    def __init__(self, hass: HomeAssistant, group_id: str, group: dict[str, Any]) -> None:
        FanGroup.__init__(self, f"smart_{group_id}_control_fan", group["name"], _group_members(group))
        self._eshtaya_init(hass, group_id, "fan")


class EshtayaCoverGroup(SmartNativeMixin, CoverGroup):
    def __init__(self, hass: HomeAssistant, group_id: str, group: dict[str, Any]) -> None:
        CoverGroup.__init__(self, f"smart_{group_id}_control_cover", group["name"], _group_members(group))
        self._eshtaya_init(hass, group_id, "cover")


class EshtayaLockGroup(SmartNativeMixin, LockGroup):
    def __init__(self, hass: HomeAssistant, group_id: str, group: dict[str, Any]) -> None:
        LockGroup.__init__(self, f"smart_{group_id}_control_lock", group["name"], _group_members(group))
        self._eshtaya_init(hass, group_id, "lock")


class EshtayaMediaPlayerGroup(SmartNativeMixin, MediaPlayerGroup):
    def __init__(self, hass: HomeAssistant, group_id: str, group: dict[str, Any]) -> None:
        MediaPlayerGroup.__init__(
            self,
            f"smart_{group_id}_control_media_player",
            group["name"],
            _group_members(group),
        )
        self._eshtaya_init(hass, group_id, "media_player")

    async def async_added_to_hass(self) -> None:
        """Register native media listeners with dynamic-entity cleanup support."""
        for entity_id in self._entities:
            self.async_update_supported_features(entity_id, self.hass.states.get(entity_id))
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, self._entities, self.async_on_state_change
            )
        )
        self.async_update_group_state()
        self.async_write_ha_state()
        self._eshtaya_register_runtime_listener()


class EshtayaValveGroup(SmartNativeMixin, ValveGroup):
    def __init__(self, hass: HomeAssistant, group_id: str, group: dict[str, Any]) -> None:
        ValveGroup.__init__(self, f"smart_{group_id}_control_valve", group["name"], _group_members(group))
        self._eshtaya_init(hass, group_id, "valve")


class EshtayaButtonGroup(SmartNativeMixin, ButtonGroup):
    def __init__(self, hass: HomeAssistant, group_id: str, group: dict[str, Any]) -> None:
        ButtonGroup.__init__(self, f"smart_{group_id}_control_button", group["name"], _group_members(group))
        self._eshtaya_init(hass, group_id, "button")


class EshtayaNotifyGroup(SmartNativeMixin, NotifyGroup):
    def __init__(self, hass: HomeAssistant, group_id: str, group: dict[str, Any]) -> None:
        NotifyGroup.__init__(self, f"smart_{group_id}_control_notify", group["name"], _group_members(group))
        self._eshtaya_init(hass, group_id, "notify")


class EshtayaEventGroup(SmartNativeMixin, EventGroup):
    def __init__(self, hass: HomeAssistant, group_id: str, group: dict[str, Any]) -> None:
        EventGroup.__init__(self, f"smart_{group_id}_control_event", group["name"], _group_members(group))
        self._eshtaya_init(hass, group_id, "event")


class EshtayaBinarySensorGroup(SmartNativeMixin, BinarySensorGroup):
    def __init__(self, hass: HomeAssistant, group_id: str, group: dict[str, Any]) -> None:
        members = _group_members(group)
        device_class = None
        for entity_id in members:
            state = hass.states.get(entity_id)
            raw = state.attributes.get("device_class") if state else None
            if raw:
                try:
                    device_class = BinarySensorDeviceClass(raw)
                except ValueError:
                    device_class = None
                break
        BinarySensorGroup.__init__(
            self,
            f"smart_{group_id}_control_binary_sensor",
            group["name"],
            device_class,
            members,
            (group.get("behavior") or {}).get("state_policy") == SMART_STATE_ALL,
        )
        self._eshtaya_init(hass, group_id, "binary_sensor")


class EshtayaSensorGroup(SmartNativeMixin, SensorGroup):
    def __init__(self, hass: HomeAssistant, group_id: str, group: dict[str, Any]) -> None:
        behavior = group.get("behavior") or {}
        SensorGroup.__init__(
            self,
            hass,
            f"smart_{group_id}_control_sensor",
            group["name"],
            _group_members(group),
            bool(behavior.get("ignore_non_numeric", False)),
            str(behavior.get("sensor_calc_type") or "mean"),
            None,
            None,
            None,
        )
        self._eshtaya_init(hass, group_id, "sensor")


FACTORIES: dict[str, Callable[[HomeAssistant, str, dict[str, Any]], Any]] = {
    "binary_sensor": EshtayaBinarySensorGroup,
    "button": EshtayaButtonGroup,
    "cover": EshtayaCoverGroup,
    "event": EshtayaEventGroup,
    "fan": EshtayaFanGroup,
    "light": EshtayaLightGroup,
    "lock": EshtayaLockGroup,
    "media_player": EshtayaMediaPlayerGroup,
    "notify": EshtayaNotifyGroup,
    "sensor": EshtayaSensorGroup,
    "switch": EshtayaSwitchGroup,
    "valve": EshtayaValveGroup,
}


async def async_setup_smart_native_platform(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
    group_type: str,
) -> None:
    """Dynamically keep domain-native Smart Group control entities in sync."""
    current: dict[str, tuple[Any, tuple[Any, ...]]] = {}
    reconcile_lock = asyncio.Lock()

    async def async_reconcile() -> None:
        async with reconcile_lock:
            store = hass.data[DOMAIN][DATA_RUNTIME]["smart_store"]
            desired = {
                group["id"]: group
                for group in store.groups()
                if group.get("kind") == SMART_KIND_VIRTUAL
                and (group.get("group_type") or group.get("virtual_type")) == group_type
            }

            for group_id, (entity, fingerprint) in list(current.items()):
                group = desired.get(group_id)
                if group is None or native_group_fingerprint(group) != fingerprint:
                    try:
                        await entity.async_remove()
                    except Exception:  # noqa: BLE001
                        pass
                    current.pop(group_id, None)

            new_entities = []
            factory = FACTORIES[group_type]
            for group_id, group in desired.items():
                if group_id in current:
                    continue
                entity = factory(hass, group_id, group)
                current[group_id] = (entity, native_group_fingerprint(group))
                new_entities.append(entity)
            if new_entities:
                async_add_entities(new_entities)

    @callback
    def schedule_reconcile() -> None:
        hass.async_create_task(async_reconcile())

    await async_reconcile()
    entry.async_on_unload(
        async_dispatcher_connect(hass, SIGNAL_SMART_GROUPS_UPDATED, schedule_reconcile)
    )
