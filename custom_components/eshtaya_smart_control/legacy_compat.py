"""Compatibility aliases for automations using the former Multi-Way service domain."""
from __future__ import annotations

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse

from .const import DOMAIN

LEGACY_DOMAIN = "eshtaya_multiway"

_GROUP_SCHEMA = vol.Schema({vol.Required("group_id"): str})
_STATE_SCHEMA = vol.Schema(
    {vol.Required("group_id"): str, vol.Required("state"): vol.In(["on", "off"])}
)

_SERVICE_SPECS = {
    "sync_group": (_GROUP_SCHEMA, SupportsResponse.NONE),
    "sync_all": (None, SupportsResponse.NONE),
    "enable_group": (_GROUP_SCHEMA, SupportsResponse.NONE),
    "disable_group": (_GROUP_SCHEMA, SupportsResponse.NONE),
    "set_group_state": (_STATE_SCHEMA, SupportsResponse.NONE),
    "test_group": (_GROUP_SCHEMA, SupportsResponse.ONLY),
    "set_smart_group_state": (_STATE_SCHEMA, SupportsResponse.NONE),
    "run_smart_group": (_GROUP_SCHEMA, SupportsResponse.NONE),
    "sync_smart_group": (_GROUP_SCHEMA, SupportsResponse.NONE),
    "test_smart_group": (_GROUP_SCHEMA, SupportsResponse.ONLY),
}


def async_register_legacy_service_aliases(hass: HomeAssistant) -> None:
    """Forward legacy service calls to Eshtaya Smart Control."""
    for service, (schema, response_mode) in _SERVICE_SPECS.items():
        if hass.services.has_service(LEGACY_DOMAIN, service):
            continue

        async def _forward(call: ServiceCall, _service: str = service):
            return await hass.services.async_call(
                DOMAIN,
                _service,
                dict(call.data),
                blocking=True,
                return_response=_service in {"test_group", "test_smart_group"},
                context=call.context,
            )

        kwargs = {"supports_response": response_mode}
        if schema is not None:
            kwargs["schema"] = schema
        hass.services.async_register(LEGACY_DOMAIN, service, _forward, **kwargs)
