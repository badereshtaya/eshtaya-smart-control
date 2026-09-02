"""Configuration and options flows for Eshtaya Smart Control."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    CONF_LEGACY_HACS_CLEANUP,
    CONF_LEGACY_MIGRATION_ENABLED,
    CONF_LEGACY_SERVICE_ALIASES,
    CONF_MIGRATE_ENTITY_MANAGER,
    CONF_MIGRATE_MULTIWAY,
    CONF_MIGRATE_TEMPLATE_MANAGER,
    CONF_NATIVE_GROUP_DISCOVERY,
    CONF_REPAIR_CONFIRMATIONS,
    CONF_REPAIR_GRACE_SECONDS,
    CONF_STARTUP_MAX_WAIT_SECONDS,
    CONF_STARTUP_SETTLE_SECONDS,
    CONF_STARTUP_WAIT_HA,
    CONF_STARTUP_WAIT_REFERENCES,
    DEFAULT_OPTIONS,
    DOMAIN,
)
from .runtime_options import effective_options


class EshtayaSmartControlConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Create the single unified platform config entry."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(title="Eshtaya Smart Control", data={})

        return self.async_show_form(step_id="user", data_schema=vol.Schema({}))

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the advanced runtime/migration options flow."""
        return EshtayaSmartControlOptionsFlow()


class EshtayaSmartControlOptionsFlow(config_entries.OptionsFlowWithReload):
    """Manage startup safety, native discovery and legacy migration controls."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ):
        """Edit all operational controls in one deterministic form."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current = effective_options(self.config_entry)
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_STARTUP_WAIT_HA,
                    default=current[CONF_STARTUP_WAIT_HA],
                ): bool,
                vol.Required(
                    CONF_STARTUP_WAIT_REFERENCES,
                    default=current[CONF_STARTUP_WAIT_REFERENCES],
                ): bool,
                vol.Required(
                    CONF_STARTUP_SETTLE_SECONDS,
                    default=current[CONF_STARTUP_SETTLE_SECONDS],
                ): vol.All(int, vol.Range(min=0, max=120)),
                vol.Required(
                    CONF_STARTUP_MAX_WAIT_SECONDS,
                    default=current[CONF_STARTUP_MAX_WAIT_SECONDS],
                ): vol.All(int, vol.Range(min=30, max=900)),
                vol.Required(
                    CONF_REPAIR_GRACE_SECONDS,
                    default=current[CONF_REPAIR_GRACE_SECONDS],
                ): vol.All(int, vol.Range(min=0, max=900)),
                vol.Required(
                    CONF_REPAIR_CONFIRMATIONS,
                    default=current[CONF_REPAIR_CONFIRMATIONS],
                ): vol.All(int, vol.Range(min=1, max=10)),
                vol.Required(
                    CONF_NATIVE_GROUP_DISCOVERY,
                    default=current[CONF_NATIVE_GROUP_DISCOVERY],
                ): bool,
                vol.Required(
                    CONF_LEGACY_MIGRATION_ENABLED,
                    default=current[CONF_LEGACY_MIGRATION_ENABLED],
                ): bool,
                vol.Required(
                    CONF_MIGRATE_ENTITY_MANAGER,
                    default=current[CONF_MIGRATE_ENTITY_MANAGER],
                ): bool,
                vol.Required(
                    CONF_MIGRATE_MULTIWAY,
                    default=current[CONF_MIGRATE_MULTIWAY],
                ): bool,
                vol.Required(
                    CONF_MIGRATE_TEMPLATE_MANAGER,
                    default=current[CONF_MIGRATE_TEMPLATE_MANAGER],
                ): bool,
                vol.Required(
                    CONF_LEGACY_HACS_CLEANUP,
                    default=current[CONF_LEGACY_HACS_CLEANUP],
                ): bool,
                vol.Required(
                    CONF_LEGACY_SERVICE_ALIASES,
                    default=current[CONF_LEGACY_SERVICE_ALIASES],
                ): bool,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
