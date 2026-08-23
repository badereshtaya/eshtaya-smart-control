"""Diagnostics for Eshtaya Multi-Way Control."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DATA_RUNTIME, DOMAIN, VERSION


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ConfigEntry) -> dict[str, Any]:
    """Return privacy-conscious diagnostics for both control engines."""
    runtime = hass.data[DOMAIN][DATA_RUNTIME]
    store = runtime["store"]
    manager = runtime["manager"]
    smart_store = runtime["smart_store"]
    smart_manager = runtime["smart_manager"]
    return {
        "version": VERSION,
        "entry_id": entry.entry_id,
        "multiway": {
            "settings": store.settings(),
            "summary": manager.summary(),
            "groups": [
                {
                    "group_id": group["id"][:10],
                    "enabled": group["enabled"],
                    "virtual_type": group["virtual_type"],
                    "controller_count": len(group["controllers"]),
                    "controller_modes": [c["mode"] for c in group["controllers"]],
                    "behavior": group["behavior"],
                    "runtime": {k: v for k, v in manager.status(group["id"]).items() if k != "members"},
                }
                for group in store.groups()
            ],
            "recent_activity": [
                {k: v for k, v in event.items() if k not in {"source", "message"}}
                for event in manager.activity(25)
            ],
        },
        "smart_groups": {
            "settings": smart_store.settings(),
            "summary": smart_manager.summary(),
            "groups": [
                {
                    "group_id": group["id"][:10],
                    "kind": group["kind"],
                    "enabled": group["enabled"],
                    "member_count": len(group["members"]),
                    "behavior": group["behavior"],
                    "runtime": {k: v for k, v in smart_manager.status(group["id"]).items() if k not in {"members", "controller"}},
                }
                for group in smart_store.groups()
            ],
            "recent_activity": [
                {k: v for k, v in event.items() if k not in {"source"}}
                for event in smart_manager.activity(25)
            ],
        },
    }
