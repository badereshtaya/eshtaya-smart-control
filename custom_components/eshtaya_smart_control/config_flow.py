"""Configuration flow for Eshtaya Smart Control.

The integration itself installs without asking for any optional cloud credentials.
Tuya is activated later, inside the Tuya Control dashboard, so a normal Home
Assistant installation never has to provide Tuya information during onboarding.
"""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries

from .const import DOMAIN


class EshtayaSmartControlConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Create the single unified platform config entry."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(title="Eshtaya Smart Control", data={})

        return self.async_show_form(step_id="user", data_schema=vol.Schema({}))
