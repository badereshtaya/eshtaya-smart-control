"""Permission-aware Entity Control WebSocket registration for v2.2."""
from __future__ import annotations

from functools import wraps
from typing import Any

import voluptuous as vol
from homeassistant.auth.permissions.const import POLICY_EDIT, POLICY_READ
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from ..access_control import require_permission
from ..ws_permissions import permissioned_admin_command
from .const import WS_PREFIX
from .websocket import (
    _manager,
    websocket_bulk_rule,
    websocket_regenerate,
    websocket_rename,
    websocket_set_defaults,
    websocket_set_domain,
    websocket_set_entity_rule,
)
from .websocket_v11 import websocket_export_rules, websocket_import_rules
from .websocket_v12 import (
    websocket_cleanup_orphans,
    websocket_repair_sync,
    websocket_set_many_rules,
)


def _entity_allowed(connection, entity_id: str, permission: str) -> bool:
    user = getattr(connection, "user", None)
    if user is None:
        return False
    if user.is_admin:
        return True
    try:
        return bool(user.permissions.check_entity(entity_id, permission))
    except Exception:  # defensive compatibility boundary
        return False


def _native_entity_guard(command, permission: str, *, many: bool = False):
    """Require native HA entity permission in addition to Eshtaya permission."""

    @wraps(command)
    def guarded(hass, connection, msg, *args, **kwargs):
        entity_ids = msg.get("entity_ids") if many else [msg.get("entity_id")]
        entity_ids = [str(value) for value in (entity_ids or []) if value]
        if not entity_ids or not all(
            _entity_allowed(connection, entity_id, permission)
            for entity_id in entity_ids
        ):
            connection.send_error(
                msg["id"],
                "native_entity_unauthorized",
                f"Missing Home Assistant {permission} permission for one or more entities",
            )
            return None
        return command(hass, connection, msg, *args, **kwargs)

    return guarded


@require_permission("entity.view")
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{WS_PREFIX}/get",
        vol.Optional("include_file", default=False): bool,
    }
)
@websocket_api.async_response
async def websocket_get_access(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return an Entity/Alexa snapshot filtered by native HA read permission."""
    user = getattr(connection, "user", None)
    is_admin = bool(user and user.is_admin)
    payload = await _manager(hass).async_get_snapshot(
        include_file=bool(msg["include_file"] and is_admin)
    )
    if is_admin:
        connection.send_result(msg["id"], payload)
        return

    entities = [
        item
        for item in payload.get("entities", [])
        if _entity_allowed(connection, str(item.get("entity_id") or ""), POLICY_READ)
    ]
    allowed_ids = {str(item.get("entity_id") or "") for item in entities}
    domains = []
    for row in payload.get("domains", []):
        domain = str(row.get("domain") or "")
        scoped = [item for item in entities if item.get("domain") == domain]
        if not scoped:
            continue
        clean = dict(row)
        clean["count"] = len(scoped)
        clean["excluded"] = sum(1 for item in scoped if item.get("excluded"))
        domains.append(clean)

    excluded = sum(1 for item in entities if item.get("excluded"))
    renamed = sum(1 for item in entities if item.get("registry_name") is not None)
    unavailable = sum(1 for item in entities if not item.get("available", False))
    overrides = sum(1 for item in entities if item.get("rule") != "inherit")
    payload["entities"] = entities
    payload["domains"] = domains
    payload["stats"] = {
        "total": len(entities),
        "included": len(entities) - excluded,
        "excluded": excluded,
        "renamed": renamed,
        "unavailable": unavailable,
        "overrides": overrides,
    }
    payload.get("file", {}).pop("content", None)
    maintenance = payload.get("maintenance") or {}
    if isinstance(maintenance.get("orphan_rules"), list):
        maintenance["orphan_rules"] = [
            entity_id
            for entity_id in maintenance["orphan_rules"]
            if entity_id in allowed_ids
            or _entity_allowed(connection, str(entity_id), POLICY_READ)
        ]
        maintenance["orphan_count"] = len(maintenance["orphan_rules"])
    connection.send_result(msg["id"], payload)


@callback
def async_register_websocket_commands(hass: HomeAssistant) -> None:
    """Register native-permission-aware Entity APIs.

    Entity-specific changes can be delegated to non-admin Eshtaya technicians only
    when Home Assistant also grants Edit for the target entity. Global Alexa-rule
    operations remain Home Assistant admin-only because they can affect entities
    outside a restricted user's native policy.
    """
    websocket_api.async_register_command(hass, websocket_get_access)

    per_entity = (
        _native_entity_guard(
            permissioned_admin_command(websocket_set_entity_rule, "entity.manage"),
            POLICY_EDIT,
        ),
        _native_entity_guard(
            permissioned_admin_command(websocket_rename, "entity.manage"),
            POLICY_EDIT,
        ),
        _native_entity_guard(
            permissioned_admin_command(websocket_set_many_rules, "entity.manage"),
            POLICY_EDIT,
            many=True,
        ),
    )
    for command in per_entity:
        websocket_api.async_register_command(hass, command)

    # These operations are global by nature and can alter/export rules covering
    # entities outside a restricted user's native HA policy. Preserve HA's
    # original require_admin guard instead of weakening it.
    for command in (
        websocket_set_domain,
        websocket_set_defaults,
        websocket_bulk_rule,
        websocket_regenerate,
        websocket_export_rules,
        websocket_import_rules,
        websocket_repair_sync,
        websocket_cleanup_orphans,
    ):
        websocket_api.async_register_command(hass, command)
