"""Core administrator WebSocket API for Eshtaya Smart Control v2."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .const import (
    DATA_ENTITY_MANAGER,
    DATA_MIGRATION,
    DATA_STARTUP_STATUS,
    DATA_TUYA_MANAGER,
    DEFAULT_OPTIONS,
    DOMAIN,
    VERSION,
)
from .multiway.const import DATA_RUNTIME
from .runtime_options import runtime_options


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _recommendations(
    entity_stats: dict[str, Any],
    file_sync: dict[str, Any] | None,
    tuya: dict[str, Any],
    multi: dict[str, Any],
    smart: dict[str, Any],
    migration: dict[str, Any],
    startup: dict[str, Any],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    phase = str(migration.get("phase") or "")
    errors = migration.get("errors") or []
    if errors or phase in {"validation_failed", "rolled_back", "cleanup_partial"}:
        items.append({"id": "migration_attention", "severity": "critical", "target": "system"})
    elif migration.get("legacy_found") and not migration.get("completed"):
        items.append({"id": "migration_running", "severity": "info", "target": "system"})

    # Startup protection is an expected lifecycle state, never a fault. Surface it
    # as informational and suppress downstream Multi-Way degradation until ready.
    if startup and not startup.get("ready", False):
        items.append(
            {
                "id": "startup_protection_active",
                "severity": "info",
                "target": "system",
                "phase": startup.get("phase"),
                "pending": startup.get("pending_count", 0),
            }
        )

    if file_sync and file_sync.get("ok") is False:
        items.append({"id": "alexa_files_out_of_sync", "severity": "warning", "target": "entity", "action": "repair_alexa_files"})

    total = int(entity_stats.get("total") or 0)
    unavailable = int(entity_stats.get("unavailable") or 0)
    if total and unavailable >= max(5, round(total * 0.10)):
        items.append({"id": "many_unavailable_entities", "severity": "warning", "target": "entity", "count": unavailable})

    if startup.get("ready", True) and int(multi.get("degraded") or 0):
        items.append({"id": "multiway_degraded", "severity": "warning", "target": "multi", "count": int(multi.get("degraded") or 0)})
    if int(smart.get("degraded") or 0):
        items.append({"id": "smart_groups_degraded", "severity": "warning", "target": "multi", "count": int(smart.get("degraded") or 0)})

    # Tuya is intentionally optional, so this is informational and does not reduce health.
    if not tuya.get("configured"):
        items.append({"id": "tuya_not_activated", "severity": "info", "target": "tuya"})

    material = [i for i in items if i["severity"] in {"critical", "warning"}]
    if not material:
        items.insert(0, {"id": "system_healthy", "severity": "success", "target": "dashboard"})
    return items


def _health_score(entity_stats, file_sync, multi, smart, migration, startup) -> int:
    score = 100
    phase = str(migration.get("phase") or "")
    if migration.get("errors") or phase in {"validation_failed", "rolled_back", "cleanup_partial"}:
        score -= 30
    elif migration.get("legacy_found") and not migration.get("completed"):
        score -= 5
    if file_sync and file_sync.get("ok") is False:
        score -= 15
    total = int(entity_stats.get("total") or 0)
    unavailable = int(entity_stats.get("unavailable") or 0)
    if total:
        ratio = unavailable / total
        score -= min(20, round(ratio * 50))
    if startup.get("ready", True):
        score -= min(20, int(multi.get("degraded") or 0) * 5)
    score -= min(20, int(smart.get("degraded") or 0) * 4)
    return max(0, min(100, score))


def _public_options(hass: HomeAssistant) -> dict[str, Any]:
    """Expose only the safe operational options; never Tuya credentials."""
    current = runtime_options(hass)
    return {key: current.get(key, value) for key, value in DEFAULT_OPTIONS.items()}


async def _snapshot(hass: HomeAssistant) -> dict[str, Any]:
    data = hass.data.get(DOMAIN, {})
    entity = data.get(DATA_ENTITY_MANAGER)
    tuya_manager = data.get(DATA_TUYA_MANAGER)
    migration = data.get(DATA_MIGRATION)
    runtime = data.get(DATA_RUNTIME) or {}
    startup = dict(data.get(DATA_STARTUP_STATUS) or {})

    entity_stats: dict[str, Any] = {}
    file_sync = None
    maintenance: dict[str, Any] = {}
    if entity:
        snap = await entity.async_get_snapshot(include_file=False)
        entity_stats = snap.get("stats", {})
        file_sync = snap.get("file", {}).get("sync")
        maintenance = snap.get("maintenance", {})

    manager = runtime.get("manager")
    smart_manager = runtime.get("smart_manager")
    multi = manager.summary() if manager else {"groups": 0, "healthy": 0, "degraded": 0, "ready": False, "starting": True}
    smart = smart_manager.summary() if smart_manager else {"groups": 0, "healthy": 0, "degraded": 0, "average_quality": 100}
    tuya = tuya_manager.public_status() if tuya_manager else {"configured": False, "activated": False}
    migration_status = (
        await migration.async_public_status()
        if migration is not None
        else {"phase": "not_started", "completed": False, "legacy_found": False}
    )
    legacy = {
        "entity_manager": bool(hass.config_entries.async_entries("eshtaya_entity_manager")),
        "multiway": bool(hass.config_entries.async_entries("eshtaya_multiway")),
    }
    recommendations = _recommendations(
        entity_stats, file_sync, tuya, multi, smart, migration_status, startup
    )
    score = _health_score(entity_stats, file_sync, multi, smart, migration_status, startup)
    return {
        "version": VERSION,
        "generated_at": _utcnow(),
        "health": {
            "score": score,
            "state": "excellent" if score >= 90 else "good" if score >= 75 else "attention" if score >= 55 else "critical",
        },
        "entity": {"stats": entity_stats, "file_sync": file_sync, "maintenance": maintenance},
        "tuya": tuya,
        "multiway": multi,
        "smart_groups": smart,
        "startup": startup,
        "settings": _public_options(hass),
        "legacy": legacy,
        "migration": migration_status,
        "recommendations": recommendations,
    }


@callback
def async_register_websocket_commands(hass: HomeAssistant) -> None:
    for command in (
        websocket_overview,
        websocket_migration_report,
        websocket_system_report,
        websocket_system_action,
    ):
        websocket_api.async_register_command(hass, command)


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/overview"})
@websocket_api.async_response
async def websocket_overview(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    connection.send_result(msg["id"], await _snapshot(hass))


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/migration_report"})
@websocket_api.async_response
async def websocket_migration_report(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    migration = hass.data.get(DOMAIN, {}).get(DATA_MIGRATION)
    if migration is None:
        connection.send_result(
            msg["id"],
            {
                "schema": 1,
                "generated_at": _utcnow(),
                "integration": {"domain": DOMAIN, "version": VERSION},
                "migration": {"phase": "not_started", "completed": False, "legacy_found": False},
                "notes": ["Migration coordinator is not loaded."],
            },
        )
        return
    report = await migration.async_report()
    report["configured_options"] = _public_options(hass)
    connection.send_result(msg["id"], report)


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/system_report"})
@websocket_api.async_response
async def websocket_system_report(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    """Return a sanitized support report; raw storage and cloud credentials are never included."""
    snapshot = await _snapshot(hass)
    connection.send_result(
        msg["id"],
        {
            "schema": 3,
            "generated_at": _utcnow(),
            "integration": {"domain": DOMAIN, "version": VERSION},
            "system": snapshot,
            "privacy": [
                "Tuya Client Secret and access tokens are excluded.",
                "Raw migration backup/storage payloads are excluded.",
                "Only non-secret startup and migration settings are included.",
                "The report is intended for diagnostics and support.",
            ],
        },
    )


SYSTEM_ACTIONS = {"repair_alexa_files", "sync_groups", "refresh_tuya", "refresh_all"}


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/system_action",
        vol.Required("action"): vol.In(SYSTEM_ACTIONS),
        vol.Optional("confirm_physical", default=False): bool,
    }
)
@websocket_api.async_response
async def websocket_system_action(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    data = hass.data.get(DOMAIN, {})
    runtime = data.get(DATA_RUNTIME) or {}
    action = msg["action"]
    result: dict[str, Any] = {"ok": True, "action": action}
    try:
        if action in {"repair_alexa_files", "refresh_all"}:
            entity = data.get(DATA_ENTITY_MANAGER)
            result["alexa_files"] = await entity.async_repair_sync() if entity else {"skipped": True}

        if action in {"refresh_tuya", "refresh_all"}:
            tuya = data.get(DATA_TUYA_MANAGER)
            if tuya and tuya.configured:
                devices = await tuya.async_list_devices(force=True)
                result["tuya"] = {"refreshed": True, "devices": len(devices)}
            else:
                result["tuya"] = {"skipped": True, "reason": "not_activated"}

        if action == "sync_groups" or (action == "refresh_all" and msg.get("confirm_physical")):
            if not msg.get("confirm_physical"):
                raise ValueError("Physical group synchronization requires explicit confirmation")
            manager = runtime.get("manager")
            smart_manager = runtime.get("smart_manager")
            smart_store = runtime.get("smart_store")
            result["multiway"] = await manager.async_sync_all() if manager else {}
            smart_results = {}
            if smart_manager and smart_store:
                for group in smart_store.groups():
                    group_id = group.get("id")
                    if group_id:
                        try:
                            smart_results[group_id] = await smart_manager.async_sync(group_id)
                        except Exception as err:
                            smart_results[group_id] = {"ok": False, "error": str(err)}
            result["smart_groups"] = smart_results

        result["overview"] = await _snapshot(hass)
    except Exception as err:
        connection.send_error(msg["id"], "system_action_failed", str(err))
        return
    connection.send_result(msg["id"], result)
