"""Admin-only WebSocket API for Tuya Entity Control."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from ..const import DATA_TUYA_MANAGER, DOMAIN


def _manager(hass: HomeAssistant):
    return hass.data[DOMAIN][DATA_TUYA_MANAGER]


def _error(connection, msg, err):
    connection.send_error(msg["id"], "tuya_error", str(err))


@callback
def async_register_websocket_commands(hass: HomeAssistant) -> None:
    for command in (
        websocket_status, websocket_test_config, websocket_save_config, websocket_clear_config,
        websocket_list_devices, websocket_device_details, websocket_shadow_props,
        websocket_update_device_name, websocket_update_prop_name,
        websocket_bulk_details, websocket_bulk_save,
    ):
        websocket_api.async_register_command(hass, command)


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/tuya/status"})
@websocket_api.async_response
async def websocket_status(hass, connection, msg):
    connection.send_result(msg["id"], _manager(hass).public_status())


CONFIG_SCHEMA = {
    vol.Optional("tuya_region"): str,
    vol.Optional("tuya_endpoint"): str,
    vol.Optional("tuya_client_id"): str,
    vol.Optional("tuya_client_secret"): str,
    vol.Optional("tuya_uid"): str,
}


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/tuya/test_config", **CONFIG_SCHEMA})
@websocket_api.async_response
async def websocket_test_config(hass, connection, msg):
    try:
        result = await _manager(hass).async_test_config({k: v for k, v in msg.items() if k.startswith("tuya_")})
    except Exception as err:
        return _error(connection, msg, err)
    connection.send_result(msg["id"], result)


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/tuya/save_config", **CONFIG_SCHEMA})
@websocket_api.async_response
async def websocket_save_config(hass, connection, msg):
    try:
        result = await _manager(hass).async_save_config({k: v for k, v in msg.items() if k.startswith("tuya_")})
    except Exception as err:
        return _error(connection, msg, err)
    connection.send_result(msg["id"], result)


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/tuya/clear_config"})
@websocket_api.async_response
async def websocket_clear_config(hass, connection, msg):
    try:
        status = await _manager(hass).async_clear_config()
    except Exception as err:
        return _error(connection, msg, err)
    connection.send_result(msg["id"], {"ok": True, "status": status})


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/tuya/list_devices", vol.Optional("force", default=False): bool})
@websocket_api.async_response
async def websocket_list_devices(hass, connection, msg):
    try:
        devices = await _manager(hass).async_list_devices(force=msg["force"])
    except Exception as err:
        return _error(connection, msg, err)
    connection.send_result(msg["id"], {"devices": devices, "total": len(devices)})


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/tuya/device_details", vol.Required("device_id"): str})
@websocket_api.async_response
async def websocket_device_details(hass, connection, msg):
    try: result = await _manager(hass).async_device_details(msg["device_id"])
    except Exception as err: return _error(connection, msg, err)
    connection.send_result(msg["id"], result)


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/tuya/shadow_props", vol.Required("device_id"): str})
@websocket_api.async_response
async def websocket_shadow_props(hass, connection, msg):
    try: result = await _manager(hass).async_shadow_props(msg["device_id"])
    except Exception as err: return _error(connection, msg, err)
    connection.send_result(msg["id"], {"properties": result})


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/tuya/update_device_name", vol.Required("device_id"): str, vol.Required("name"): str})
@websocket_api.async_response
async def websocket_update_device_name(hass, connection, msg):
    try: await _manager(hass).async_update_device_name(msg["device_id"], msg["name"])
    except Exception as err: return _error(connection, msg, err)
    connection.send_result(msg["id"], {"ok": True})


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/tuya/update_prop_custom_name", vol.Required("device_id"): str, vol.Required("code"): str, vol.Required("custom_name"): str})
@websocket_api.async_response
async def websocket_update_prop_name(hass, connection, msg):
    try: await _manager(hass).async_update_prop_name(msg["device_id"], msg["code"], msg["custom_name"])
    except Exception as err: return _error(connection, msg, err)
    connection.send_result(msg["id"], {"ok": True})


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/tuya/bulk_details", vol.Required("device_ids"): [str]})
@websocket_api.async_response
async def websocket_bulk_details(hass, connection, msg):
    try: result = await _manager(hass).async_bulk_details(msg["device_ids"])
    except Exception as err: return _error(connection, msg, err)
    connection.send_result(msg["id"], {"devices": result})


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/tuya/bulk_save", vol.Required("changes"): [dict]})
@websocket_api.async_response
async def websocket_bulk_save(hass, connection, msg):
    try: result = await _manager(hass).async_bulk_save(msg["changes"])
    except Exception as err: return _error(connection, msg, err)
    connection.send_result(msg["id"], result)
