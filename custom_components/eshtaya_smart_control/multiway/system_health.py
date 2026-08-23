"""System health support for Eshtaya Multi-Way Control."""
from __future__ import annotations

from homeassistant.components import system_health
from homeassistant.core import HomeAssistant, callback

from .const import DATA_RUNTIME, DOMAIN, VERSION


@callback
def async_register(hass: HomeAssistant, register: system_health.SystemHealthRegistration) -> None:
    async def system_health_info() -> dict:
        data = hass.data.get(DOMAIN, {}).get(DATA_RUNTIME)
        if not data:
            return {"version": VERSION, "loaded": False}
        return {
            "version": VERSION,
            "loaded": True,
            "multiway": data["manager"].summary(),
            "smart_groups": data["smart_manager"].summary(),
        }
    register.async_register_info(system_health_info)
