"""Integrated Template Manager module."""
from __future__ import annotations

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall

from ..const import DOMAIN
from .const import DATA_TEMPLATE_MANAGER, LEGACY_DOMAIN

CREATE_SCHEMA = vol.Schema(
    {
        vol.Required("source_entity"): str,
        vol.Required("template_type"): vol.In(["light", "fan"]),
        vol.Required("name"): str,
        vol.Required("entity_id"): str,
    }
)
EDIT_SCHEMA = vol.Schema(
    {
        vol.Required("managed_entity"): str,
        vol.Required("name"): str,
        vol.Required("entity_id"): str,
    }
)
DELETE_SCHEMA = vol.Schema({vol.Required("managed_entity"): str})
RELINK_SCHEMA = vol.Schema(
    {vol.Required("managed_entity"): str, vol.Required("source_entity"): str}
)

_LEGACY_SERVICES = (
    "scan",
    "create_template",
    "edit_template",
    "delete_template",
    "relink",
)


def _manager(hass: HomeAssistant):
    manager = hass.data.get(DOMAIN, {}).get(DATA_TEMPLATE_MANAGER)
    if manager is None:
        raise RuntimeError("Template Manager is not initialized")
    return manager


def _register(hass: HomeAssistant, service_domain: str, service: str, handler, schema=None, *, replace=False) -> None:
    if replace and hass.services.has_service(service_domain, service):
        hass.services.async_remove(service_domain, service)
    if not hass.services.has_service(service_domain, service):
        hass.services.async_register(service_domain, service, handler, schema=schema)


def async_remove_legacy_services(hass: HomeAssistant) -> None:
    """Remove compatibility aliases from the retired Template Manager domain."""
    for service in _LEGACY_SERVICES:
        if hass.services.has_service(LEGACY_DOMAIN, service):
            hass.services.async_remove(LEGACY_DOMAIN, service)


async def async_setup_services(
    hass: HomeAssistant,
    *,
    register_legacy: bool = False,
    replace_legacy: bool = False,
) -> None:
    """Register unified services and, when explicitly enabled, legacy aliases."""

    async def scan(_call: ServiceCall) -> None:
        await _manager(hass).async_scan()

    async def create_template(call: ServiceCall) -> None:
        await _manager(hass).async_create(**dict(call.data))

    async def edit_template(call: ServiceCall) -> None:
        await _manager(hass).async_edit(**dict(call.data))

    async def delete_template(call: ServiceCall) -> None:
        await _manager(hass).async_delete(call.data["managed_entity"])

    async def relink(call: ServiceCall) -> None:
        await _manager(hass).async_relink(**dict(call.data))

    unified = {
        "template_scan": (scan, None),
        "template_create": (create_template, CREATE_SCHEMA),
        "template_edit": (edit_template, EDIT_SCHEMA),
        "template_delete": (delete_template, DELETE_SCHEMA),
        "template_relink": (relink, RELINK_SCHEMA),
    }
    for service, (handler, schema) in unified.items():
        _register(hass, DOMAIN, service, handler, schema)

    if not register_legacy:
        async_remove_legacy_services(hass)
        return

    legacy = {
        "scan": (scan, None),
        "create_template": (create_template, CREATE_SCHEMA),
        "edit_template": (edit_template, EDIT_SCHEMA),
        "delete_template": (delete_template, DELETE_SCHEMA),
        "relink": (relink, RELINK_SCHEMA),
    }
    for service, (handler, schema) in legacy.items():
        _register(
            hass,
            LEGACY_DOMAIN,
            service,
            handler,
            schema,
            replace=replace_legacy,
        )
