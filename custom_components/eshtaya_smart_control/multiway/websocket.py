"""WebSocket management API for Eshtaya Multi-Way Control."""
from __future__ import annotations

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er

from .native_group_migration import async_take_over_group, native_group_entries

from .const import (
    DATA_RUNTIME,
    DOMAIN,
    MODE_EVENT,
    MODE_FOLLOW,
    MODE_MIRROR,
    MODE_MOMENTARY_OFF,
    MODE_MOMENTARY_ON,
    MODE_TOGGLE,
    VIRTUAL_LIGHT,
    VIRTUAL_SWITCH,
    VERSION,
    SMART_ACTION_TYPES,
    SMART_GROUP_TYPES,
    SMART_KIND_VIRTUAL,
    SMART_KINDS,
    SMART_MEMBER_DOMAINS,
)

CONTROLLER_SCHEMA = vol.Schema(
    {
        vol.Required("entity_id"): str,
        vol.Optional("mode", default=MODE_MIRROR): vol.In(
            [
                MODE_MIRROR,
                MODE_TOGGLE,
                MODE_MOMENTARY_ON,
                MODE_MOMENTARY_OFF,
                MODE_EVENT,
                MODE_FOLLOW,
            ]
        ),
        vol.Optional("invert", default=False): bool,
        vol.Optional("reflect_state"): bool,
    },
    extra=vol.PREVENT_EXTRA,
)

GROUP_FIELDS = {
    vol.Required("name"): vol.All(str, vol.Length(min=1, max=100)),
    vol.Required("output"): str,
    vol.Required("controllers"): vol.All([CONTROLLER_SCHEMA], vol.Length(min=1)),
    vol.Optional("enabled", default=True): bool,
    vol.Optional("virtual_type", default=VIRTUAL_LIGHT): vol.In(
        [VIRTUAL_LIGHT, VIRTUAL_SWITCH]
    ),
    vol.Optional("area_id", default=None): vol.Any(None, str),
    vol.Optional("behavior", default={}): dict,
}


def _runtime_all(hass: HomeAssistant):
    data = hass.data.get(DOMAIN, {}).get(DATA_RUNTIME)
    if not data:
        raise ValueError("Eshtaya Multi-Way Control is not loaded")
    return data


def _runtime(hass: HomeAssistant):
    data = _runtime_all(hass)
    return data["store"], data["manager"]


def _ensure_config_unlocked(hass: HomeAssistant) -> None:
    data = _runtime_all(hass)
    if data["smart_store"].settings().get("config_locked"):
        raise ValueError("Configuration is locked. Unlock it from Settings first")


def async_register_websocket_commands(hass: HomeAssistant) -> None:
    """Register the panel API."""
    for command in (
        ws_list,
        ws_create,
        ws_update,
        ws_delete,
        ws_set_enabled,
        ws_sync,
        ws_sync_all,
        ws_activity,
        ws_get_settings,
        ws_update_settings,
        ws_export,
        ws_import,
        ws_test,
        ws_test_entity_action,
        ws_rapid_toggle_test,
        ws_learn_start,
        ws_learn_status,
        ws_learn_cancel,
        ws_smart_list,
        ws_smart_create,
        ws_smart_update,
        ws_smart_delete,
        ws_smart_clone,
        ws_smart_set_state,
        ws_smart_action,
        ws_smart_set_enabled,
        ws_smart_sync,
        ws_smart_test,
        ws_smart_test_all,
        ws_smart_quarantine,
        ws_smart_settings,
        ws_smart_template_save,
        ws_smart_template_delete,
        ws_smart_undo,
        ws_smart_diagnostics,
        ws_smart_ha_groups,
        ws_smart_import_ha_group,
        ws_smart_takeover_ha_group,
        ws_smart_refresh_ha_group,
        ws_full_export,
        ws_full_import,
        ws_repair_missing,
        ws_repair_remap,
        ws_multiway_undo,
    ):
        websocket_api.async_register_command(hass, command)


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/multiway/list"})
@callback
def ws_list(hass, connection, msg) -> None:
    """List groups with current runtime state."""
    try:
        store, manager = _runtime(hass)
        result = []
        for group in store.groups():
            item = dict(group)
            item["runtime"] = manager.status(group["id"])
            result.append(item)
        connection.send_result(
            msg["id"],
            {
                "version": VERSION,
                "groups": result,
                "summary": manager.summary(),
                "settings": store.settings(),
            },
        )
    except Exception as err:  # noqa: BLE001
        connection.send_error(msg["id"], "list_failed", str(err))


@websocket_api.require_admin
@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/multiway/create", **GROUP_FIELDS}
)
@websocket_api.async_response
async def ws_create(hass, connection, msg) -> None:
    """Create a group."""
    try:
        _ensure_config_unlocked(hass)
        store, manager = _runtime(hass)
        payload = {key: value for key, value in msg.items() if key not in {"id", "type"}}
        group = await store.async_create(payload)
        await manager.async_reload(reconcile=True)
        connection.send_result(msg["id"], group)
    except Exception as err:  # noqa: BLE001
        connection.send_error(msg["id"], "create_failed", str(err))


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/multiway/update",
        vol.Required("group_id"): str,
        **GROUP_FIELDS,
    }
)
@websocket_api.async_response
async def ws_update(hass, connection, msg) -> None:
    """Update a group."""
    try:
        _ensure_config_unlocked(hass)
        store, manager = _runtime(hass)
        old = store.get(msg["group_id"])
        payload = {
            key: value
            for key, value in msg.items()
            if key not in {"id", "type", "group_id"}
        }
        group = await store.async_update(msg["group_id"], payload)
        if old and old["virtual_type"] != group["virtual_type"]:
            _remove_virtual_registry_entity(hass, group["id"], old["virtual_type"])
        await manager.async_reload(reconcile=True)
        connection.send_result(msg["id"], group)
    except Exception as err:  # noqa: BLE001
        connection.send_error(msg["id"], "update_failed", str(err))


@websocket_api.require_admin
@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/multiway/delete", vol.Required("group_id"): str}
)
@websocket_api.async_response
async def ws_delete(hass, connection, msg) -> None:
    """Delete a group and its virtual entity registry entries."""
    try:
        _ensure_config_unlocked(hass)
        store, manager = _runtime(hass)
        await store.async_delete(msg["group_id"])
        _remove_group_registry_entities(hass, msg["group_id"])
        await manager.async_reload(reconcile=False)
        connection.send_result(msg["id"], {"ok": True})
    except Exception as err:  # noqa: BLE001
        connection.send_error(msg["id"], "delete_failed", str(err))


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/multiway/set_enabled",
        vol.Required("group_id"): str,
        vol.Required("enabled"): bool,
    }
)
@websocket_api.async_response
async def ws_set_enabled(hass, connection, msg) -> None:
    try:
        _, manager = _runtime(hass)
        group = await manager.async_set_enabled(msg["group_id"], msg["enabled"])
        connection.send_result(msg["id"], group)
    except Exception as err:  # noqa: BLE001
        connection.send_error(msg["id"], "enable_failed", str(err))


@websocket_api.require_admin
@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/multiway/sync", vol.Required("group_id"): str}
)
@websocket_api.async_response
async def ws_sync(hass, connection, msg) -> None:
    try:
        _, manager = _runtime(hass)
        ok = await manager.async_sync_group(msg["group_id"])
        connection.send_result(msg["id"], {"ok": ok})
    except Exception as err:  # noqa: BLE001
        connection.send_error(msg["id"], "sync_failed", str(err))


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/multiway/sync_all"})
@websocket_api.async_response
async def ws_sync_all(hass, connection, msg) -> None:
    try:
        _, manager = _runtime(hass)
        result = await manager.async_sync_all()
        connection.send_result(msg["id"], result)
    except Exception as err:  # noqa: BLE001
        connection.send_error(msg["id"], "sync_all_failed", str(err))


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/multiway/activity",
        vol.Optional("limit", default=100): vol.All(vol.Coerce(int), vol.Range(min=1, max=1000)),
    }
)
@callback
def ws_activity(hass, connection, msg) -> None:
    try:
        _, manager = _runtime(hass)
        connection.send_result(msg["id"], {"activity": manager.activity(msg["limit"])})
    except Exception as err:  # noqa: BLE001
        connection.send_error(msg["id"], "activity_failed", str(err))


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/multiway/settings"})
@callback
def ws_get_settings(hass, connection, msg) -> None:
    try:
        store, _ = _runtime(hass)
        connection.send_result(msg["id"], store.settings())
    except Exception as err:  # noqa: BLE001
        connection.send_error(msg["id"], "settings_failed", str(err))


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/multiway/update_settings",
        vol.Required("settings"): dict,
    }
)
@websocket_api.async_response
async def ws_update_settings(hass, connection, msg) -> None:
    try:
        store, manager = _runtime(hass)
        settings = await store.async_update_settings(msg["settings"])
        await manager.async_reload(reconcile=False)
        connection.send_result(msg["id"], settings)
    except Exception as err:  # noqa: BLE001
        connection.send_error(msg["id"], "settings_update_failed", str(err))


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/multiway/export"})
@callback
def ws_export(hass, connection, msg) -> None:
    try:
        store, _ = _runtime(hass)
        connection.send_result(msg["id"], store.export_data())
    except Exception as err:  # noqa: BLE001
        connection.send_error(msg["id"], "export_failed", str(err))


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/multiway/import",
        vol.Required("data"): dict,
        vol.Optional("replace", default=False): bool,
    }
)
@websocket_api.async_response
async def ws_import(hass, connection, msg) -> None:
    try:
        _ensure_config_unlocked(hass)
        store, manager = _runtime(hass)
        old_ids = {group["id"] for group in store.groups()} if msg["replace"] else set()
        result = await store.async_import_data(msg["data"], msg["replace"])
        if msg["replace"]:
            new_ids = {group["id"] for group in store.groups()}
            for group_id in old_ids - new_ids:
                _remove_group_registry_entities(hass, group_id)
        await manager.async_reload(reconcile=True)
        connection.send_result(msg["id"], result)
    except Exception as err:  # noqa: BLE001
        connection.send_error(msg["id"], "import_failed", str(err))


@websocket_api.require_admin
@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/multiway/test", vol.Required("group_id"): str}
)
@callback
def ws_test(hass, connection, msg) -> None:
    try:
        _, manager = _runtime(hass)
        connection.send_result(msg["id"], manager.test_group(msg["group_id"]))
    except Exception as err:  # noqa: BLE001
        connection.send_error(msg["id"], "test_failed", str(err))


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/multiway/test_entity_action",
        vol.Required("group_id"): str,
        vol.Required("entity_id"): str,
    }
)
@websocket_api.async_response
async def ws_test_entity_action(hass, connection, msg) -> None:
    """Exercise one group member through the real multi-way propagation path."""
    try:
        _, manager = _runtime(hass)
        result = await manager.async_test_entity_action(msg["group_id"], msg["entity_id"])
        connection.send_result(msg["id"], result)
    except Exception as err:  # noqa: BLE001
        connection.send_error(msg["id"], "test_entity_failed", str(err))



@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/multiway/rapid_toggle_test",
        vol.Required("group_id"): str,
        vol.Required("entity_id"): str,
        vol.Optional("count", default=4): vol.All(vol.Coerce(int), vol.Range(min=2, max=10)),
        vol.Optional("interval_ms", default=120): vol.All(vol.Coerce(int), vol.Range(min=50, max=1000)),
    }
)
@websocket_api.async_response
async def ws_rapid_toggle_test(hass, connection, msg) -> None:
    """Run a physical rapid-edge stress test against one group member."""
    try:
        _, manager = _runtime(hass)
        result = await manager.async_rapid_toggle_test(
            msg["group_id"], msg["entity_id"], msg["count"], msg["interval_ms"]
        )
        connection.send_result(msg["id"], result)
    except Exception as err:  # noqa: BLE001
        connection.send_error(msg["id"], "rapid_test_failed", str(err))


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/multiway/learn_start",
        vol.Required("role"): vol.In(["output", "controller"]),
        vol.Optional("timeout", default=12): vol.All(vol.Coerce(float), vol.Range(min=5, max=30)),
        vol.Optional("domains", default=None): vol.Any(None, [str]),
    }
)
@callback
def ws_learn_start(hass, connection, msg) -> None:
    """Start a temporary learn session."""
    try:
        _, manager = _runtime(hass)
        connection.send_result(
            msg["id"],
            manager.start_learn(msg["role"], msg["timeout"], msg.get("domains")),
        )
    except Exception as err:  # noqa: BLE001
        connection.send_error(msg["id"], "learn_start_failed", str(err))


@websocket_api.require_admin
@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/multiway/learn_status", vol.Required("session_id"): str}
)
@callback
def ws_learn_status(hass, connection, msg) -> None:
    """Return current learn candidates."""
    try:
        _, manager = _runtime(hass)
        connection.send_result(msg["id"], manager.learn_status(msg["session_id"]))
    except Exception as err:  # noqa: BLE001
        connection.send_error(msg["id"], "learn_status_failed", str(err))


@websocket_api.require_admin
@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/multiway/learn_cancel", vol.Required("session_id"): str}
)
@callback
def ws_learn_cancel(hass, connection, msg) -> None:
    """Cancel an active learn session."""
    try:
        _, manager = _runtime(hass)
        connection.send_result(msg["id"], {"ok": manager.cancel_learn(msg["session_id"])})
    except Exception as err:  # noqa: BLE001
        connection.send_error(msg["id"], "learn_cancel_failed", str(err))


SMART_MEMBER_SCHEMA = vol.Schema(
    {
        vol.Required("entity_id"): str,
        vol.Optional("enabled", default=True): bool,
    },
    extra=vol.PREVENT_EXTRA,
)

SMART_GROUP_FIELDS = {
    vol.Required("name"): vol.All(str, vol.Length(min=1, max=100)),
    vol.Required("kind"): vol.In(list(SMART_KINDS)),
    vol.Optional("controller_entity", default=None): vol.Any(None, str),
    vol.Required("members"): vol.All([SMART_MEMBER_SCHEMA], vol.Length(min=1)),
    vol.Optional("group_type", default=VIRTUAL_LIGHT): vol.In(sorted(SMART_GROUP_TYPES)),
    vol.Optional("virtual_type", default=VIRTUAL_LIGHT): str,
    vol.Optional("area_id", default=None): vol.Any(None, str),
    vol.Optional("enabled", default=True): bool,
    vol.Optional("maintenance", default=False): bool,
    vol.Optional("locked", default=False): bool,
    vol.Optional("favorite", default=False): bool,
    vol.Optional("hide_members", default=False): bool,
    vol.Optional("behavior", default={}): dict,
}


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/multiway/smart/list"})
@callback
def ws_smart_list(hass, connection, msg) -> None:
    try:
        data = _runtime_all(hass)
        connection.send_result(msg["id"], {
            "version": VERSION,
            "groups": data["smart_manager"].list_with_runtime(),
            "summary": data["smart_manager"].summary(),
            "settings": data["smart_store"].settings(),
            "templates": data["smart_store"].templates(),
            "snapshots": data["smart_store"].snapshots()[-10:],
        })
    except Exception as err:  # noqa: BLE001
        connection.send_error(msg["id"], "smart_list_failed", str(err))


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/multiway/smart/create", **SMART_GROUP_FIELDS})
@websocket_api.async_response
async def ws_smart_create(hass, connection, msg) -> None:
    try:
        _ensure_config_unlocked(hass)
        data = _runtime_all(hass)
        payload = {k: v for k, v in msg.items() if k not in {"id", "type"}}
        group = await data["smart_store"].async_create(payload)
        await data["smart_manager"].async_reload()
        connection.send_result(msg["id"], group)
    except Exception as err:  # noqa: BLE001
        connection.send_error(msg["id"], "smart_create_failed", str(err))


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/multiway/smart/update", vol.Required("group_id"): str, **SMART_GROUP_FIELDS})
@websocket_api.async_response
async def ws_smart_update(hass, connection, msg) -> None:
    try:
        _ensure_config_unlocked(hass)
        data = _runtime_all(hass)
        old = data["smart_store"].get(msg["group_id"])
        payload = {k: v for k, v in msg.items() if k not in {"id", "type", "group_id"}}
        group = await data["smart_store"].async_update(msg["group_id"], payload)
        old_type = (old or {}).get("group_type") or (old or {}).get("virtual_type")
        new_type = group.get("group_type") or group.get("virtual_type")
        if old:
            old_is_action = old_type in SMART_ACTION_TYPES
            new_is_action = new_type in SMART_ACTION_TYPES
            remove_old_control = False
            if old_is_action:
                # All Action Group domains intentionally share one persistent
                # button control entity, even when a physical controller is added.
                remove_old_control = not new_is_action
            elif old.get("kind") == SMART_KIND_VIRTUAL:
                remove_old_control = (
                    group.get("kind") != SMART_KIND_VIRTUAL or old_type != new_type
                )
            if remove_old_control:
                _remove_smart_control_registry_entity(
                    hass, group["id"], old_type or VIRTUAL_LIGHT
                )
        await data["smart_manager"].async_reload()
        connection.send_result(msg["id"], group)
    except Exception as err:  # noqa: BLE001
        connection.send_error(msg["id"], "smart_update_failed", str(err))


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/multiway/smart/delete", vol.Required("group_id"): str})
@websocket_api.async_response
async def ws_smart_delete(hass, connection, msg) -> None:
    try:
        _ensure_config_unlocked(hass)
        data = _runtime_all(hass)
        await data["smart_store"].async_delete(msg["group_id"])
        _remove_smart_registry_entities(hass, msg["group_id"])
        await data["smart_manager"].async_reload()
        connection.send_result(msg["id"], {"ok": True})
    except Exception as err:  # noqa: BLE001
        connection.send_error(msg["id"], "smart_delete_failed", str(err))


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/multiway/smart/clone", vol.Required("group_id"): str, vol.Optional("name"): str})
@websocket_api.async_response
async def ws_smart_clone(hass, connection, msg) -> None:
    try:
        _ensure_config_unlocked(hass)
        data = _runtime_all(hass)
        group = await data["smart_store"].async_clone(msg["group_id"], msg.get("name"))
        await data["smart_manager"].async_reload()
        connection.send_result(msg["id"], group)
    except Exception as err:  # noqa: BLE001
        connection.send_error(msg["id"], "smart_clone_failed", str(err))


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/multiway/smart/set_state", vol.Required("group_id"): str, vol.Required("state"): vol.In(["on", "off"])})
@websocket_api.async_response
async def ws_smart_set_state(hass, connection, msg) -> None:
    try:
        data = _runtime_all(hass)
        ok = await data["smart_manager"].async_set_state(msg["group_id"], msg["state"], source="panel", origin="virtual")
        connection.send_result(msg["id"], {"ok": ok, "runtime": data["smart_manager"].status(msg["group_id"])})
    except Exception as err:  # noqa: BLE001
        connection.send_error(msg["id"], "smart_set_state_failed", str(err))


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/multiway/smart/action",
        vol.Required("group_id"): str,
        vol.Required("action"): str,
        vol.Optional("service_data", default={}): dict,
    }
)
@websocket_api.async_response
async def ws_smart_action(hass, connection, msg) -> None:
    """Execute a domain-aware action against one Smart Group."""
    try:
        data = _runtime_all(hass)
        ok = await data["smart_manager"].async_action(
            msg["group_id"],
            msg["action"],
            source="panel",
            service_data=msg.get("service_data") or None,
        )
        connection.send_result(
            msg["id"],
            {"ok": ok, "runtime": data["smart_manager"].status(msg["group_id"])},
        )
    except Exception as err:  # noqa: BLE001
        connection.send_error(msg["id"], "smart_action_failed", str(err))


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/multiway/smart/set_enabled",
        vol.Required("group_id"): str,
        vol.Required("enabled"): bool,
    }
)
@websocket_api.async_response
async def ws_smart_set_enabled(hass, connection, msg) -> None:
    """Enable or disable one Smart Group."""
    try:
        data = _runtime_all(hass)
        group = await data["smart_manager"].async_set_enabled(
            msg["group_id"], msg["enabled"]
        )
        connection.send_result(
            msg["id"],
            {
                "group": group,
                "runtime": data["smart_manager"].status(msg["group_id"]),
            },
        )
    except Exception as err:  # noqa: BLE001
        connection.send_error(msg["id"], "smart_set_enabled_failed", str(err))


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/multiway/smart/sync", vol.Required("group_id"): str})
@websocket_api.async_response
async def ws_smart_sync(hass, connection, msg) -> None:
    try:
        data = _runtime_all(hass)
        ok = await data["smart_manager"].async_sync(msg["group_id"])
        connection.send_result(msg["id"], {"ok": ok})
    except Exception as err:  # noqa: BLE001
        connection.send_error(msg["id"], "smart_sync_failed", str(err))


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/multiway/smart/test", vol.Required("group_id"): str, vol.Optional("destructive", default=False): bool})
@websocket_api.async_response
async def ws_smart_test(hass, connection, msg) -> None:
    try:
        data = _runtime_all(hass)
        result = await data["smart_manager"].async_full_test(msg["group_id"], msg["destructive"])
        connection.send_result(msg["id"], result)
    except Exception as err:  # noqa: BLE001
        connection.send_error(msg["id"], "smart_test_failed", str(err))


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/multiway/smart/test_all"})
@websocket_api.async_response
async def ws_smart_test_all(hass, connection, msg) -> None:
    try:
        data = _runtime_all(hass)
        connection.send_result(msg["id"], await data["smart_manager"].async_test_all())
    except Exception as err:  # noqa: BLE001
        connection.send_error(msg["id"], "smart_test_all_failed", str(err))


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/multiway/smart/quarantine", vol.Required("group_id"): str, vol.Required("entity_id"): str, vol.Required("enabled"): bool})
@websocket_api.async_response
async def ws_smart_quarantine(hass, connection, msg) -> None:
    try:
        data = _runtime_all(hass)
        await data["smart_manager"].async_set_member_quarantine(msg["group_id"], msg["entity_id"], msg["enabled"])
        connection.send_result(msg["id"], data["smart_manager"].status(msg["group_id"]))
    except Exception as err:  # noqa: BLE001
        connection.send_error(msg["id"], "smart_quarantine_failed", str(err))


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/multiway/smart/settings", vol.Required("settings"): dict})
@websocket_api.async_response
async def ws_smart_settings(hass, connection, msg) -> None:
    try:
        data = _runtime_all(hass)
        settings = await data["smart_store"].async_set_settings(msg["settings"])
        connection.send_result(msg["id"], settings)
    except Exception as err:  # noqa: BLE001
        connection.send_error(msg["id"], "smart_settings_failed", str(err))


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/multiway/smart/template_save", vol.Required("group_id"): str, vol.Required("name"): str})
@websocket_api.async_response
async def ws_smart_template_save(hass, connection, msg) -> None:
    try:
        _ensure_config_unlocked(hass)
        data = _runtime_all(hass)
        template = await data["smart_store"].async_save_template(msg["name"], msg["group_id"])
        connection.send_result(msg["id"], template)
    except Exception as err:  # noqa: BLE001
        connection.send_error(msg["id"], "smart_template_failed", str(err))


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/multiway/smart/template_delete", vol.Required("template_id"): str})
@websocket_api.async_response
async def ws_smart_template_delete(hass, connection, msg) -> None:
    try:
        _ensure_config_unlocked(hass)
        data = _runtime_all(hass)
        await data["smart_store"].async_delete_template(msg["template_id"])
        connection.send_result(msg["id"], {"ok": True})
    except Exception as err:  # noqa: BLE001
        connection.send_error(msg["id"], "smart_template_delete_failed", str(err))


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/multiway/smart/undo"})
@websocket_api.async_response
async def ws_smart_undo(hass, connection, msg) -> None:
    try:
        _ensure_config_unlocked(hass)
        data = _runtime_all(hass)
        result = await data["smart_store"].async_undo_last()
        await data["smart_manager"].async_reload()
        connection.send_result(msg["id"], result)
    except Exception as err:  # noqa: BLE001
        connection.send_error(msg["id"], "smart_undo_failed", str(err))


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/multiway/undo"})
@websocket_api.async_response
async def ws_multiway_undo(hass, connection, msg) -> None:
    try:
        _ensure_config_unlocked(hass)
        data = _runtime_all(hass)
        result = await data["store"].async_undo_last()
        await data["manager"].async_reload(reconcile=False)
        connection.send_result(msg["id"], result)
    except Exception as err:  # noqa: BLE001
        connection.send_error(msg["id"], "multiway_undo_failed", str(err))


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/multiway/smart/diagnostics", vol.Optional("group_id"): str})
@callback
def ws_smart_diagnostics(hass, connection, msg) -> None:
    try:
        data = _runtime_all(hass)
        connection.send_result(msg["id"], data["smart_manager"].diagnostics_bundle(msg.get("group_id")))
    except Exception as err:  # noqa: BLE001
        connection.send_error(msg["id"], "smart_diagnostics_failed", str(err))


def _native_group_entries(hass: HomeAssistant) -> list[dict]:
    """Compatibility wrapper around the native Group helper inspector."""
    return native_group_entries(hass)


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/multiway/smart/ha_groups"})
@callback
def ws_smart_ha_groups(hass, connection, msg) -> None:
    try:
        connection.send_result(msg["id"], {"groups": _native_group_entries(hass)})
    except Exception as err:  # noqa: BLE001
        connection.send_error(msg["id"], "native_groups_failed", str(err))


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/multiway/smart/import_ha_group",
        vol.Required("entity_id"): str,
    }
)
@callback
def ws_smart_import_ha_group(hass, connection, msg) -> None:
    """Reject the retired copy-import endpoint so stale UIs cannot delete helpers."""
    connection.send_error(
        msg["id"],
        "native_group_import_retired",
        "Group import was replaced by transactional Take Over in V3.1. "
        "Refresh the Eshtaya Control Center and use Take Over.",
    )


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/multiway/smart/takeover_ha_group",
        vol.Required("entity_id"): str,
    }
)
@websocket_api.async_response
async def ws_smart_takeover_ha_group(hass, connection, msg) -> None:
    """Take full ownership of a UI-created Home Assistant Group helper."""
    try:
        _ensure_config_unlocked(hass)
        data = _runtime_all(hass)
        result = await async_take_over_group(
            hass,
            data["smart_store"],
            data["smart_manager"],
            msg["entity_id"],
        )
        connection.send_result(msg["id"], result)
    except Exception as err:  # noqa: BLE001
        connection.send_error(msg["id"], "native_group_takeover_failed", str(err))


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/multiway/smart/refresh_ha_group",
        vol.Required("group_id"): str,
    }
)
@websocket_api.async_response
async def ws_smart_refresh_ha_group(hass, connection, msg) -> None:
    """Refresh an imported Smart Group membership from its HA source group."""
    try:
        _ensure_config_unlocked(hass)
        data = _runtime_all(hass)
        group = data["smart_store"].get(msg["group_id"])
        if not group:
            raise ValueError("Smart Group not found")
        source_entity = group.get("source_group_entity")
        if not source_entity:
            raise ValueError("This Smart Group was not imported from Home Assistant")
        found = next(
            (item for item in _native_group_entries(hass) if item["entity_id"] == source_entity),
            None,
        )
        if not found:
            raise ValueError("The source Home Assistant group no longer exists")
        members = [
            member
            for member in found["members"]
            if member.split(".", 1)[0] in SMART_MEMBER_DOMAINS
        ]
        if not members:
            raise ValueError("The source group has no compatible commandable members")
        existing_enabled = {
            item["entity_id"]: bool(item.get("enabled", True))
            for item in group.get("members", [])
        }
        updated = await data["smart_store"].async_update(
            group["id"],
            {
                "members": [
                    {
                        "entity_id": member,
                        "enabled": existing_enabled.get(member, True),
                    }
                    for member in members
                ],
                "area_id": found.get("area_id") or group.get("area_id"),
                "source_group_entity": source_entity,
            },
        )
        await data["smart_manager"].async_reload()
        connection.send_result(
            msg["id"],
            {
                "group": updated,
                "source": found,
                "members_refreshed": len(members),
                "original_unchanged": True,
            },
        )
    except Exception as err:  # noqa: BLE001
        connection.send_error(msg["id"], "native_group_refresh_failed", str(err))

@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/multiway/backup/full_export"})
@callback
def ws_full_export(hass, connection, msg) -> None:
    try:
        data = _runtime_all(hass)
        connection.send_result(msg["id"], {
            "format": "eshtaya_multiway_full_backup",
            "version": VERSION,
            "multiway": data["store"].export_data(),
            "smart_groups": data["smart_store"].export_data(),
        })
    except Exception as err:  # noqa: BLE001
        connection.send_error(msg["id"], "full_export_failed", str(err))


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/multiway/backup/full_import", vol.Required("data"): dict})
@websocket_api.async_response
async def ws_full_import(hass, connection, msg) -> None:
    try:
        _ensure_config_unlocked(hass)
        data = _runtime_all(hass)
        payload = msg["data"]
        if payload.get("format") != "eshtaya_multiway_full_backup":
            raise ValueError("Unsupported backup format")
        old_multi = data["store"].export_data()
        old_smart = data["smart_store"].export_data()
        try:
            await data["store"].async_import_data(payload.get("multiway") or {}, True)
            await data["smart_store"].async_import(payload.get("smart_groups") or {}, True)
        except Exception:
            await data["store"].async_import_data(old_multi, True)
            await data["smart_store"].async_import(old_smart, True)
            raise
        await data["manager"].async_reload(reconcile=False)
        await data["smart_manager"].async_reload()
        connection.send_result(msg["id"], {"ok": True})
    except Exception as err:  # noqa: BLE001
        connection.send_error(msg["id"], "full_import_failed", str(err))


def _missing_references(hass: HomeAssistant) -> list[dict]:
    data = _runtime_all(hass)
    registry = er.async_get(hass)
    rows = []
    def meta(entity_id: str) -> tuple[str | None, str]:
        entry = registry.async_get(entity_id)
        return (getattr(entry, "area_id", None) if entry else None, entity_id.split(".", 1)[0])
    for group in data["store"].groups():
        refs = [("output", group["output"])] + [("controller", c["entity_id"]) for c in group["controllers"]]
        fallback = group.get("behavior", {}).get("fallback_output")
        if fallback:
            refs.append(("fallback_output", fallback))
        for role, entity_id in refs:
            if hass.states.get(entity_id) is None:
                area_id, domain = meta(entity_id)
                rows.append({"engine":"multiway","group_id":group["id"],"group_name":group["name"],"role":role,"entity_id":entity_id,"domain":domain,"area_id":area_id})
    for group in data["smart_store"].groups():
        refs = []
        if group.get("controller_entity"):
            refs.append(("controller", group["controller_entity"]))
        refs += [("member", m["entity_id"]) for m in group["members"]]
        for role, entity_id in refs:
            if hass.states.get(entity_id) is None:
                area_id, domain = meta(entity_id)
                rows.append({"engine":"smart","group_id":group["id"],"group_name":group["name"],"role":role,"entity_id":entity_id,"domain":domain,"area_id":area_id})
    return rows


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/multiway/repair/missing"})
@callback
def ws_repair_missing(hass, connection, msg) -> None:
    try:
        connection.send_result(msg["id"], {"missing": _missing_references(hass)})
    except Exception as err:  # noqa: BLE001
        connection.send_error(msg["id"], "repair_missing_failed", str(err))


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/multiway/repair/remap", vol.Required("mapping"): dict})
@websocket_api.async_response
async def ws_repair_remap(hass, connection, msg) -> None:
    try:
        _ensure_config_unlocked(hass)
        data = _runtime_all(hass)
        mapping = {str(k): str(v) for k, v in msg["mapping"].items() if k and v and k != v}
        if not mapping:
            raise ValueError("A non-empty mapping is required")
        for entity_id in mapping.values():
            if hass.states.get(entity_id) is None:
                raise ValueError(f"Replacement entity {entity_id} does not exist")
        old_multi = data["store"].export_data()
        old_smart = data["smart_store"].export_data()
        try:
            await data["store"].async_remap_entities(mapping)
            await data["smart_store"].async_remap_entities(mapping)
        except Exception:
            await data["store"].async_import_data(old_multi, True)
            await data["smart_store"].async_import(old_smart, True)
            raise
        await data["manager"].async_reload(reconcile=False)
        await data["smart_manager"].async_reload()
        connection.send_result(msg["id"], {"ok": True, "missing": _missing_references(hass)})
    except Exception as err:  # noqa: BLE001
        connection.send_error(msg["id"], "repair_remap_failed", str(err))



def _remove_smart_control_registry_entity(
    hass: HomeAssistant, group_id: str, group_type: str
) -> None:
    """Remove only the obsolete Smart Group control entity after a type change."""
    registry = er.async_get(hass)
    if group_type in SMART_ACTION_TYPES:
        platform = Platform.BUTTON
        unique_id = f"smart_{group_id}_control_action"
    else:
        try:
            platform = Platform(group_type)
        except ValueError:
            return
        unique_id = f"smart_{group_id}_control_{group_type}"
    entity_id = registry.async_get_entity_id(platform, DOMAIN, unique_id)
    if entity_id:
        registry.async_remove(entity_id)


def _remove_smart_registry_entities(hass: HomeAssistant, group_id: str) -> None:
    registry = er.async_get(hass)
    pairs: list[tuple[Platform, str]] = []
    for group_type in sorted(SMART_GROUP_TYPES - SMART_ACTION_TYPES):
        try:
            platform = Platform(group_type)
        except ValueError:
            continue
        pairs.append((platform, f"smart_{group_id}_control_{group_type}"))
    pairs.extend(
        [
            (Platform.BUTTON, f"smart_{group_id}_control_action"),
            (Platform.SWITCH, f"smart_{group_id}_enabled"),
            (Platform.SENSOR, f"smart_{group_id}_health"),
            (Platform.SENSOR, f"smart_{group_id}_quality"),
            (Platform.SENSOR, f"smart_{group_id}_last_source"),
            (Platform.SENSOR, f"smart_{group_id}_last_latency"),
            (Platform.BINARY_SENSOR, f"smart_{group_id}_healthy"),
            (Platform.BUTTON, f"smart_{group_id}_sync"),
        ]
    )
    for platform, unique_id in pairs:
        entity_id = registry.async_get_entity_id(platform, DOMAIN, unique_id)
        if entity_id:
            registry.async_remove(entity_id)


def _remove_virtual_registry_entity(hass: HomeAssistant, group_id: str, virtual_type: str) -> None:
    registry = er.async_get(hass)
    platform = Platform.LIGHT if virtual_type == VIRTUAL_LIGHT else Platform.SWITCH
    unique_id = f"{group_id}_control_{virtual_type}"
    entity_id = registry.async_get_entity_id(platform, DOMAIN, unique_id)
    if entity_id:
        registry.async_remove(entity_id)


def _remove_group_registry_entities(hass: HomeAssistant, group_id: str) -> None:
    registry = er.async_get(hass)
    pairs = [
        (Platform.LIGHT, f"{group_id}_control_light"),
        (Platform.SWITCH, f"{group_id}_control_switch"),
        (Platform.SWITCH, f"{group_id}_enabled"),
        (Platform.SENSOR, f"{group_id}_health"),
        (Platform.SENSOR, f"{group_id}_last_source"),
        (Platform.SENSOR, f"{group_id}_last_latency"),
        (Platform.BINARY_SENSOR, f"{group_id}_in_sync"),
        (Platform.BUTTON, f"{group_id}_sync"),
    ]
    for platform, unique_id in pairs:
        entity_id = registry.async_get_entity_id(platform, DOMAIN, unique_id)
        if entity_id:
            registry.async_remove(entity_id)
