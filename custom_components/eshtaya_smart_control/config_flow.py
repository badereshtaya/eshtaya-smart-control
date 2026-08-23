"""Config and reconfigure flows for Eshtaya Smart Control."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_TUYA_CLIENT_ID,
    CONF_TUYA_CLIENT_SECRET,
    CONF_TUYA_ENDPOINT,
    CONF_TUYA_REGION,
    CONF_TUYA_UID,
    DOMAIN,
    TUYA_REGION_ENDPOINTS,
)
from .tuya.client import TuyaOpenApiClient

REGIONS = ["eu", "eu_west", "us", "us_east", "cn", "in", "sg", "custom"]


def _schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    defaults = defaults or {}
    region = str(defaults.get(CONF_TUYA_REGION, "eu"))
    endpoint = str(defaults.get(CONF_TUYA_ENDPOINT, TUYA_REGION_ENDPOINTS.get(region, "")))
    return vol.Schema(
        {
            vol.Optional(CONF_TUYA_REGION, default=region): SelectSelector(
                SelectSelectorConfig(options=REGIONS, mode=SelectSelectorMode.DROPDOWN, translation_key="tuya_region")
            ),
            vol.Optional(CONF_TUYA_ENDPOINT, default=endpoint): TextSelector(),
            vol.Optional(
                CONF_TUYA_CLIENT_ID, default=str(defaults.get(CONF_TUYA_CLIENT_ID, ""))
            ): TextSelector(TextSelectorConfig(autocomplete="username")),
            vol.Optional(CONF_TUYA_CLIENT_SECRET, default=""): TextSelector(
                TextSelectorConfig(
                    type=TextSelectorType.PASSWORD, autocomplete="current-password"
                )
            ),
            vol.Optional(
                CONF_TUYA_UID, default=str(defaults.get(CONF_TUYA_UID, ""))
            ): TextSelector(),
        }
    )


def _normalize(raw: dict[str, Any], current: dict[str, Any] | None = None) -> dict[str, str]:
    current = current or {}
    region = str(raw.get(CONF_TUYA_REGION, current.get(CONF_TUYA_REGION, "eu")))
    endpoint = str(
        raw.get(CONF_TUYA_ENDPOINT, current.get(CONF_TUYA_ENDPOINT, ""))
    ).strip().rstrip("/")
    if region != "custom":
        endpoint = TUYA_REGION_ENDPOINTS[region]
    client_id = str(raw.get(CONF_TUYA_CLIENT_ID, "")).strip() or str(
        current.get(CONF_TUYA_CLIENT_ID, "")
    ).strip()
    secret = str(raw.get(CONF_TUYA_CLIENT_SECRET, "")).strip() or str(
        current.get(CONF_TUYA_CLIENT_SECRET, "")
    ).strip()
    uid = str(raw.get(CONF_TUYA_UID, "")).strip() or str(
        current.get(CONF_TUYA_UID, "")
    ).strip()
    return {
        CONF_TUYA_REGION: region,
        CONF_TUYA_ENDPOINT: endpoint,
        CONF_TUYA_CLIENT_ID: client_id,
        CONF_TUYA_CLIENT_SECRET: secret,
        CONF_TUYA_UID: uid,
    }


def _tuya_field_state(data: dict[str, str]) -> tuple[bool, bool]:
    values = [
        data.get(CONF_TUYA_CLIENT_ID, ""),
        data.get(CONF_TUYA_CLIENT_SECRET, ""),
        data.get(CONF_TUYA_UID, ""),
    ]
    return any(values), all(values)


async def _validate_tuya(hass, data: dict[str, str]) -> None:
    client = TuyaOpenApiClient(
        hass,
        endpoint=data[CONF_TUYA_ENDPOINT],
        client_id=data[CONF_TUYA_CLIENT_ID],
        client_secret=data[CONF_TUYA_CLIENT_SECRET],
    )
    await client.async_test()
    await client.async_request("GET", f"/v1.0/users/{data[CONF_TUYA_UID]}/devices")


class EshtayaSmartControlConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Set up and reconfigure the unified platform."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        errors: dict[str, str] = {}
        if user_input is not None:
            data = _normalize(user_input)
            any_tuya, complete_tuya = _tuya_field_state(data)
            if any_tuya and not complete_tuya:
                errors["base"] = "incomplete_tuya"
            elif complete_tuya:
                try:
                    await _validate_tuya(self.hass, data)
                except Exception:
                    errors["base"] = "cannot_connect"
            if not errors:
                return self.async_create_entry(title="Eshtaya Smart Control", data=data)
        return self.async_show_form(
            step_id="user", data_schema=_schema(user_input), errors=errors
        )

    async def async_step_reconfigure(self, user_input=None):
        entry = self._get_reconfigure_entry()
        current = dict(entry.data)
        errors: dict[str, str] = {}
        if user_input is not None:
            data = _normalize(user_input, current)
            any_tuya, complete_tuya = _tuya_field_state(data)
            if any_tuya and not complete_tuya:
                errors["base"] = "incomplete_tuya"
            elif complete_tuya:
                try:
                    await _validate_tuya(self.hass, data)
                except Exception:
                    errors["base"] = "cannot_connect"
            if not errors:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_mismatch()
                # We already have an update listener; do not trigger a second reload.
                return self.async_update_and_abort(entry, data_updates=data)
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_schema(current if user_input is None else {**current, **user_input}),
            errors=errors,
        )
