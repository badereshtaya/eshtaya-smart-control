"""Core WebSocket API for Eshtaya Smart Control."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .const import DATA_ENTITY_MANAGER, DATA_MIGRATION, DATA_TUYA_MANAGER, DOMAIN, VERSION
from .multiway.const import DATA_RUNTIME


@callback
def async_register_websocket_commands(hass: HomeAssistant) -> None:
    websocket_api.async_register_command(hass, websocket_overview)


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/overview"})
@websocket_api.async_response
async def websocket_overview(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    data = hass.data.get(DOMAIN, {})
    entity = data.get(DATA_ENTITY_MANAGER)
    tuya = data.get(DATA_TUYA_MANAGER)
    migration = data.get(DATA_MIGRATION)
    runtime = data.get(DATA_RUNTIME) or {}

    entity_stats = {}
    file_sync = None
    if entity:
        snapshot = await entity.async_get_snapshot(include_file=False)
        entity_stats = snapshot.get("stats", {})
        file_sync = snapshot.get("file", {}).get("sync")

    multi_store = runtime.get("store")
    smart_store = runtime.get("smart_store")
    multi_groups = len(multi_store.groups()) if multi_store else 0
    smart_groups = len(smart_store.groups()) if smart_store else 0

    legacy = {
        "entity_manager": bool(hass.config_entries.async_entries("eshtaya_entity_manager")),
        "multiway": bool(hass.config_entries.async_entries("eshtaya_multiway")),
    }
    migration_status = (
        await migration.async_public_status()
        if migration is not None
        else {"phase": "not_started", "completed": False, "legacy_found": False}
    )
    connection.send_result(
        msg["id"],
        {
            "version": VERSION,
            "entity": {"stats": entity_stats, "file_sync": file_sync},
            "tuya": tuya.public_status() if tuya else {"configured": False},
            "multiway": {"groups": multi_groups, "smart_groups": smart_groups},
            "legacy": legacy,
            "migration": migration_status,
        },
    )
