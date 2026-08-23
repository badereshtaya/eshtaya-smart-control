"""Eshtaya Multi-Way Control integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.typing import ConfigType

from .const import (
    DATA_RUNTIME,
    DOMAIN,
    SERVICE_DISABLE_GROUP,
    SERVICE_ENABLE_GROUP,
    SERVICE_SET_STATE,
    SERVICE_SYNC_ALL,
    SERVICE_SYNC_GROUP,
    SERVICE_TEST_GROUP,
    SERVICE_SMART_RUN,
    SERVICE_SMART_SET_STATE,
    SERVICE_SMART_SYNC,
    SERVICE_SMART_TEST,
)
from .manager import MultiWayManager
from .smart_group_manager import SmartGroupManager
from .smart_storage import SmartGroupStore
from .storage import MultiWayStore
from .websocket import async_register_websocket_commands

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


PLATFORMS: list[Platform] = [
    Platform.LIGHT,
    Platform.SWITCH,
    Platform.FAN,
    Platform.COVER,
    Platform.LOCK,
    Platform.MEDIA_PLAYER,
    Platform.VALVE,
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.BUTTON,
    Platform.EVENT,
    Platform.NOTIFY,
]

GROUP_SCHEMA = vol.Schema({vol.Required("group_id"): str})
STATE_SCHEMA = vol.Schema(
    {vol.Required("group_id"): str, vol.Required("state"): vol.In(["on", "off"])}
)


def _get_runtime(hass: HomeAssistant) -> dict[str, Any]:
    runtime = hass.data.get(DOMAIN, {}).get(DATA_RUNTIME)
    if not runtime:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="not_loaded",
        )
    return runtime


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up shared API, panel assets, and service actions."""
    hass.data.setdefault(DOMAIN, {})
    async_register_websocket_commands(hass)

    async def sync_group(call: ServiceCall) -> None:
        runtime = _get_runtime(hass)
        try:
            await runtime["manager"].async_sync_group(call.data["group_id"])
        except ValueError as err:
            raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="group_error",
            translation_placeholders={"error": str(err)},
        ) from err

    async def sync_all(_call: ServiceCall) -> None:
        runtime = _get_runtime(hass)
        await runtime["manager"].async_sync_all()

    async def enable_group(call: ServiceCall) -> None:
        runtime = _get_runtime(hass)
        try:
            await runtime["manager"].async_set_enabled(call.data["group_id"], True)
        except ValueError as err:
            raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="group_error",
            translation_placeholders={"error": str(err)},
        ) from err

    async def disable_group(call: ServiceCall) -> None:
        runtime = _get_runtime(hass)
        try:
            await runtime["manager"].async_set_enabled(call.data["group_id"], False)
        except ValueError as err:
            raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="group_error",
            translation_placeholders={"error": str(err)},
        ) from err

    async def set_group_state(call: ServiceCall) -> None:
        runtime = _get_runtime(hass)
        try:
            await runtime["manager"].async_request_state(
                call.data["group_id"],
                call.data["state"],
                source="service_action",
                origin="service_action",
            )
        except ValueError as err:
            raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="group_error",
            translation_placeholders={"error": str(err)},
        ) from err

    async def test_group(call: ServiceCall) -> dict[str, Any]:
        runtime = _get_runtime(hass)
        try:
            return runtime["manager"].test_group(call.data["group_id"])
        except ValueError as err:
            raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="group_error",
            translation_placeholders={"error": str(err)},
        ) from err

    hass.services.async_register(DOMAIN, SERVICE_SYNC_GROUP, sync_group, schema=GROUP_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SYNC_ALL, sync_all)
    hass.services.async_register(DOMAIN, SERVICE_ENABLE_GROUP, enable_group, schema=GROUP_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_DISABLE_GROUP, disable_group, schema=GROUP_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SET_STATE, set_group_state, schema=STATE_SCHEMA)
    hass.services.async_register(
        DOMAIN,
        SERVICE_TEST_GROUP,
        test_group,
        schema=GROUP_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )

    async def smart_set_state(call: ServiceCall) -> None:
        runtime = _get_runtime(hass)
        try:
            await runtime["smart_manager"].async_set_state(
                call.data["group_id"], call.data["state"], source="service_action", origin="service"
            )
        except ValueError as err:
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="group_error",
                translation_placeholders={"error": str(err)},
            ) from err

    async def smart_sync(call: ServiceCall) -> None:
        runtime = _get_runtime(hass)
        try:
            await runtime["smart_manager"].async_sync(call.data["group_id"])
        except ValueError as err:
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="group_error",
                translation_placeholders={"error": str(err)},
            ) from err


    async def smart_run(call: ServiceCall) -> None:
        runtime = _get_runtime(hass)
        try:
            await runtime["smart_manager"].async_run_action_group(
                call.data["group_id"], source="service_action", origin="service"
            )
        except ValueError as err:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="group_error",
                translation_placeholders={"error": str(err)},
            ) from err

    async def smart_test(call: ServiceCall) -> dict[str, Any]:
        runtime = _get_runtime(hass)
        try:
            return runtime["smart_manager"].test_group(call.data["group_id"])
        except ValueError as err:
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="group_error",
                translation_placeholders={"error": str(err)},
            ) from err

    hass.services.async_register(DOMAIN, SERVICE_SMART_SET_STATE, smart_set_state, schema=STATE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SMART_RUN, smart_run, schema=GROUP_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SMART_SYNC, smart_sync, schema=GROUP_SCHEMA)
    hass.services.async_register(
        DOMAIN, SERVICE_SMART_TEST, smart_test, schema=GROUP_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the single config entry."""
    store = MultiWayStore(hass)
    smart_store = SmartGroupStore(hass)
    await store.async_load()
    await smart_store.async_load()
    manager = MultiWayManager(hass, store)
    smart_manager = SmartGroupManager(hass, smart_store)
    hass.data.setdefault(DOMAIN, {})[DATA_RUNTIME] = {
        "entry_id": entry.entry_id,
        "store": store,
        "manager": manager,
        "smart_store": smart_store,
        "smart_manager": smart_manager,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await manager.async_start()
    await smart_manager.async_start()
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload cleanly, including listeners, timers, entities, and panel."""
    runtime = hass.data.get(DOMAIN, {}).get(DATA_RUNTIME)
    if runtime:
        await runtime["manager"].async_stop()
        await runtime["smart_manager"].async_stop()
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.get(DOMAIN, {}).pop(DATA_RUNTIME, None)
    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Delete persistent data and stale repair issues when the entry is removed."""
    store = MultiWayStore(hass)
    smart_store = SmartGroupStore(hass)
    await smart_store.async_load()
    entity_registry = er.async_get(hass)
    for entity_id in smart_store.hidden_members_owned():
        entity_entry = entity_registry.async_get(entity_id)
        if entity_entry and entity_entry.hidden_by == er.RegistryEntryHider.INTEGRATION:
            entity_registry.async_update_entity(entity_id, hidden_by=None)
    await store.async_remove()
    await smart_store.async_remove()

    registry = ir.async_get(hass)
    for domain, issue_id in list(registry.issues):
        if domain == DOMAIN:
            registry.async_delete(DOMAIN, issue_id)
