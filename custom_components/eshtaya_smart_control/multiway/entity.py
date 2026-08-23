"""Base entities for Eshtaya Multi-Way Control."""
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
    MODEL,
    SIGNAL_GROUPS_UPDATED,
    SIGNAL_RUNTIME_UPDATED,
    VERSION,
)


class MultiWayEntity(Entity):
    """Base class for a virtual multi-way group entity."""

    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, group_id: str, suffix: str) -> None:
        self.hass = hass
        self.group_id = group_id
        self._attr_unique_id = f"{group_id}_{suffix}"

    @property
    def _runtime_data(self) -> dict[str, Any]:
        return self.hass.data[DOMAIN][DATA_RUNTIME]

    @property
    def manager(self):
        return self._runtime_data["manager"]

    @property
    def store(self):
        return self._runtime_data["store"]

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
            identifiers={(DOMAIN, self.group_id)},
            name=group["name"],
            manufacturer=MANUFACTURER,
            model=MODEL,
            sw_version=VERSION,
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        group = self.group
        if group is None:
            return {}
        status = self.manager.status(self.group_id)
        return {
            "output": group["output"],
            "controllers": [c["entity_id"] for c in group["controllers"]],
            "controller_count": len(group["controllers"]),
            "health": status.get("health"),
            "last_source": status.get("last_source"),
            "last_transaction_id": status.get("last_transaction_id"),
        }

    def _still_expected(self, group: dict[str, Any] | None) -> bool:
        return group is not None

    async def async_added_to_hass(self) -> None:
        """Subscribe to runtime and group updates."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_RUNTIME_UPDATED, self._handle_runtime_update
            )
        )
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_GROUPS_UPDATED, self._handle_groups_update
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
