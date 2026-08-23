"""Base entities for Eshtaya Smart Groups."""
from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity

from .const import (
    DATA_RUNTIME,
    DOMAIN,
    MANUFACTURER,
    SIGNAL_SMART_GROUPS_UPDATED,
    SIGNAL_SMART_RUNTIME_UPDATED,
    SMART_MODEL,
    VERSION,
)


class SmartGroupEntity(Entity):
    """Base class for a Smart Group entity."""

    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, group_id: str, suffix: str) -> None:
        self.hass = hass
        self.group_id = group_id
        self._attr_unique_id = f"smart_{group_id}_{suffix}"
        group = hass.data.get(DOMAIN, {}).get(DATA_RUNTIME, {}).get("smart_store")
        group = group.get(group_id) if group else None
        if suffix in {"control_light", "control_switch"}:
            # The control entity is the group itself, so keep its visible name clean.
            self._attr_translation_key = None
            self._attr_name = None
            preferred = group.get("preferred_entity_id") if group else None
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
    def available(self) -> bool:
        return self.group is not None

    @property
    def device_info(self) -> DeviceInfo | None:
        group = self.group
        if group is None:
            return None
        return DeviceInfo(
            identifiers={(DOMAIN, f"smart_{self.group_id}")},
            name=group["name"],
            manufacturer=MANUFACTURER,
            model=SMART_MODEL,
            sw_version=VERSION,
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        group = self.group
        if group is None:
            return {}
        status = self.manager.status(self.group_id)
        return {
            "smart_group_id": self.group_id,
            "kind": group.get("kind"),
            "group_type": group.get("group_type") or group.get("virtual_type"),
            "controller": group.get("controller_entity"),
            "members": [m["entity_id"] for m in group.get("members", [])],
            "member_count": len(group.get("members", [])),
            "state_policy": group.get("behavior", {}).get("state_policy"),
            "direction": group.get("behavior", {}).get("direction"),
            "performance_mode": group.get("behavior", {}).get("performance_mode"),
            "health": status.get("health"),
            "quality_score": status.get("quality_score"),
            "response_class": status.get("response_class"),
            "last_source": status.get("last_source"),
            "last_latency_ms": status.get("last_latency_ms"),
            "average_member_latency_ms": status.get("average_member_latency_ms"),
            "quarantined": status.get("quarantined", []),
            "maintenance": bool(group.get("maintenance")),
            "locked": bool(group.get("locked")),
            "hide_members": bool(group.get("hide_members")),
            "preferred_entity_id": group.get("preferred_entity_id"),
            "takeover_managed": bool((group.get("migration") or {}).get("takeover")),
            "action_execution": group.get("behavior", {}).get("action_execution"),
            "automation_skip_condition": group.get("behavior", {}).get("automation_skip_condition"),
        }

    def _still_expected(self, group: dict[str, Any] | None) -> bool:
        return group is not None

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_SMART_RUNTIME_UPDATED, self._handle_runtime_update
            )
        )
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_SMART_GROUPS_UPDATED, self._handle_groups_update
            )
        )

    @callback
    def _handle_runtime_update(self, group_id: str) -> None:
        if group_id == self.group_id:
            self.async_write_ha_state()

    @callback
    def _handle_groups_update(self) -> None:
        group = self.group
        if not self._still_expected(group):
            self.hass.async_create_task(self.async_remove())
            return
        self.async_write_ha_state()
